from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import faiss
import numpy as np
from azure.storage.blob import BlobServiceClient
import openai
import os
from openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

# Set the embedding model
embed_model = OpenAIEmbedding(model="text-embedding-3-large")


app = FastAPI()


openai.api_key = os.getenv("OPENAI_API_KEY")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
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


client = OpenAI()

def get_embeddings(text):
    

    response = client.embeddings.create(
    input=text,
    model="text-embedding-3-small"
    )
	#response = openai.Embedding.create(
        #input=text,
       # model="text-embedding-ada-002"
    #)
    #embeddings = response['data'][0]['embedding']
    embeddings = response.data[0].embedding
    return np.array(embeddings).astype('float32')

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Upload to Azure Blob Storage
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    with open(file_location, "rb") as data:
       # blob_client.upload_blob(data)
        blob_client.upload_blob(data, overwrite=True)
    # Read file content and generate embedding
    with open(file_location, "r") as f:
        content = f.read()
    embedding = get_embeddings(content)
   # embedding = embed_model.get_text_embedding(content)    
    index.add(np.array([embedding]))
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}

@app.post("/query/")
async def query_index(query: dict):
    question_embedding = get_embeddings(query['question'])
    D, I = index.search(np.array([question_embedding]), k=1)  # Search top-k nearest neighbors
    return {"question": query['question'], "answer": f"Closest document index: {I[0][0]}, Distance: {D[0][0]}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

