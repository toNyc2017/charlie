  import faiss
  import numpy as np
# import io
# from fastapi import FastAPI, File, UploadFile, Request, HTTPException 
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from starlette.responses import JSONResponse
# from azure.storage.blob import BlobServiceClient
# import os
# from dotenv import load_dotenv
# import openai
# from docx import Document
# from docx.shared import Pt
# from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# import pdb
# from datetime import datetime
# import re
# import requests

# from BasePrompts import eti_prompt


# from BlogExamples import blog_examples, recent_example, stamos_example, disney_example, long_form_examples, sector_example
# import PyPDF2
# This is a minor change to trigger redeployment


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}
