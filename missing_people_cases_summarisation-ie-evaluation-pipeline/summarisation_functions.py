from utils.ask_open_ai import ask_open_ai
from utils.ask_llama31 import ask_open_llama

def gpt_4o_summary_base(mp_serialized, vp_serialized):
    prompt = f'''Your task is to summarize records for a missing person including relevant information from their vulnerability reports.

    Here is the past missing person records:
    {mp_serialized}

    Here are all the past vulnerability reports:
    {vp_serialized}

    Please provide a concise summary in maximum 300 words.'''

    response = ask_open_ai(prompt, maxtokens=800)
    return response
    
def mock(mp_serialized, vp_serialized):
    return "hello"


def gpt_4o_summary_template(mp_serialized, vp_serialized):
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''
    
    
    prompt = f'''[INST]Based on the past missing records and past vulnerability reports 
    below, fill out the following template report for the person:
    
    Basic information:
    
    Vulnerabilities:
    
    Association Network:
    
    Locations:
    
    Patterns of Disappearance:
    
    [/INST]

    Here is the past missing person records:
    {mp_serialized}

    Here are all the past vulnerability reports:
    {vp_serialized}

    Please provide a concise summary in maximum 300 words.'''

    response = ask_open_ai(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    return response
    
    
def gpt_4o_summary_template_explanations(mp_serialized, vp_serialized):
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''
    
    prompt = f'''[INST]Based on the past missing records and past vulnerability reports 
    below, fill out the following template report for the person:
    
    Basic information:
    [For example, names, nicknames age]
    
    Vulnerabilities:
    [For example, vulnerable age, risk levels, health conditions, isolation, language barriers]
    
    Association Network:
    [For example, Contacts, relationships, people mentioned in reports]
    
    Locations:
    [For example, Previous places person was found in, birthplaces]
    
    Patterns of Disappearance:
    
    [For example, Repeating behaviour across incidents,e.g. timings of disappearance]
    
    [/INST]

    Here is the past missing person records:
    {mp_serialized}

    Here are all the past vulnerability reports:
    {vp_serialized}

    Please provide a concise summary in maximum 300 words.'''

    response = ask_open_ai(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    return response

def mock(mp_serialized, vp_serialized):
    return '''- **Identity & Background:**
  - Name: Kim Wright
  - Date of Birth: 2007-06-19 (currently 17 years old)
  - Place of Birth: Newry
  - Ethnic Appearance: Black British
  - Disabilities: Hearing impairment (affecting well-being and interactions)

- **Missing Person Records:**
  - **Incident History:** Kim has been reported missing on multiple occasions from her home at 1 St James Square, EH1 3AX, under various circumstances, often seeking solitude or feeling overwhelmed.
    1. **First Report (2021-11-12):** Kim was last seen hurriedly leaving home; found safe after 5 days, showing signs of potentially unusual behavior.
    2. **Subsequent Reports (2022-2023):** Several incidents involved her leaving due to arguments, seeking space, or miscommunication, with durations of being missing ranging from hours to several days.
    3. **Last Report (2025-03-22):** Missing for 3 days; found disoriented at a familiar location after feeling overwhelmed.'''

def mock2(mp_serialized, vp_serialized):
    return '''- **Identity & Background:**
  - Name: Kim Wright
  - Date of Birth: 2007-06-19 (currently 17 years old)
  - Place of Birth: Newry
  - Ethnic Appearance: Black British
  - Disabilities: Hearing impairment (affecting well-being and interactions)

- **Missing Person Records:**
  - **Incident History:** Kim has been reported missing on multiple occasions from her home at 1 St James Square, EH1 3AX, under various circumstances, often seeking solitude or feeling overwhelmed.
    1. **First Report (2021-11-12):** Kim was last seen hurriedly leaving home; found safe after 5 days, showing signs of potentially unusual behavior.
    2. **Subsequent Reports (2022-2023):** Several incidents involved her leaving due to arguments, seeking space, or miscommunication, with durations of being missing ranging from hours to several days.
    3. **Last Report (2025-03-22):** Missing for 3 days; found disoriented at a familiar location after feeling overwhelmed.'''



def llama31instruct_summary_template(mp_serialized, vp_serialized):
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''
    
    
    prompt = f'''[INST]Based on the past missing records and past vulnerability reports 
    below, fill out the following template report for the person:
    
    Basic information:
    
    Vulnerabilities:
    
    Association Network:
    
    Locations:
    
    Patterns of Disappearance:
    
    [/INST]

    Here is the past missing person records:
    {mp_serialized}

    Here are all the past vulnerability reports:
    {vp_serialized}

    Please provide a concise summary in maximum 300 words.'''

    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response