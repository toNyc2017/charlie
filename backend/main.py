from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn
import faiss
import numpy as np
from azure.storage.blob import BlobServiceClient
import os
import openai
from openai import OpenAI

openai.api_key = os.getenv("OPENAI_API_KEY")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")


client = OpenAI(
    # This is the default and can be omitted
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
d = 512  # Dimension of the embeddings
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




@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Upload to Azure Blob Storage
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    with open(file_location, "rb") as data:
        #blob_client.upload_blob(data)
        blob_client.upload_blob(data, overwrite=True)
    # Read file content and generate embeddings
    with open(file_location, "r") as f:
        content = f.read()
    embeddings, chunks = get_embeddings(content)
    
    # Add each embedding to the FAISS index and store the chunks
    for idx, embedding in enumerate(embeddings):
        index.add(np.array([embedding]))
        chunks_storage[idx] = chunks[idx]

    return {"info": f"file '{file.filename}' saved at '{file_location}'"}




@app.post("/query/")
async def query_index(query: dict):
   

    question_embedding, _ = get_embeddings(query['question'])
    question_embedding = question_embedding[0]  # Assuming the query is short and fits in one chunk

    D, I = index.search(np.array([question_embedding]), k=5)  # Search top-k nearest neighbors

    # Retrieve the corresponding text chunks (assuming you have stored them)
    relevant_chunks = [get_chunk_by_index(idx) for idx in I[0]]  # Implement get_chunk_by_index to retrieve the chunk

    # Combine the relevant chunks into a single prompt
    combined_text = " ".join(relevant_chunks)



    # Create the prompt for GPT-4
    prompt = f"Question: {query['question']}\n\nContext: {combined_text}\n\nAnswer:"

    # Generate the response using GPT-4
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3500
    )

    answer = response.choices[0].message.content

    return {"question": query['question'], "answer": answer}








if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
