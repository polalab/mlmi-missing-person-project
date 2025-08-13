import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ask_llama31 import ask_open_llama
# from utils.ask_open_ai import ask_open_ai
import pandas as pd
from utils.mappings import mp_column_contexts, twenty_five_mp_questions, vp_column_contexts

import os
from utils.mappings import mp_column_contexts, vp_column_contexts
from utils.serialize import mp_serialize_dataframe_just_circumstances, mp_serialize_dataframe_for_llm, vp_serialize_dataframe_for_llm, vp_serialize_dataframe_for_llm_nominalsynopsisonly, mp_serialize_dataframe_for_llm_cirumstancesonly
# from utils.mappings import mp_column_contexts, twenty_five_mp_questions, vp_column_contexts

############################ PEOPLE ############################

def split_output_people (text):
    lines = text.splitlines()
    people_names_relations = []
    people_desc = []

    for line in lines:
        key, value = line.split("=", 1)
        items = value.strip("[] \n,").split(", ")
        if key.strip() == "people_names_relations":
            people_names_relations = items
        elif key.strip() == "people_desc":
            people_desc = items
    return people_names_relations, people_desc

def llama31instruct_summary_template_with_reportid(textual_field):
    system_prompt = '''You are a helpful assistant whose job is to extract entities from text.'''
    
    
    prompt = f'''[INST]
    You will extract structured information from the following text.

    1. First, extract all phrases that indicate **people**, dividing them into three categories:
    -  Names with relationship in brackets only if available (for example: Anna Smith (mother))
    -  Otherwise, people entitie's descriptions (for example: sister, members of the public).
    Note: MP refers to missing person and hence is the main person the narrative is about.    
    
    
    3. Format the output in exactly this format and do not add anything else:

    people_names_relations=[...],
    people_desc=[...],
   
    For Example:
    Input: Bianca Smith went missing of Friday informing only her sister, Laura Smith. The mother found out in the morning and called the police after MP has not returned. Bianca was found with Lucy.
    Output:
    people_names_relations=[Bianca Smith (MP), Laura Smith (sister), Lucy]
    people_desc=[mother, police]
    
    or 
    For Example:
    Input: MP was found by a member of public.
    people_names_relations=[]
    people_desc=[MP, a member of public]
    [/INST]
    Here is the text:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response


def llama31instruct_narrative_of_people(entity_lists):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    prompt = f'''[INST]
   
    1. Here is a list of extracted entities (primarily names and people entities) from many past reports for a given missing person.
    In a short narrative summarise the assosiation network - so all people involved in the past incidents of the missing person.
    
    Output ONLY one sentence summary only regarding the assosiation network. Do not output anything else.
    [/INST]
    The list of previously extracted entities:
    {entity_lists}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response

def people_extraction_pipleine(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/assosiation_network"):
            os.makedirs(f"summaries/fake/{misperid}/assosiation_network")
        
        names = []  
        people = []
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        for index, row in mp_df_misperid.iterrows():
            for i in range(5):
                try:
                    output = llama31instruct_summary_template_with_reportid(row['circumstances'])
                    print("SUMMARY\n")
                    print(row['circumstances'])
                    print('\n')
                    print(output)
                    print("\nEND SUMMARY")
                    path = f"summaries/fake/{misperid}/assosiation_network/"
                
                    people_names_relations, people_desc = split_output_people(output)
                    print(len(people_desc))
                    for p in people_names_relations:  
                        if p.split('(', 1)[0]  not in row['circumstances']:
                            print("WRONG", p)
                            continue
                        with open(path + func_name + '.txt', "a+") as f:
                            f.write(str(row['reportid']) + ','+ 'people_names_relations' +  ',' + p + '\n')
                            names.append(p)
                    for p in people_desc:
                        if p.split('(', 1)[0] not in row['circumstances']:
                            print("WRONG", p)
                            continue  
                        with open(path + func_name + '.txt', "a+") as f:
                            people.append(p)
                            f.write(str(row['reportid']) + ','+ 'people_desc' + ',' + p + '\n')
                    break
                except:
                    if i == 4:
                        raise ValueError("couldn't parse for 4 iterations")
                    
        path = f"summaries/fake/{misperid}/assosiation_network/"
        output = llama31instruct_narrative_of_people(names + people) 
        with open(path + func_name + '_narrative' + '.txt', "a+") as f:
            f.write(output)



############################ LOCATIONS ############################
def llama31instruct_summary_template_with_reportid_locations(textual_field):
    system_prompt = '''You are a helpful assistant whose job is to extract entities from text.'''
    
    prompt = f'''[INST]
    You will extract structured information from the following text.

    1. First, extract all phrases that indicate **addresses**, dividing them into two categories:
    -  Addresses (concrete places that could be found on a map)
    - Landmarks and more descriptive locations such as 'forest'
    
    
    3. Format the output in exactly this format and do not add anything else:

    addresses=[...],
    landmarks_other_locations=[...],
    
    For Example:
    Input: Bianca Smith left her school at Maryland Road 1, CB3 0SZ and was traced three hours later in a nearby forest
    Output:
    addresses=[Maryland Road 1, CB3 0SZ]
    landmarks_other_locations=[school, nearby forest]
    
    Second example:
    Input: Bianca Smith went missing.
    Output:
    addresses=[]
    landmarks_other_locations=[]
    
    Output only the two lists and nothing else.
    [\INST]
    Here is the textual field:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response


def llama31instruct_narrative_of_locations(entity_lists):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    
    prompt = f'''[INST]
   
    1. Here is a list of extracted addresses and locations from many past reports for a given missing person.
    In a short narrative summarise the locations - give an overview of what trends they could portray.
    
    Output ONLY one sentence summary only regarding the locations. Do not output anything else.
    [/INST]
    The list of previously extracted entities:
    {entity_lists}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response

def split_output_locations (text):
    lines = text.splitlines()
    addresses = []
    landmarks = []

    for line in lines:
        key, value = line.split("=", 1)
        items = value.strip("[] \n,").split(", ")
        if key.strip() == "addresses":
            addresses = items
        elif key.strip() == "landmarks_other_locations":
            landmarks = items
    return addresses, landmarks

def locations_addresses_extraction_pipleine(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()

    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        
        if not os.path.exists(f"summaries/fake/{misperid}/locations"):
            os.makedirs(f"summaries/fake/{misperid}/locations")
        
        names = []  
        people = []
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        for index, row in mp_df_misperid.iterrows():
            for i in range(5):
                try:
                    output = llama31instruct_summary_template_with_reportid_locations(
                        row['circumstances']
                    )
                    path = f"summaries/fake/{misperid}/locations/"
                
                    locations, names_relations, people_desc = split_output_locations(output)
                    print(len(people_desc))
                    for p in people_names_relations:  
                        if p.split('(', 1)[0]  not in row['circumstances']:
                            print("WRONG", p)
                            continue
                        with open(path + func_name + '.txt', "a+") as f:
                            f.write(str(row['reportid']) + ','+ 'addresses' +  ',' + p + '\n')
                            names.append(p)
                    for p in people_desc:
                        if p.split('(', 1)[0] not in row['circumstances']:
                            print("WRONG", p)
                            continue  
                        with open(path + func_name + '.txt', "a+") as f:
                            people.append(p)
                            print("WRITING TO ", path + func_name + '.txt')
                            f.write(str(row['reportid']) + ','+ 'landmarks_other_locations' + ',' + p + '\n')
                    break
                except:
                    if i == 4:
                        raise ValueError("couldn't parse for 4 iterations")
                    
        path = f"summaries/fake/{misperid}/locations/"
        output = llama31instruct_narrative_of_locations(names + people) 
        with open(path + func_name + '_narrative' + '.txt', "a+") as f:
            f.write(output)


############################ VULNARABILITIES ############################


def llama31instruct_extract_most_important_vp_records(textual_field):
    system_prompt = '''You are a helpful assistant whose job is to extract entities from text.'''
    
    prompt = f'''[INST]
    You will extract structured information from the following text.

    1. First, extract all phrases that indicate **addresses**, dividing them into two categories:
    -  Addresses (concrete places that could be found on a map)
    - Landmarks and more descriptive locations such as 'forest'
    
    
    3. Format the output in exactly this format and do not add anything else:

    addresses=[...],
    landmarks_other_locations=[...],
    
    For Example:
    Input: Bianca Smith left her school at Maryland Road 1, CB3 0SZ and was traced three hours later in a nearby forest
    Output:
    addresses=[Maryland Road 1, CB3 0SZ]
    landmarks_other_locations=[school, nearby forest]
    
    Second example:
    Input: Bianca Smith went missing.
    Output:
    addresses=[]
    landmarks_other_locations=[]
    
    Output only the two lists and nothing else.
    [\INST]
    Here is the textual field:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response


def llama31instruct_narrative_of_vulnarabilities(reports):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    
    prompt = f'''[INST]
   
    Here is a list of all past missing person and other relevant reports for one person.
    
    Output MAXIMUM 2 sentences summary only regarding the vulnarabiltities of the idividual. Do not output anything else.
    Only output the narrative.
    [/INST]
    The list of previous records:
    {reports}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=800, system_prompt=system_prompt)
    print(response)
    return response


def vulnarabilities_narrative(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    
    misperids = [2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        try:
            os.makedirs(f"summaries/fake/{misperid}/vul")
        except FileExistsError:
            pass 
          
        names = []  
        people = []
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = mp_serialize_dataframe_for_llm(mp_df_misperid, mp_column_contexts, twenty_five_mp_questions)
        vp_serialized = vp_serialize_dataframe_for_llm(vp_df_misperid, vp_column_contexts)

        path = f"summaries/fake/{misperid}/vul/"
        output = llama31instruct_narrative_of_vulnarabilities(mp_serialized + '\n' + vp_serialized)
        with open(path + func_name + '_narrative' + '.txt', "w+") as f:
            f.write(output)


def llama31instruct_narrative_of_vulnarabilities_per_queston(reports, q):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    
    prompt = f'''[INST]
   
    Here is a list of all past missing person and other relevant reports for one person.
    Summarise the circumstances of the incidents and focus on why the question {mp_column_contexts[q]} was answered 'yes'.
    
    DO NOT mention the age and the number or reports.
    
    Output MAXIMUM 2 sentences summary. Do not output anything else.
    Only output the narrative.
    [/INST]
    The list of previous records:
    {reports}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=800, system_prompt=system_prompt)
    print(response)
    return response


def llama31instruct_narrative_of_vulnarabilities_per_queston_vp(reports, q):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    
    prompt = f'''[INST]
   
    Here is a list of all past missing person and other relevant reports for one person.
    Summarise the circumstances of the reports and focus on why {vp_column_contexts[q]} was answered 'yes'.
    
    DO NOT mention the age and the number or reports.
    
    Output MAXIMUM 2 sentences summary. Do not output anything else.
    Only output the narrative.
    [/INST]
    The list of previous records:
    {reports}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=800, system_prompt=system_prompt)
    print(response)
    return response


def vulnarabilities_summary_per_question(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/vul"):
            os.makedirs(f"summaries/fake/{misperid}/vul")
        
        names = []  
        people = []
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        
        question_columns = [f'q_{n}' for n in range(1, 26)]
        # vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        for q in question_columns:
            mp_df_misperid_question = mp_df_misperid[mp_df_misperid[q]==1]
        
            if len(mp_df_misperid_question):
                mp_serialized = mp_serialize_dataframe_for_llm(mp_df_misperid_question, mp_column_contexts, twenty_five_mp_questions)

                path = f"summaries/fake/{misperid}/vul/"
                output = llama31instruct_narrative_of_vulnarabilities_per_queston(mp_serialized, q)
            else:
                path = f"summaries/fake/{misperid}/vul/"
                output=""
            with open(path + func_name + '.txt', "a+") as f:
                f.write(q + ": " + output + '['+' '.join(str(reportid) for reportid in mp_df_misperid_question['reportid'].to_list()) +']'+'\n')



def vulnarabilities_summary_per_question_vdp(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/vul"):
            os.makedirs(f"summaries/fake/{misperid}/vul")
        
        names = []  
        people = []
    
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        question_columns = vp_df_misperid.columns.to_list()[-43:]        
        for q in question_columns:
            vp_df_misperid_question = vp_df_misperid[vp_df_misperid[q]==1]
        
            if len(vp_df_misperid_question):
                vp_serialized = vp_serialize_dataframe_for_llm(vp_df_misperid_question, vp_column_contexts)

                path = f"summaries/fake/{misperid}/vul/"
                output = llama31instruct_narrative_of_vulnarabilities_per_queston_vp(vp_serialized, q)
            else:
                path = f"summaries/fake/{misperid}/vul/"
                output=""
            with open(path + func_name + '.txt', "a+") as f:
                f.write(q + ": " + output + '['+' '.join(str(reportid) for reportid in vp_df_misperid_question['VPD_NOMINALINCIDENTID_PK'.lower()].to_list()) +']'+'\n')




############################ PATTERNS ############################


def llama31instruct_extract_most_important_senteces_from_circumstances(textual_field):
    system_prompt = '''You are a helpful assistant whose job is to extract sentences from individual reports.'''
    
    prompt = f'''[INST]
    Extract the top most important fragments (or sentences) among all of the reports  from the following list of reports and retain the link to the relevant report.
    The sentences are important if they contain important information to the general missing person behaviour pattern.
    
    Output the original report ids and sentences ONLY in the following format
    reportid, sentence1
    reportid, sentence2
    ...
    
    Output OMLY the report IDs and sencences. Do not output anything else. The reportids should be just the numbers do not add anything else.

    [\INST]
    Here are the reports:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response

def llama31instruct_extract_patterns_from_most_important(textual_field):
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    prompt = f'''[INST]
    Here is a list of most relevant sentences from past missing person reports.
    
    Output MAXIMUM 2 sentences summary only regarding the patterns of the idividual. Do not output anything else.
    Only output the narrative.
    [/INST]
    The list of previous records:
    
    
    [\INST]
    Here are the reports:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response


def patterns_extraction_pipleine(func_name, mp_df, vp_df):
    """
    Extracting the narrative and quotes from the reports.
    """
    
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
            os.makedirs(f"summaries/fake/{misperid}/patterns")
    
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = mp_serialize_dataframe_just_circumstances(mp_df_misperid)
        vp_serialized = vp_serialize_dataframe_for_llm(vp_df_misperid, vp_column_contexts)
                    
        path = f"summaries/fake/{misperid}/patterns/"
        output = llama31instruct_extract_most_important_senteces_from_circumstances(mp_serialized+ '\n' +vp_serialized)
        with open(path + func_name + '_list' + '.txt', "w+") as f:
            f.write(output)
            
        path = f"summaries/fake/{misperid}/patterns/"
        output = llama31instruct_extract_patterns_from_most_important(output)
        with open(path + func_name + '_narrative' + '.txt', "w+") as f:
            f.write(output)
        
        



def llama31instruct_extract_custom_patterns(textual_field):
    print(textual_field)
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    prompt = f'''[INST]  
        You are given a list of past missing person reports, each with details about the circumstances of the disappearance.  

        Your task is to analyze these reports and identify maximum five key themes that are specifically related to patterns of disappearance. Give them informative names.
        Avoid themes based on personal vulnerabilities and named entities such as locations or people. Focus on behaviours. Make all themes different from each other.

        For each theme you identify:  
        - Ensure it is clearly related to how or where the disappearance occurred.  
        - Provide at least two unique report IDs (from the data) that support this theme.  
        - Format your output exactly as follows, with no additional commentary:

        theme name 1, [reportid1, reportid2, ...]  
        theme name 2, [reportid3, reportid4, ...]  
        ...

        Use the actual reportid values from the input.  
        Do not output anything else.  
        [/INST]  
        Here are the reports:
    {textual_field}
    '''
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response

def patterns_advanced_extraction_pipleine(func_name, mp_df, vp_df):
    """
    Extract patterns from reports.
    """
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
            os.makedirs(f"summaries/fake/{misperid}/patterns")
    
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
        vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

       
        path = f"summaries/fake/{misperid}/patterns/"
        output = llama31instruct_extract_custom_patterns(mp_serialized + '\n' +vp_serialized)
        with open(path + func_name + '_list' + '.txt', "w+") as f:
            f.write(output)
            

def llama31instruct_extract_for_dashboard(textual_field):
    print(textual_field)
    system_prompt = '''You are a helpful assistant whose job is to summarise police records.'''
    
    prompt = f'''[INST]  
        "Extrat information about patterns of the dissapearances from the following reports in the format: 
        report_id, explanation, pattern_name, quote 
        Make sure that for each pattern_name there are multiple instances. 
        Output them in lines like txt file


        report_id, explanation, pattern_name, quote  
        report_id_2, explanation2, pattern_name, quote2  
        ...

        Use the actual reportid values from the input.  
        Do not output anything else.  
        [/INST]  
        Here are the reports:
    {textual_field}
    '''
    response =ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response


def patterns_advanced_extraction_pipleine_dashboard(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
            os.makedirs(f"summaries/fake/{misperid}/patterns")
    
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = llama31instruct_extract_for_dashboard(mp_df_misperid)
        vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

        path = f"summaries/fake/{misperid}/patterns/"
        output = llama31instruct_extract_custom_patterns(mp_serialized + vp_serialized)
        with open(path + func_name + '.txt', "w+") as f:
            f.write(output)
            
################## COMPLEX PEOPLE ###########################
def llama31instruct_extract_assosiation_network(textual_field):
    
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''
    prompt = f'''
    Below, you are given all past missing person and vulnderable person reports for one individual.
    TASK: Extract relationships between people in the text. Pay special attention to the relationships of the missing person to others.
    Output them in lines like below. Do not output anything else:
   
    ## Example Output:

    person1,person2,relationship,reportid 
    Abigail Ferguson,Jennifer Ferguson, mother, 6531
 

    ## Important Notes:

    - Extract relationships from context clues (e.g., "her mother called", "his brother stated")
    - If relationship type is unclear, use "other" and explain in description
    - Always include the report ID in quotes
    - IMPORTANT: Output ONLY data in format like: person1,person2,relationship,reportid ,no additional text or headers
    Now process the following missing person report:
    
    {textual_field}    
    '''
    response =ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt)
    print(response)
    return response

def people_advanced_extraction_pipleine_assosiation_network(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperid}")
    
        try:
            os.makedirs(f"summaries/fake/{misperid}")
        except FileExistsError:
            pass 
        try:
            os.makedirs(f"summaries/fake/{misperid}/assosiation_network")
        except FileExistsError:
            pass 
        
        
    
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = mp_serialize_dataframe_for_llm(mp_df_misperid)
        vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

        path = f"summaries/fake/{misperid}/assosiation_network/"
        output = llama31instruct_extract_assosiation_network(mp_serialized + vp_serialized)
        with open(path + func_name + '.txt', "w+") as f:
            f.write(output)

def llama31instruct_extract_addresses_types(textual_field):
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''

    prompt = f"""Below, you are given all past missing person and vulnderable person reports for one individual.
    TASK: Extract recurring themes in locations and the locations themselves from the reports from the reports where the same pattern appears multiple times.
    Extract them in format like:
    report_id,location,location_type,quote,pattern_if_relevant
    if a given location_type occurs in a given report with report id.
    Make sure that for each location_type there are multiple instances.
    Come up with location_types and patterns taylored to the individuals.

    Output them in lines like below. Do not output anything else:

    1240,"Edward Street footbridge, Kilsyth","Bridge/Elevated Structure","Phoned family saying she was high above water, found sitting wrong side of bridge barriers, fell 20-25 feet","Impulsive/Crisis Location"
    2361,"Gorge area North East of Balcastle Farm","Rural/Farm Area","Full scale search in gorge area, found safe and well","Isolation Seeking"


    The reports:
    {textual_field}"""
    response = ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt)
    print(response)
    return response

def locations_advanced_extraction_pipleine_addresses_types(func_name, mp_df, vp_df):
    misperids = mp_df['misperid'].drop_duplicates().to_list()
    misperids = [5433, 8940, 962, 5051, 2280, 51, 9039]
    for misperid in misperids: 
        print(f"Processing {misperids}")

        # if not os.path.exists(f"summaries/fake/{misperid}:"):
        #     os.makedirs(f"summaries/fake/{misperid}")
        
        if not os.path.exists(f"summaries/fake/{misperid}/locations"):
            os.makedirs(f"summaries/fake/{misperid}/locations")


        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
        mp_serialized = llama31instruct_extract_for_dashboard(mp_df_misperid)
        vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

        path = f"summaries/fake/{misperid}/locations/"
        output = llama31instruct_extract_addresses_types(mp_serialized + vp_serialized)
        with open(path + func_name + '.txt', "w+") as f:
            f.write(output)
            
if __name__=="__main__":
    print(os.getcwd())
    mp_df = pd.read_csv("DATA/fake/fake_mp_data.csv")
    vp_df = pd.read_csv("DATA/fake/fake_vp_data.csv")
    
    vp_df.columns = vp_df.columns.str.lower()


    # locations
    # locations_addresses_extraction_pipleine("locations3.1_both", mp_df, vp_df)
    
    # people asso
    people_advanced_extraction_pipleine_assosiation_network("people_assograph_3.1", mp_df, vp_df)
    #locations_advanced_extraction_pipleine_addresses_types("locations_types_3.1", mp_df, vp_df)
    # patterns_advanced_extraction_pipleine_dashboard
    
    # # pattern types
    # patterns_advanced_extraction_pipleine("custom_llm_pattersllama3.1", mp_df, vp_df)
    
    # # # vulnerability questions narrative + quotes
    # patterns_extraction_pipleine("patterns_llama3.1", mp_df, vp_df)
    
    # # # make a summary per vul question
    # vulnarabilities_summary_per_question("vul_explanation_perquestion", mp_df, vp_df)
    
    # # make vulnerabilities narrative
    # vulnarabilities_narrative("vul_llama3.1",mp_df, vp_df )
    
