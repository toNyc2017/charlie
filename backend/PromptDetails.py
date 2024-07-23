
# NOTE -  for Tear Sheet, sym is required as an input and is used in the prompts. Need to extract this from
# file chosen in UI drop down, ans that file should have sym as last entry in name before extension








def quick_one_page_production(documents, sym, model_name):
#sequential_tear_sheet_production(content_to_send, file_path,new_file_path)
    
    today_date = datetime.today().strftime('%Y-%m-%d')

    #sanitized_company_name = re.sub(r'\s+', '_', company_name).replace("'", "").replace('"', "")
    sanitized_company_name = re.sub(r'\s+', '_', sym).replace("'", "").replace('"', "")
    #filename = f"Formatted_SuperLong_{today_date}_{sanitized_company_name}.docx"
    filename = f"Formatted_OnePageCurrent_{today_date}_{sym}.docx"
    print("sanitized_company_name:",sanitized_company_name)
    #filename = f"Formatted_SuperLong_{today_date}_{company_name}.docx"
    docx_file_path = f"/home/azureuser/charlie/backend/results/{filename}"
    

    
    #pdb.set_trace()
    
    all_str = " "



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey  and Company. in this case, you are helping a user create an
             Please create a one page memo to the investment team describing events covered in the context provided, as well as any potential conclusions and action items:"
               """}
        ]
          
            
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})

    print(f'iter is {iter_}')
    print('length of input for this iteration is:',len(transcription[A:A+chunk_size]))
    for attempt in range(5):  # Try up to 5 times
        try:
            response = client.chat.completions.create(
            messages=jls_extract_var,
            model = model_name,
                    temperature = .3,
                    #model="gpt-4",
                
                    max_tokens=3500
)

            break  # If the request was successful, break the loop
        except Exception as e:
            print(f"Attempt {attempt+1} failed with error: {e}")
            if attempt < 4:  # Wait for 2 seconds unless this was the last attem
                time.sleep(2)
                continue  # Try again
            else:
                print("All attempts failed. Exiting.")
                pdb.set_trace()
                #return None
    
   
    response_str = response.choices[0].message.content
   


    # Splitting the string into lines
    one_page = response_str.split('\n')
    one_page_str = '\n'.join(one_page)


    one_page_str = clean_text(one_page_str)

# Open the file in write mode ('w') and write the response_str to it
    
    doc = Document()
 
    # Generate each section and store the results
    formatted_section = analyze_text_with_gpt(one_page_str)    
    add_formatted_content(doc, formatted_section)
    #text_so_far = text_so_far + '\n' + report_sections[section]
        #pdb.set_trace()

    clean_document(doc)


    print('Inside quick_one_page_production. about to clean doc')
    clean_document(doc)
  
    
    print('Inside quick_one_page_production. about to save doc')
    doc.save(docx_file_path)
    print('Inside quick_one_page_production. saved doc to:',docx_file_path)

    return  docx_file_path




def sequential_tear_sheet_production(documents, sym, model_name):
#sequential_tear_sheet_production(content_to_send, file_path,new_file_path)
    
    today_date = datetime.today().strftime('%Y-%m-%d')

    #sanitized_company_name = re.sub(r'\s+', '_', company_name).replace("'", "").replace('"', "")
    sanitized_company_name = re.sub(r'\s+', '_', sym).replace("'", "").replace('"', "")
    #filename = f"Formatted_SuperLong_{today_date}_{sanitized_company_name}.docx"
    filename = f"Formatted_TearSheet_{today_date}_{sym}.docx"
    print("sanitized_company_name:",sanitized_company_name)
    #filename = f"Formatted_SuperLong_{today_date}_{company_name}.docx"
    docx_file_path = f"/home/azureuser/charlie/backend/results/{filename}"
    

# Splitting the filename on underscores and extracting the part before '.txt'
    extracted_string = filename.split('_')[-1].split('.')[0]
    
    
    #sym = parts[1]

    sym = extracted_string
    
    
    #pdb.set_trace()
    
    all_str = " "



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
             The user will provide you with an example of a recent investment analysis summary so you can see the kind of information we are going after. 
            here is the example: {stamos_example}". 
            for this iteration of the process you should just look at the 'I. Company Thesis' section of the example.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. this investment analysis summary concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of the history, development, positioning of a company we are considering investing in.
            Where summaries make include observations or conclusions, please make sure to include at least brief reference to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
            Please don't use overly hyperbolic language, but the tone 
             should be more cautiously optimistic, where optimisim is appropriate, as befits analyses related to potential investments. 
             Overall,  I would like you to tell me about the company
              and its prospects and things you find admirable about its philosphy, history and approach.
                It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied.
             
              also , here are a few other points to keep in mind: {eti_prompt}.
              Where summaries make include observations or conclusions, please make sure to include at least brief reference to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
              in this particular iteration of the process we only want to produce an overal Company Thesis section for the investment analysis summary. This should be similar in style and content to that privoded in the example investment analysis summary. this should be between 250 and 350 words long  AT MOST.
              the Company Thesis section is wehre we talk a little about the origin, history, development, philosophy and mission fo the company.
               the TEXT IS: {chunk}.
              I prefer not to have too many financial results in the ‘Company Thesis’ section  High level, very salient financials are ok in the Company Thesis section, but it should be in service of painting the big picture about the company, rather than a report of recent financials. The Company Thesis section is meant to be a picture picture view of why we might want to be invested in this company.
              In addition, please try to add a sense of inspriration and aspiration to the Company Thesis section. But definitely don't go overboard with enthusiasm.
              Please only output the Company Thesis section in this reponse.  please try hard not be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
               Also please try not to use the word 'delve'.
               """}
        ]
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})
        

    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content
   


    # Splitting the string into lines
    thesis = response_str.split('\n')
    thesis_str = '\n'.join(thesis)


    thesis_str = clean_text(thesis_str)

    all_str = all_str + '\n' +  thesis_str # prevent double statement of section title
   

    ##############################################################################################################################

    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
            The user will provide you with an example of a recent investment analysis summary so you can see the kind of information we are going after. 
            here is the example: {stamos_example}". for this iteration of the process you should just look at the 'II. Company Basics' section of the example.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. this investment analysis summary concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of the positioning and most important recent financial results of a company we are considering investing in.
          Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
             Overall,  I would like you to tell me some basic important facts about the company.  Such as who is the CEO, what is the CEOs tenure, what is the rough size of the company, etx.
              It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied. Don't make anyhthing up. 
              also , here are a few other points to keep in mind: {eti_prompt}.
              in this particular iteration of the process we only want to produce a Company Basics section for the investment analysis summary.  this should be short. absolute maximum 150 words long.  only facts or statistics that are in the text should be included.  please don't include anything in this Company Basics section that you've arlead included in the Company Thesis section.
              I definitely do want to include a sentence about who is the current CEO and what is their tenure in that role, if you have that information.
              The Company Basics section should be short. Concise accurate information.  Maximum of 150 words.
              the TEXT IS: {chunk} and the Company Thesis section of this investment analysis summary that was created during a previous call to the model is: {thesis_str}
              Please only output the Company Basics section in this reponse.  please try hard very hard NOT to be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
              Again, the seciton you are creaing here is the Company Basics section. Previous sections you  want to be sure not be repetitive with in this section is Company thesis: {thesis_str}. Also please try not to use the word 'delve'.
               """}
        ]
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})


    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content

    # Splitting the string into lines
    recent_finanical_results = response_str.split('\n')
    financial_str = '\n'.join(recent_finanical_results)

    financial_str = clean_text(financial_str)

    #all_str = all_str + '\n' + " Company Basics: " + '\n' + financial_str

   
    all_str = all_str +  '\n' + financial_str # prevent double statement of section title

    ########################################################################################################################



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
            The user will provide you with an example of a recent investment analysis summary so you can see the kind of information we are going after. 
            here is the example: {stamos_example}".
            
             for this iteration of the process you should just look at the 'III. Investment Highlights' section of the example.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. this investment analysis summary concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of teh positioning and recent financial results of a company we are considering investing in.
            Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
           Please make sure to capture and cite any information related to activist shareholders or investors being involved.  This is always interesting.  Also please make sure to mention any stock buyback or repurchase activity the company may be involved in.
            Please don't use overly hyperbolic language, but
             definitely do recognize and mention financial successes, capturing and citing data and statistics where possible. the tone 
             should be more cautiously optimistic, where optimisim is appropriate, as befits analyses related to potential investments. if negativity is appropriate, be negative, please be sure to back it up with data and analysis.  
             Overall,  I would like you to tell me about the company
              and its prospects and things you like and things you would be concerned about as I think about investing in 
              this company.              
                It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied. Don't make anyhthing up. 
              in this particular instance we only want to produce an Investment Highlights section for the blog post.  this should be between 300 and 400 words long.  
              the TEXT IS: {chunk} and the Company Thesis section of this investment analysis summary that was created during a previous call to the model is: {thesis_str}.please don't include anything in this Investment Highlights section that you've arlead included in the Company Thesis section.
                the Company Basics section of this investment analysis summary that was created during a previous call to the model is: {financial_str}. please also don't include anything in this Investment Highlights section that you've arlead included in the Company Basics section.
                Please only output the Investment Highights section in this particular reponse.  please try hard NOT to be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
              Also please try not to use the word 'delve'.
               """}
        ]
     
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})


    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content

    # Splitting the string into lines
    investment_highlights = response_str.split('\n')

    highlights_str = '\n'.join(investment_highlights)

    highlights_str = clean_text(highlights_str)

    #all_str = all_str + '\n'+" Investment Highlights " + '\n'+ highlights_str

    all_str = all_str + '\n'+ highlights_str # prevent double statement of section title


    ########################################################################################################################



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
            
            The user will provide you with an example of a recent investment analysis summary so you can see the kind of information we are going after. 
            here is the example: {stamos_example}". for this iteration of the process you should just look at the 'IV. Investment Concerns' section of the example.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. keep in mind investment analysis summary we are building here concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of the positioning and recent financial results of a company we are considering investing in.
            Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
           
            Please don't use overly hyperbolic language, but
             definitely do recognize and mention financial successes, capturing and citing data and statistics where possible. the tone 
             should be more cautiously optimistic, where optimisim is appropriate, as befits analyses related to potential investments. if negativity is appropriate, be negative, please be sure to back it up with data and analysis.  
             Overall,  in this section I would like you to tell me about the things you would be concerned about as I think about investing in 
              this company.  
                It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied.
             
             
             
              also , here are a few other points to keep in mind: {eti_prompt}.
              
              
              in this particular instance we only want to produce an Investment Concerns section for the investment analysis summary.  this should be between 150 and 300 words long.
              please tell me what you think might be some risks to the future prospects of {company_name} and why.  Please make sure to provide specific data or references to ground concerns you may have.  we don't want any generic fluff. thank you.  
              in general for transcripts of earnings calls, analysts attening the call wil ask questions after the management of the company makes its presentation.  
              analysts are often asking about items they are particularly concerned about or intereted in,  typically analyst questions help highligh the most important concerns and also the biggest opportunities.
              the text here includes earnigns call  transcripts. please be sure to pay attention to the questions that are asked by the analysts as they can provide important insights into what the market is thinking about the company.
              and of course the answers management gives to the questions are also a good source of insights.
              
             
              the TEXT IS: {chunk} and the Company Thesis section of this investment analysis summary that was created during a previous call to the model is: {thesis_str}. please don't include anything in this Investment Concerns section that you've arlead included in the Company Thesis section.
                the Company Basics section of this investment analysis summary that was created during a previous call to the model is: {financial_str}. please also don't include anything in this Investment Concerns section that you've arlead included in the Company Basics section.
                the Investment Highlights section of this investment analysis summarythat was created during a previous call to the model is: {highlights_str} . please don't include anything in this Investment Concerns section that you've arlead included in the Company Thesis section.
                Please only output the Investment Concerns section in this reponse.  please try hard Not to be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
               For the Investment Concerns section you should list what you see as meaningful areas of risk.  But please do NOT end this section with a summarizing statement about your overall risk assessment.
               
               Also please try not to use the word 'delve'.
               """}
        ]
    
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})


    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content

    # Splitting the string into lines
    concerns = response_str.split('\n')
    concerns_str = '\n'.join(concerns)

    concerns_str = clean_text(concerns_str)

    #all_str = all_str + '\n'+" Investment Concerns: " + '\n'+ concerns_str

    all_str = all_str + '\n'+ concerns_str # prevent double statement of section title

 

# Open the file in write mode ('w') and write the response_str to it
    
    doc = Document()
 
    # Generate each section and store the results
    formatted_section = analyze_text_with_gpt(all_str)    
    add_formatted_content(doc, formatted_section)
    #text_so_far = text_so_far + '\n' + report_sections[section]
        #pdb.set_trace()

    clean_document(doc)


    print('Inside sequential_tear_sheet_production. about to clean doc')
    clean_document(doc)
  
    
    print('Inside sequential_tear_sheet_production. about to save doc')
    doc.save(docx_file_path)
    print('Inside sequential_tear_sheet_production. saved doc to:',
    docx_file_path)
    return  docx_file_path


def sequential_long_memo_production(documents, sym, model_name):
#sequential_tear_sheet_production(content_to_send, file_path,new_file_path)
     
    today_date = datetime.today().strftime('%Y-%m-%d')

   
    sanitized_company_name = re.sub(r'\s+', '_', sym).replace("'", "").replace('"', "")
  
    filename = f"Formatted_TearSheet_{today_date}_{sym}.docx"
    print("sanitized_company_name:",sanitized_company_name)
  
    docx_file_path = f"/home/azureuser/charlie/backend/results/{filename}"

    
    all_str = " "



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
             The user will provide you with two examples of recent investment analysis summaries so you can see the kind of information we are going after. 
            here are the two examples: {long_form_examples}". 
            for this iteration of the process you should just look at the Company Origin and the Why (Mission, Vision, and Values )section of the example.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. this investment analysis summary concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of the history, development, positioning of a company we are considering investing in.
             Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
             And things you find admirable about its philosphy, histroy and approach. Again, the Why sections hould contain your best efforts at summarizing this Mission, Vision and Values of the company.
            
            Please don't use overly hyperbolic language, but the tone 
             should be more cautiously optimistic, where optimisim is appropriate, as befits analyses related to potential investments. 
             Overall,  I would like you to tell me about the company
              and its origin and history.
                It is very important for purposes of these analyses that you only use and report facts, statistics and numbers which exist in the text that is supplied.
             
              also , here are a few other points to keep in mind: {eti_prompt}.
              in this particular iteration of the process we only want to produce an overal Company Origin section for the investment analysis summary. This should be similar in style and content to that privoded in the examples investment analysis summary. this should be no longer than 300 or 400 words long. 
              the Company Origin section is wehre we talk a little about the origin, history, development, philosophy and mission fo the company.
              I definitely want to include an explicit  "Why" component in this section.  The "Why" component should be a brief summary of the company's Mission, Vision, and Values to the best of your ability, or similar.  The "Why" component should be no longer than 100 words. 
               the TEXT IS: {chunk}.
              In addition, please try to add a sense of inspriration and aspiration to the Company Origin section. But definitely don't go overboard with enthusiasm.
              Please only output the Company Thesis section in this reponse.  please try hard not be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
               Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.
               Also please try not to use the word 'delve'.
               """}
        ]
    
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlined in the system content above."})
 

    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content


    # Splitting the string into lines
    origin = response_str.split('\n')
    origin_str = '\n'.join(origin)

    origin_str = clean_text(origin_str)


    all_str = all_str + '\n'  + origin_str # prevent double statement of section title


    ##############################################################################################################################

    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
            The user will provide you with two examples of recent investment analysis summaries so you can see the kind of information we are going after. 
            here is the example: {long_form_examples}". for this iteration of the process you should just look at the 'What' section of the examples.
            this example investment analysis summary is only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here. this investment analysis summary concerns the company: {sym}
            The purpose of the investment analysis summary is to provide portfolio managers a summary of the positioning and most important recent financial results of a company we are considering investing in.
          Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
             Overall,  I would like you to tell me some basic important facts about the company.  This mainly relates to financial results, line of busines focused on , geographies covered , etc.
               It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied. Don't make anyhthing up. 
              also , here are a few other points to keep in mind: {eti_prompt}.
              
              Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.
              in this particular iteration of the process we only want to produce a 'What' section for the investment analysis summary.  this should be between roughly 400 to 600 words long.  
              
              the TEXT IS: {chunk} and the Company Origin section of this investment analysis summary that was created during a previous call to the model is: {origin_str}
              Please only output the 'What' section in this reponse.  please try hard very hard NOT to be repetitive either within or across the sections you are writing.  
              Again, the seciton you are creaing here is the 'What' section. Previous sections you  want to be sure not be repetitive with in this section is Company Origin: {origin_str}. Also please try not to use the word 'delve'.
               """}
        ]
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlines in the system content above."})
 
    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content


    # Splitting the string into lines
    what_section = response_str.split('\n')
    what_str = '\n'.join(what_section)

    what_str = clean_text(what_str)

   
    all_str = all_str + '\n' +  what_str    

    ########################################################################################################################



    jls_extract_var = [
            {"role": "system", "content": f"""You are a helpful assistant. You have the business acumen and drive to discover value creation opportunities of a 15 year partner at Goldman Sachs or McKinsey and Company. in this case, you are helping a user create an
             investment analysis summary based on a series of recent SEC filings and some broader internet research. due to limitations in the length of output tokens that can be produced 
            by the model, we will be processing the text sequentially and iteratively.
           
            The user will provide you with two examples of recent investment analysis summaries so you can see the kind of information we are going after. 
            here is the example: {long_form_examples}".
            these examples are only to show you the format and style of what we are trying to produce - none of the content in this example
            investment analysis summary should appear in the summary we are creating here.
             for this iteration of the process you should just look at the 'How' section of the example.
             this largely relates to organization, information about senior executires , leadership and coporate governance. also informaiton about how the company's operations are structured if possible. and how its cusomters and suppliers are segmented and managed, if possible.
            
             this investment analysis summary concerns the company: {sym}
            The overall purpose of the investment analysis summary is to provide portfolio managers a summary of the positioning and recent financial results of a company we are considering investing in.
            Where summaries make include observations or conclusions, please make sure to include at least brief references to specific data which leads to these conclusions of observations.  we never want to be accused of speaking in generalities which might equally apply to any company in an industry .  supporting specifics are always desired. 
            Please make sure to capture and cite any information related to activist shareholders or investors being involved.  This is always interesting.  Also please make sure to mention any stock buyback or repurchase activity the company may be involved in.
            Please don't use overly hyperbolic language, but
             definitely do recognize and mention financial successes, capturing and citing data and statistics where possible. the tone 
             should be more cautiously optimistic, where optimisim is appropriate, as befits analyses related to potential investments. if negativity is appropriate, be negative, please be sure to back it up with data and analysis.  
             Overall,  I would like you to tell me about the company
              and its prospects and things you like and things you would be concerned about as I think about investing in 
              this company.              
                 It is very important for purposes of these analyses that you only use and report statistics and numbers which exist in the text that is supplied. Don't make anyhthing up. 
              in this particular instance we only want to produce an Investment Highlights section for the blog post.  this should be between 300 and 400 words long.  
              the TEXT IS: {chunk} and the Company origin  section of this investment analysis summary that was created during a previous call to the model is: {origin_str}.please don't include anything in this Investment Highlights section that you've arlead included in the Company Thesis section.
                the 'What' section of this investment analysis summary that was created during a previous call to the model is: {what_str}. please also don't include anything in this Investment Highlights section that you've arlead included in the Company Basics section.
                Please only output the 'How' section in this particular reponse.  please try hard NOT to be repetitive either within or across the sections you are writing.  if this means that some sections are shorter than the target length, that is fine.
              Please do not include a summarizing or concluding paragraph in this section of the exercise. no ending paragrpah that summarizes overall takeways or inferences from the seciton, please.
              Also please try not to use the word 'delve'.
               """}
        ]
    jls_extract_var.append({"role": "user", "content": f"please execute the task outlines in the system content above."})


    response =client.chat.completions.create(
        messages=jls_extract_var,
        model = model_name,
        temperature = .3,
        max_tokens=2500
    )
    
    response_str = response.choices[0].message.content


    # Splitting the string into lines
    how_section = response_str.split('\n')

    how_str = '\n'.join(how_section)

    how_str = clean_text(how_str)

    #all_str = all_str + '\n'+" How " + '\n'+ how_str

    all_str = all_str + '\n'+ how_str

    
    doc = Document()
 
    # Generate each section and store the results
    formatted_section = analyze_text_with_gpt(all_str)    
    add_formatted_content(doc, formatted_section)
   

    print('Inside sequential_long_memo_production. about to clean doc')
    clean_document(doc)
  
    
    print('Inside sequential_long_memo_production. about to save doc')
    doc.save(docx_file_path)
   
    return  docx_file_path




