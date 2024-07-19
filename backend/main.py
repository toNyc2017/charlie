import faiss
import numpy as np
import io
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import openai
from docx import Document

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # React dev server
    "http://10.0.0.4:3000",  # Replace with your frontend IP or domain
    "https://10.0.0.4:3000"  # For HTTPS
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chunks_storage = {}  # {index: chunk_text}

def get_chunk_by_index(idx):
    return chunks_storage.get(idx, "")

@app.exception_handler(413)
async def request_entity_too_large_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=413,
        content={"message": "Payload too large"},
    )

# Increase the maximum payload size
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

# Initialize Faiss index
d = 1536  # Dimension of the embeddings
index = faiss.IndexFlatL2(d)

# Initialize Azure Blob Storage
account_name = "yorkvilleworks9016610742"

# Form the connection string
connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

# Create a BlobServiceClient
print("Creating BlobServiceClient...")
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

container_name = "uploaded-files"

def split_text_into_chunks(text, max_tokens=8192):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def get_embeddings(text, chunk_size=8192):
    text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    embeddings = []
    for chunk in text_chunks:
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        embedding = np.array(response.data[0].embedding).astype('float32')
        embeddings.append(embedding)
    
    embeddings = np.vstack(embeddings)
    
    return embeddings, text_chunks


def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    
    print("About to upload file:",file.filename)
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Upload to Azure Blob Storage
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    with open(file_location, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    
    content = ""
    if file.filename.endswith(".txt"):
        with open(file_location, "r") as f:
            content = f.read()
    elif file.filename.endswith(".docx"):
        content = read_docx(file_location)

    
    
    
    
    ## Read file content and generate embeddings
    #with open(file_location, "r") as f:
    #    content = f.read()
    embeddings, chunks = get_embeddings(content)
    
    # Add each embedding to the FAISS index and store the chunks
    for idx, embedding in enumerate(embeddings):
        index.add(np.array([embedding]))
        chunks_storage[idx] = chunks[idx]

    index_file = f"{file.filename}_index"
    faiss.write_index(index, index_file)
    blob_client_index = blob_service_client.get_blob_client(container=container_name, blob=index_file)
    with open(index_file, "rb") as data:
        blob_client_index.upload_blob(data, overwrite=True)

    chunks_file = f"{file.filename}_chunks"
    with open(chunks_file, "w") as f:
        f.write("\n".join(chunks))
    blob_client_chunks = blob_service_client.get_blob_client(container=container_name, blob=chunks_file)
    with open(chunks_file, "rb") as data:
        blob_client_chunks.upload_blob(data, overwrite=True)

    # Clean up local files
    os.remove(file_location)
    os.remove(index_file)
    os.remove(chunks_file)

    return {"info": f"file '{file.filename}' saved at '{file_location}' and '{index_file}' also saved. "}

def get_chunks_from_db(db_name):
    index_blob_client = blob_service_client.get_blob_client(container=container_name, blob=db_name)
    index_data = index_blob_client.download_blob().readall()

    # Write index data to a temporary file
    temp_index_file = f"temp_{db_name}"
    with open(temp_index_file, "wb") as f:
        f.write(index_data)
        
    temp_index = faiss.read_index(temp_index_file)
    os.remove(temp_index_file)

    # Add the embeddings from temp_index to the main index
    index.add(temp_index.reconstruct_n(0, temp_index.ntotal))

    # Retrieve the chunks associated with this database
    chunks_blob_name = db_name.replace('_index', '_chunks')
    chunks_blob_client = blob_service_client.get_blob_client(container=container_name, blob=chunks_blob_name)
    chunks_data = chunks_blob_client.download_blob().readall().decode('utf-8')
    chunks = chunks_data.split('\n')

    return chunks

@app.post("/query/")
async def query_index(query: dict):
    selected_databases = query['databases']
    selected_template = query.get('template', '')

    print("Query received:", query)
    print("Selected template:", selected_template)

    # Clear the existing index and chunks_storage
    index.reset()
    chunks_storage.clear()

    # Load the selected databases into the index
    for db_name in selected_databases:
        chunks = get_chunks_from_db(db_name)
        for idx, chunk in enumerate(chunks):
            chunks_storage[len(chunks_storage)] = chunk

    question_embedding, _ = get_embeddings(query['question'])
    question_embedding = question_embedding[0]  # Assuming the query is short and fits in one chunk

    D, I = index.search(np.array([question_embedding]), k=5)  # Search top-k nearest neighbors

    # Retrieve the corresponding text chunks
    relevant_chunks = [get_chunk_by_index(idx) for idx in I[0]]

    # Combine the relevant chunks into a single prompt
    combined_text = " ".join(relevant_chunks)

    # Create the prompt for GPT-4
    prompt = f"Question: {query['question']}\n\nContext: {combined_text}\n\nAnswer:"
    print("Prompt generated:", prompt)

    # Generate the response using GPT-4
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a partner at Goldman Sachs or McKinsey and Company. Please answer questions you are asked using the context supplied."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3500
    )

    answer = response.choices[0].message.content

    return {"question": query['question'], "answer": answer, "context": combined_text}


@app.get("/vector-databases")
async def list_vector_databases():
    print("Databases being requested")
    blob_list = blob_service_client.get_container_client(container_name).list_blobs()
    databases = [blob.name for blob in blob_list if blob.name.endswith("_index")]
    print("Databases found:", databases)
    return databases

@app.get("/prompt-templates")
async def list_prompt_templates():
    print("Templates being requested")
    with open('prompt_templates.txt', 'r') as f:
        templates = f.read().splitlines()
    return templates




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
