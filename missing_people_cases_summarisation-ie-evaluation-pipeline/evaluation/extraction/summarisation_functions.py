import os
print(os.getcwd())
from .utils.serialize import mp_serialize_dataframe_just_circumstances, mp_serialize_dataframe_for_llm, vp_serialize_dataframe_for_llm, vp_serialize_dataframe_for_llm_nominalsynopsisonly, mp_serialize_dataframe_for_llm_cirumstancesonly
from .utils.ask_llama31 import ask_open_llama
from .utils.mappings import mp_column_contexts, vp_column_contexts, twenty_five_mp_questions

############### PEOPLE ###############

def llama31instruct_extract_assosiation_network(textual_field, temp=0.1):
    
    system_prompt = '''You are a specialized data extraction assistant focused on analyzing missing person reports. Your primary function is to identify and extract relationship information between individuals mentioned in these reports.'''
    prompt = f'''
    You are analyzing missing person and vulnerable person reports to extract relationship data.

    OBJECTIVE: Identify and extract all relationships between people mentioned in the report, with special focus on the missing person's connections to others.

    OUTPUT FORMAT: Return ONLY comma-separated values in this exact format:
    person1,person2,relationship,reportid

    RELATIONSHIP EXTRACTION RULES:
    1. Look for explicit relationships: "mother", "father", "sister", "brother", "spouse", "friend", "neighbor"
    2. Infer relationships from context clues:
    - "her mother called" → mother relationship
    - "his brother stated" → brother relationship  
    - "the family reported" → family member relationship
    - "roommate said" → roommate relationship
    3. Use "other" for unclear relationships and note the connection type
    4. Always include the report ID number
    5. Extract ALL relationships found, not just those involving the missing person

    EXAMPLE:
    Abigail Ferguson,Jennifer Ferguson,mother,6531
    John Smith,Abigail Ferguson,friend,6531

    CRITICAL: Output ONLY the relationship data lines. No headers, explanations, or additional text.

    Process this missing person report:
    
    {textual_field}    
    '''
    response =ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt, temperature=temp)
    # print(response)
    return response

def people_advanced_extraction_pipleine_assosiation_network(func_name, mp_df, vp_df, misperid, temp=0.1):
    
    # print(f"Processing {misperid}")

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
    
    
    mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

    path = f"summaries/fake/{misperid}/assosiation_network/"
    output = llama31instruct_extract_assosiation_network(mp_serialized + vp_serialized, temp=temp)
    with open(path + func_name + '.txt', "w+") as f:
        f.write(output)
        
#################### LOCATIONS ####################

def llama31instruct_extract_addresses_types(textual_field, temp=0.1):
    system_prompt = '''You are a specialized data extraction assistant focused on analyzing missing person reports. Your primary function is to identify and extract information about locations mentioned in the reports.'''

    prompt = f"""Below, you are given all past missing person and vulnderable person reports for one individual.
    
    TASK: Extract recurring themes in locations and the locations themselves from the reports from the reports where the same pattern appears multiple times.
   
    EXTRACTION RULES:
    1. Extract them in format like:
    report_id,location,location_type,quote,pattern_if_relevant
    2. If a given location_type occurs in a given report with report id.
    3. Make sure that for each location_type there are multiple instances.
    4. Come up with location_types and patterns taylored to the individuals.

    Output them in lines like below. Do not output anything else:

    EXAMPLE.
    1240,"Edward Street footbridge, Kilsyth","Bridge/Elevated Structure","Phoned family saying she was high above water, found sitting wrong side of bridge barriers, fell 20-25 feet","Impulsive/Crisis Location"
    2361,"Gorge area North East of Balcastle Farm","Rural/Farm Area","Full scale search in gorge area, found safe and well","Isolation Seeking"


    CRITICAL: Output ONLY the data lines. No headers, explanations, or additional text.
    
    The reports:
    {textual_field}"""
    response = ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt, temperature=temp)
    # print(response)
    return response

def locations_advanced_extraction_pipleine_addresses_types(func_name, mp_df, vp_df, misperid, temp=0.1):
    if not os.path.exists(f"summaries/fake/{misperid}/locations"):
        os.makedirs(f"summaries/fake/{misperid}/locations")


    mp_df_misperid = mp_df[mp_df['misperid']==misperid]
    vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
    
    
    mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

    path = f"summaries/fake/{misperid}/locations/"
    output = llama31instruct_extract_addresses_types(mp_serialized + vp_serialized, temp=temp)
    with open(path + func_name + '.txt', "w+") as f:
        f.write(output)
            
def llama31instruct_extract_locations(textual_field, temp=0.1):
    system_prompt = '''You are a specialized data extraction assistant focused on analyzing missing person reports. Your primary function is to identify and extract information about locations mentioned in the reports.'''

    prompt = f"""Below, you are given all past missing person and vulnderable person reports for one individual.
    
    TASK: Extract all locations that are mentioned in the reports. Those include both addresses and more descriptive locations or landmarks.

    OUTPUT FORMAT: Return ONLY comma-separated values in this exact format:
    location, reportid

    Output them in lines like below. Do not output anything else:

    EXAMPLEs:
    Edward Street 1 CB30SZ, 1234
    school, 12345

    CRITICAL: Output ONLY the data lines. No headers, explanations, or additional text.
    
    The reports:
    {textual_field}"""
    response = ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt, temperature=temp)
    # print(response)
    return response

def locations_extraction_pipleine_addresses_and_landmarks(func_name, mp_df, vp_df, misperid, temp=0.1):
    if not os.path.exists(f"summaries/fake/{misperid}/locations"):
        os.makedirs(f"summaries/fake/{misperid}/locations")


    mp_df_misperid = mp_df[mp_df['misperid']==misperid]
    vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
    
    
    mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

    path = f"summaries/fake/{misperid}/locations/"
    output = llama31instruct_extract_locations(mp_serialized + vp_serialized, temp=temp)
    with open(path + func_name + '.txt', "w+") as f:
        f.write(output)
        
############## PATTERNS ##############
def llama31instruct_extract_custom_patterns(textual_field, temp=0.1):
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
    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt, temperature=temp)
    print(response)
    return response

def patterns_advanced_extraction_pipleine(func_name, mp_df, vp_df, misperid, temp=0.1):
    """
    Extract patterns from reports.
    """
    
    if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
        os.makedirs(f"summaries/fake/{misperid}/patterns")


    mp_df_misperid = mp_df[mp_df['misperid']==misperid]
    vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
    
    
    mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

    path = f"summaries/fake/{misperid}/patterns/"
    output = llama31instruct_extract_custom_patterns(mp_serialized + vp_serialized, temp=temp)
    with open(path + func_name + '.txt', "w+") as f:
        f.write(output)
        
    # misperids = mp_df['misperid'].drop_duplicates().to_list()
    
    # for misperid in misperids: 
    #     print(f"Processing {misperid}")
    
    #     if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
    #         os.makedirs(f"summaries/fake/{misperid}/patterns")
    
    
    #     mp_df_misperid = mp_df[mp_df['misperid']==misperid]
    #     vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        
    #     mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    #     vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

       
    #     path = f"summaries/fake/{misperid}/patterns/"
    #     output = llama31instruct_extract_custom_patterns(mp_serialized + '\n' +vp_serialized, temp=temp)
    #     with open(path + func_name + '_list' + '.txt', "w+") as f:
    #         f.write(output)
            
            
#################### ADVANCED PATTERNS ####################

def llama31instruct_extract_advanced_patterns(textual_field, temp=0.1):
    system_prompt = '''You are a specialized data extraction assistant focused on analyzing missing person reports. Your primary function is to identify and extract information about patterns in the reports.'''

    prompt = f"""
    
    You are given a list of past missing person reports, each with details about the circumstances of the disappearance.  Your task is to analyze these reports and identify key themes that are specifically related to patterns of disappearance. Give them informative names.
    Avoid themes based on personal vulnerabilities and named entities such as locations or people. Focus on behaviours. Make all themes different from each other.
            
    TASK: Extract recurring patterns in the reports where a pattern has occured multiple times.
   
    EXTRACTION RULES:
    1. Extract them in format like:
    report_id,explanation,pattern_name,quote
    2. If a given pattern_name occurs in a given report with report id.
    3. Make sure that for each pattern_name there are multiple instances.
    4. Come up with pattern_names taylored to the individuals.

    Output them in lines like below. Do not output anything else:

    EXAMPLE.
    22623,"MP attempted to hang herself",self_harm_attempt_pattern,"MP attempted to make noose round her neck and hang from same however was quickly assisted."

    note that the last part, "MP attempted to make noose round her neck and hang from same however was quickly assisted" was directly extracted from report 22623.
    CRITICAL: Output ONLY the data lines. No headers, explanations, or additional text.
    
    The reports:
    {textual_field}"""
    response = ask_open_llama(prompt=prompt, maxtokens=5000, system_prompt=system_prompt, temperature=temp)
    # print(response)
    return response

def patterns_advanced_extraction_pipleine_full(func_name, mp_df, vp_df, misperid, temp=0.1):
    if not os.path.exists(f"summaries/fake/{misperid}/patterns"):
        os.makedirs(f"summaries/fake/{misperid}/patterns")


    mp_df_misperid = mp_df[mp_df['misperid']==misperid]
    vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
    
    
    mp_serialized = mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df_misperid)
    vp_serialized = vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df_misperid, vp_column_contexts)

    path = f"summaries/fake/{misperid}/patterns/"
    output = llama31instruct_extract_advanced_patterns(mp_serialized + vp_serialized, temp=temp)
    with open(path + func_name + '.txt', "w+") as f:
        f.write(output)