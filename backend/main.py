import faiss
import numpy as np
import io
from fastapi import FastAPI, File, UploadFile, Request
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


from BlogExamples import blog_examples, recent_example, stamos_example, disney_example, long_form_examples, sector_example

from BasePrompts import eti_prompt



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
    temp_index_file = f"temp_{db_name}"
    
    with open(temp_index_file, "wb") as f:
        f.write(index_data)
    
    temp_index = faiss.read_index(temp_index_file)
    embeddings = temp_index.reconstruct_n(0, temp_index.ntotal)
    os.remove(temp_index_file)
    
    # Retrieve the chunks associated with this database
    chunks_blob_name = db_name.replace('_index', '_chunks')
    print(f"Fetching chunks for {chunks_blob_name}")
    
    chunks_blob_client = blob_service_client.get_blob_client(container=container_name, blob=chunks_blob_name)
    chunks_data = chunks_blob_client.download_blob().readall().decode('utf-8')
    chunks = chunks_data.split('\n')
    
    return chunks, embeddings




def generate_section(prompt, model_name):
    #response = openai.ChatCompletion.create(
    #    model=model_name,
    #    messages=[
    #        {"role": "system", "content": "You are a helpful assistant."},
    #        {"role": "user", "content": prompt}
    #    ],
    #    max_tokens=3500
    #)
    
    response =client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a business, strategy, and finance expert, as well as a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model = model_name,
        temperature = .3,
        max_tokens=3500
    )
    
    
    #return response.choices[0].message['content']
    return response.choices[0].message.content


def add_formatted_content(doc, formatted_text):
    lines = formatted_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('#### '):
            doc.add_heading(line[5:], level=4)
        elif line.startswith('##### '):
            para = doc.add_paragraph()
            run = para.add_run(line[6:])
            run.bold = True
        elif line.startswith('- '):
            para = doc.add_paragraph(style='List Bullet')
            para.add_run(line[2:])
        elif len(line) > 3 and line[0].isdigit() and line[1] == '.' and line[2] == ' ':
            para = doc.add_paragraph(style='List Number')
            para.add_run(line[3:])
        else:
            para = doc.add_paragraph()
            para.add_run(line)
            para.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

def analyze_text_with_gpt(text):
    
    #prompt=f"Analyze the following text and determine which sections should be formatted as headings, subheadings, paragraphs, or lists. Return a structured representation of the text:\n\n{text}",
   
    
    
    jls_extract_var = [
            #{"role": "system", "content": f"You are a helpful assistant. in this case, you are helping a user create blog posts from summaries of text transcripts. The user will provide you with examples of original text summary and final blog post. then the user will provide an additional original text summary. your task is to create a blog post from this new original text summary.  it should be similar in style and approach as the given examples. note it is good if the blog posts have section headings to organize the thinking. please make the contents of each section quite a lot longer than current example sections are. The purpose of the blog series is to provide insights into happenings in financial markets and products used to trade and invest in these markets.Please don't use overly hyperbolic language, but definitely do recognize and mention financial successes, capturing and citing data and statistics where possible. the tone should be more cautiously optimisitc, where optimisim is appropriate, as befits analyses related to potential investments. Please don't use overly hyperbolic language, but definitely do recognize and mention financial successes, capturing and citing data and statistics where possible. the tone should be more cautiously optimisitc, where optimisim is appropriate, as befits analyses related to potential investments. also , here are a few other points to keep in mind: {eti_prompt}. Also please try not to use the word 'delve'.  "}
       {"role": "system", "content": f"""
       You are a helpful assistant and a meticulous editor
       """}
       
        ]
    #jls_extract_var.append({"role": "user", "content": f"here are some examples: {blog_examples}"})
    jls_extract_var.append({"role": "user", "content": f""""
    Analyze the following text and determine which sections should be formatted as headings, subheadings, paragraphs, or lists.
     In no event should the following symbols and text appear : "```markdown" or the word "markdown" which I have seen in some past examples.  also I don't want any asterisks '*' within bullet points or numbered lists. in the text nor any instances of the word 'bold' or 'italic'.
     also please no instances of  " ``` " which I have seen in some past examples.
     I do not like to have more than one line of blank space between any two sections.
    In addition, on some occasions I have seen numbered lists where the numbering of each item appears twice.  It is as though in some cases the original text has a numbered list and then this formatting exercise decides this text is a numbered list and so numbers it again.  please avoid this.
     
     Please return a structured representation of the text:\n\n{text}"""})  
        



    response = client.chat.completions.create(
        messages=jls_extract_var,
        model = "gpt-4o",
                        temperature = .3,
                        
                    
                        max_tokens=2500
    )



    
    response_str = response.choices[0].message.content

    

    return response_str
    



def clean_document(doc):
    for para in doc.paragraphs:
        for run in para.runs:
            run.text = clean_text(run.text)



def clean_text(text):
    # Remove unwanted symbols like '*', '#', and other non-alphanumeric characters
    cleaned_text = re.sub(r'[^\w\s,.()-]', '', text)  # Keep alphanumeric, spaces, and some punctuation
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove extra spaces
    return cleaned_text


def sequential_superlong(documents, company_name, model_name):
   

    today_date = datetime.today().strftime('%Y-%m-%d')
    filename = f"Formatted_SuperLong_{today_date}_{company_name}.docx"
    docx_file_path = f"/home/azureuser/charlie/backend/results/{filename}"

 

# Ensure no unwanted quotes
    docx_file_path = docx_file_path.replace('"', '').replace("'", "")


    # Create a new Document
    doc = Document()

    # Add some dummy content
    doc.add_heading('Dummy Document', 0)
    doc.add_paragraph(f'This is a dummy document for {company_name}.')
    doc.add_paragraph('This is just for testing the file writing and downloading process.')

    # Save the document
    doc.save(docx_file_path)

    print(f"Dummy document saved to {docx_file_path}")

    return docx_file_path
    
    #filename = new_file_path.split('/')[-1]

# Splitting the filename on underscores and extracting the part before '.txt'
    #extracted_string = filename.split('_')[-1].split('.')[0]
    

    
    #sym = parts[1]

    #sym = extracted_string
    
    
    #pdb.set_trace()
    
    all_str = " "


    text_so_far = " "

    today_date = datetime.today().strftime('%Y-%m-%d')

# Section Prompts
    prompts = {
        #"executive_summary": f"""
        #    You are an expert business analyst. Based on the following documents, generate a 1-page Executive Summary for {company_name}.
        #    Summarize the key insights from the analysis of customers, competitors, and the corporation itself.
            

        #    Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
        #    We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
        #    This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
        #    Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

        #    Aslo, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
        #    but not this example is just for style reference.  do not include any of the content from this example in the summary you are creating here.

        #    Here are the source Documents:
        #    {documents}
        #    """,

        "company_analysis": f"""
            You are an expert business analyst. Based on the following documents, generate a 3-page Company Analysis for {company_name}.
            Provide an overview of the company’s history and business model.
            
            
            
            
            Start with an overview of the company's Origin, History , Development and Current Business Model
            
            Analyze the financial performance including key metrics, growth, and profitability.
            Please make sure to capture and cite any information related to activist shareholders or investors being involved.  This is always interesting.  Also please make sure to mention any stock buyback or repurchase activity the company may be involved in.
            Please also Perform a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats). Again, in this section, please only include information from the documents you are being presented with.  Do not search the web or use other sources for this section or the SWOT analysis
            
            Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
            We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
            This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
            Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

            
            Please try to make sure your information is as accurate and up to date as possible at least as up to date as two months ago. Note today's date is {today_date} If you are not sure about something, please don't include it.  But if you are sure, please include it.
            Explicitly avoid talking about divisions that may have recently been sold or operations that have recent ceased. For example, Johnson and Johnson sold off its consumer health division in August 2023.  So don’t talk about this business or it’s consumers in the analysis 
            
            Also, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
            but not this example is just for style reference. But I do not want any overall summarizing or concluding paragraph in this section, notwithstanding whether the example has this. do not include any of the content from this example in the summary you are creating here.

                        
            For this section, please make sure to only include information about {company_name} that comes form the documents you are being presented as part of this prompt.  Do not search the web or use other sources for this section. 
            You may search the web for information about the industry and competitors as you create these sections.
            That said, while I don't want facts or data about {company_name} in this section coming from outside the documents, it is ok to use your strong business acumen and reasoning ability when creating this section.    
            When organizing the seciton, please feel free to use sub-numbering where it makes sense.  This is section 2 of the overall document, so if it makes sense you could talk baout some potins as 2.1, 2.2, etc.  But please don't force things.
                        
            
            Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.
           
            Please make sure not repeat anything you've already produced for this document, which is: {text_so_far}

            Also, please don't include any repetitive or similar section headings at the begining of each section. I've seen a lot of this in previous versions.  
            One section title is fine.  then distinct subheadings, if necessary through the text.  but please avoid repetition.

            Please try not to use the word "delve".

            Here are the source Documents:
            {documents}
            """,

        "customer_analysis": f"""
            
            
            
            You are an expert business analyst. Based on the following documents, generate a 2-3 page Customer Analysis for {company_name}.
            Analyze customer demographics and segmentation.
            Describe the needs and preferences of these customers.
            Evaluate customer satisfaction and loyalty.

            Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
            We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
            This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
            Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

           
            
            Also, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
            but not this example is just for style reference. But I do not want any overall summarizing or concluding paragraph in this section, notwithstanding whether the example has this.  do not include any of the content from this example in the summary you are creating here.

            Please try to make sure your information is as accurate and up to date as possible at least as up to date as two months ago. Note today's date is {today_date} If you are not sure about something, please don't include it.  But if you are sure, please include it.

            Explicitly avoid talking about divisions that may have recently been sold or operations that have recent ceased. For example, Johnson and Johnson sold off its consumer health division in August 2023.  So don’t talk about this business or it’s consumers in the analysis 
                          
            For this section, please make sure to only include information about {company_name} that comes form the documents you are being presented as part of this prompt.  Do not search the web or use other sources for this section. 
            You may search the web for information about the industry and competitors as you create these sections.
            That said, while I don't want facts or data about {company_name} in this section coming from outside the documents, it is ok to use your strong business acumen and reasoning ability when creating this section.    
            When organizing the seciton, please feel free to use sub-numbering where it makes sense.  This is section 2 of the overall document, so if it makes sense you could talk baout some potins as 2.1, 2.2, etc.  But please don't force things.
                     




            Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.

            Please make sure not repeat anything you've already produced for this document, which is: {text_so_far}
            
            Also, please don't include any repetitive or similar section headings at the begining of each section. I've seen a lot of this in previous versions.  
            One section title is fine.  then distinct subheadings, if necessary through the text.  but please avoid repetition.

             Please try not to use the word "delve".



            Here are the source Documents:
            {documents}
            """,

        "competitor_analysis": f"""
            You are an expert business analyst. Based on the following documents, generate a 2-3 page Competitor Analysis for {company_name}.
            Identify and analyze the major competitors and their market share.
            Describe their competitive strategies and positioning.
            Provide a comparative performance analysis.

            Also, please mention developments in the sector that might impact the competitive landscape.

            For this section when discussing {company_name}, please make sure to only include information about {company_name} that comes form the documents you are being presented as part of this prompt.  Do not search the web or use other sources regarding {company_name} for this section. 
            For information on other competitor ompanies you may use sources outside the documents share as part of this request.  Still, please only present information you are quite sure is factual. Do not make things up.


            Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
            We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
            This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
            Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

            
            Please try to make sure your information is as accurate and up to date as possible at least as up to date as two months ago. Note today's date is {today_date} If you are not sure about something, please don't include it.  But if you are sure, please include it.
            
            Explicitly avoid talking about divisions that may have recently been sold or operations that have recent ceased. For example, Johnson and Johnson sold off its consumer health division in August 2023.  So don’t talk about this business or it’s consumers in the analysis 
                          
            For this section, please make sure to only include information about {company_name} that comes form the documents you are being presented as part of this prompt.  Do not search the web or use other sources for this section. 
            You may search the web for information about the industry and competitors as you create these sections.
            That said, while I don't want facts or data about {company_name} in this section coming from outside the documents, it is ok to use your strong business acumen and reasoning ability when creating this section.    
            When organizing the seciton, please feel free to use sub-numbering where it makes sense.  This is section 2 of the overall document, so if it makes sense you could talk baout some potins as 2.1, 2.2, etc.  But please don't force things.
                     


            Also, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
            but not this example is just for style reference. But I do not want any overall summarizing or concluding paragraph in this section, notwithstanding whether the example has this. do not include any of the content from this example in the summary you are creating here.

            
            
            
           Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.
           

            Please make sure not repeat anything you've already produced for this document, which is: {text_so_far}

            Also, please don't include any repetitive or similar section headings at the begining of each section. I've seen a lot of this in previous versions.  
            One section title is fine.  then distinct subheadings, if necessary through the text.  but please avoid repetition.

             Please try not to use the word "delve".

            
            Here are the source Documents:
            {documents}
            """,

        "porters_five_forces": f"""
            You are an expert business analyst. Based on the following documents, generate a 5-page Porter’s Five Forces Analysis for {company_name}.
            - Competitive Rivalry: Discuss the market structure and competitive landscape.
            - Supplier Power: Identify key suppliers, their bargaining power, and supplier relationships.
            - Buyer Power: Identify key buyers, their bargaining power, and buyer behavior.
            - Threat of Substitution: Identify alternative products/services and evaluate substitution risk.
            - Threat of New Entry: Discuss barriers to entry and potential new entrants.

            Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
            We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
            This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
            Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

            Also, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
            but not this example is just for style reference.  But I do not want any overall summarizing or concluding paragraph in this section, notwithstanding whether the example has this. do not include any of the content from this example in the summary you are creating here.

            Please try to make sure your information is as accurate and up to date as possible at least as up to date as two months ago. Note today's date is {today_date} If you are not sure about something, please don't include it.  But if you are sure, please include it.

            Explicitly avoid talking about divisions that may have recently been sold or operations that have recent ceased. For example, Johnson and Johnson sold off its consumer health division in August 2023.  So don’t talk about this business or it’s consumers in the analysis 
                          
            For this section, please make sure to only include information about {company_name} that comes form the documents you are being presented as part of this prompt.  Do not search the web or use other sources for this section. 
            You may search the web for information about the industry and competitors as you create these sections.
            That said, while I don't want facts or data about {company_name} in this section coming from outside the documents, it is ok to use your strong business acumen and reasoning ability when creating this section.    
            When organizing the seciton, please feel free to use sub-numbering where it makes sense.  This is section 2 of the overall document, so if it makes sense you could talk baout some potins as 2.1, 2.2, etc.  But please don't force things.
                     


            Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.

            Please make sure not repeat anything you've already produced for this document, which is: {text_so_far}
            
            Also, please don't include any repetitive or similar section headings at the begining of each section. I've seen a lot of this in previous versions.  
            One section title is fine.  then distinct subheadings, if necessary through the text.  but please avoid repetition.

             Please try not to use the word "delve".


            Here are the source Documents:
            {documents}
            """,

        #"conclusion_recommendations": f"""
        #    You are an expert business analyst. Based on the following documents, generate a 2-page Conclusion and Recommendations for {company_name}.
        #    Summarize the key insights from the report.
        #    Provide strategic recommendations for investing in the company.
        #    Offer a future outlook for the company.

        #    Please write in an engaging and informative style, highlighting the most important points but don't make it too terse. 
        #    We do want a lot of data and statistics drawn for the text,  but we also want some narrative.
        #    This should be an informative and accurate read but something we'd be able to listent to as a podcast episode and not get bored.
        #    Do the best you can to execute the analyses according to the framework outlined.  but if the supplied text won't allow it. then gracefuly avoid the requested sections and move on.

           
        #    Aslo, please don't present in just bullet points.  while we like lots of specific data, we also like prose.  an example of the style we are going after is here: {disney_example}
        #    but not this example is just for style reference.  do not include any of the content from this example in the summary you are creating here.

        #    Please make sure not repeat anything you've already productedd for this document, which is: {text_so_far}


        #    Here are the source Documents:
           # {documents}
           # """
    }

   

# Create a new Document
  
# Create a new Document
    doc = Document()
 
    # Generate each section and store the results
    report_sections = {}
    
    print('Inside sequential_superlong. about to loop through prompts')
    for section, prompt in prompts.items():
        report_sections[section] = generate_section(prompt, model_name)
        report_sections[section] = clean_text(report_sections[section])
        formatted_section = analyze_text_with_gpt(report_sections[section])    
        add_formatted_content(doc, formatted_section)
        text_so_far = text_so_far + '\n' + report_sections[section]
        print('Inside sequential_superlong. did a loop')
        #pdb.set_trace()

    
    
    print('Inside sequential_superlong. about to clean doc')
    clean_document(doc)
    # Compile the full report
    


    #doc.save(f'/Users/tomolds/Local/transcription/Stamos/{sym}/Formatted_SuperLong_{today_date}_{sym}.docx')
    
    print('Inside sequential_superlong. about to save doc')
    doc.save(docx_file_path)
    
    full_report = "\n\n".join(report_sections.values())

    full_report = clean_text(full_report)

    all_str = all_str + '\n' + " Full Report: " + '\n' + full_report


    #try:
    #    with open(new_file_path, 'w', encoding='utf-8') as file:
    #        file.write(all_str)
    #except:
    #    print('error writing to file')
    #    pdb.set_trace()

    #print(f"Sequential SuperLong saved to {new_file_path}")

    #pdb.set_trace()

    return  docx_file_path





#@app.post("/query/")
#async def query_index(query: dict):
#    selected_databases = query['databases']
#    selected_template = query.get('template', '')

#    print("Query received:", query)
#    print("Selected template:", selected_template)

#    # Clear the existing index and chunks_storage
#    index.reset()
#    chunks_storage.clear()

#    # Load the selected databases into the index
#    for db_name in selected_databases:
#        chunks = get_chunks_from_db(db_name)
#        for idx, chunk in enumerate(chunks):
#            chunks_storage[len(chunks_storage)] = chunk

#    question_embedding, _ = get_embeddings(query['question'])
#    question_embedding = question_embedding[0]  # Assuming the query is short and fits in one chunk

#    D, I = index.search(np.array([question_embedding]), k=5)  # Search top-k nearest neighbors

#    # Retrieve the corresponding text chunks
#    relevant_chunks = [get_chunk_by_index(idx) for idx in I[0]]

#    # Combine the relevant chunks into a single prompt
#    combined_text = " ".join(relevant_chunks)

#    # Create the prompt for GPT-4
#    prompt = f"Question: {query['question']}\n\nContext: {combined_text}\n\nAnswer:"
#    print("Prompt generated:", prompt)

#    # Generate the response using GPT-4
#    response = client.chat.completions.create(
#        model="gpt-4o",
#        messages=[{"role": "system", "content": "You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a partner at Goldman Sachs or McKinsey and Company. Please answer questions you are asked using the context supplied."},
#                  {"role": "user", "content": prompt}],
#        temperature=0.3,
#        max_tokens=3500
#    )

#    answer = response.choices[0].message.content

#    return {"question": query['question'], "answer": answer, "context": combined_text}

from fastapi.responses import JSONResponse
@app.post("/query/")
async def query_index(query: dict):
    selected_databases = query['databases']
    selected_template = query['template']
    question = query['question']

    if selected_template == "SuperLong":
        # Handle SuperLong template separately
        all_chunks = []
        print('in SuperLong section, about to get chunks')
        for db_name in selected_databases:
            chunks, _ = get_chunks_from_db(db_name)  # Only retrieve chunks
            all_chunks.extend(chunks)
        print('in SuperLong section, about to join chunks')
        documents = "\n".join(all_chunks)

        #for db_name in selected_databases:
        #    chunks, _ = get_chunks_from_db(db_name)  # Only retrieve chunks
        #    all_chunks.extend(chunks)
        #documents = "\n".join(all_chunks)

        company_name = "Your Company Name"  # Adjust as necessary
        model_name = "gpt-4o"

        print('in SuperLong section, about to call sequential_superlong')
        file_path = sequential_superlong(documents, company_name, model_name)
        print('in SuperLong section, FINISHED sequential_superlong')

        # Return the file path as a response
        return {"file_path": file_path}

    else:
        # Non-SuperLong case
        index.reset()
        chunks_storage.clear()
        print("Query received:", query)

        # Load the selected databases into the index
        for db_name in selected_databases:
            chunks, embeddings = get_chunks_from_db(db_name)
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                index.add(np.array([embedding]))  # Add the embedding to the FAISS index
                chunks_storage[len(chunks_storage)] = chunk  # Store the chunk text

        question_embedding, _ = get_embeddings(question)
        question_embedding = question_embedding[0]  # Assuming the query is short and fits in one chunk

        D, I = index.search(np.array([question_embedding]), k=5)  # Search top-k nearest neighbors

        # Retrieve the corresponding text chunks
        relevant_chunks = [get_chunk_by_index(idx) for idx in I[0]]

        # Combine the relevant chunks into a single prompt
        combined_text = " ".join(relevant_chunks)

        # Template-based prompt creation
        if selected_template == "Tear Sheet":
            prompt = f"Question: {question}\n\nContext: {combined_text}\n\nAnswer in the form of a Tear Sheet:"

        elif selected_template == "Long Form":
            prompt = f"Question: {question}\n\nContext: {combined_text}\n\nAnswer in a long form analysis:"

        elif selected_template == "Ad Hoc Query":
            prompt = f"Question: {question}\n\nContext: {combined_text}\n\nAnswer this ad hoc query:"

        else:
            return {"error": "Invalid template selected"}

        # Generate the response using GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a partner at Goldman Sachs or McKinsey and Company. Please answer questions you are asked using the context supplied."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500
        )

        answer = response.choices[0].message.content

        return {"question": question, "answer": answer}


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


@app.get("/download")
async def download_file(file_path: str):
    file_path = file_path.replace('"', '').replace("'", "")
    filename = os.path.basename(file_path)
    # Remove any leading/trailing spaces and normalize any other characters if necessary
    filename = filename.strip()
    return FileResponse(file_path, filename=filename)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
