#import faiss
import numpy as np
import io
from fastapi import FastAPI, File, UploadFile, Request, HTTPException 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import openai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

import pdb
from datetime import datetime
import re
import requests

from BasePrompts import eti_prompt


from BlogExamples import blog_examples, recent_example, stamos_example, disney_example, long_form_examples, sector_example
import PyPDF2
# This is a minor change to trigger redeployment



print('GOT EVERYTIHG LOADED SUCESFULLY')


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

#app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # React dev server
    "https://askyorkville-c3ckc8hgh4hzajeu.eastus-01.azurewebsites.net"  # For HTTPS
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print('GOT CORS CONFIGURED SUCCESSFULLY')

chunks_storage = {}  # {index: chunk_text}

def get_chunk_by_index(idx):
    return chunks_storage.get(idx, "")


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World, A SECOND TIME"}

