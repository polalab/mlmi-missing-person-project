#from summarisation_functions import llama31instruct_summary_template
from utils.ask_llama31 import ask_open_llama
import pandas as pd
import os
from utils.serialize import mp_serialize_dataframe_for_llm, vp_serialize_dataframe_for_llm
from utils.mappings import mp_column_contexts, twenty_five_mp_questions, vp_column_contexts


def llama31instruct_summary_template_with_reportid(mp_serialized, vp_serialized):
    system_prompt = '''You are a Police Search Officer who needs to create a concise summary for a person who has gone missing.'''
    
    
    prompt = f'''[INST]Based on the past missing records and past vulnerability reports 
    below, fill out the following template report for the person.
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

    For each piece of information provide a reporid in square brackets. For example Gender: Female [reportid: 2034]. Use exactly this format of annotating the reportids "reportid:".
    Please provide a concise summary in maximum 300 words.'''

    response = ask_open_llama(prompt=prompt, maxtokens=1000, system_prompt=system_prompt)
    print(response)
    return response

def simple_summarisation_soring_pipeline(func_name, df_scores, mp_df, vp_df):
    # if hasattr(summarisation_functions, func_name):
    #     func = getattr(summarisation_functions, func_name)
    #     if not callable(func):
    #         raise ValueError(f"Function '{func_name}' not working")
    # else:
    #     raise ValueError(f"Function '{func_name}' not found")
    

    misperids = mp_df['misperid'].drop_duplicates().to_list()

    for misperid in misperids: 
        
        print(f"Processing {misperid}")
        # if has_been_processes(misperid):
        #     print(f"Not processing{misperid} since it has been processed.")
        #     continue
        if not os.path.exists(f"missing_people_cases_summarisation/summaries/real/{misperid}"):
            os.makedirs(f"missing_people_cases_summarisation/summaries/real/{misperid}")
        
        
        mp_df_misperid = mp_df[mp_df['misperid']==misperid]
        vp_df_misperid = vp_df[vp_df['misper_misperid']==misperid]
        
        mp_serialized = mp_serialize_dataframe_for_llm(mp_df_misperid, mp_column_contexts, twenty_five_mp_questions)
        vp_serialized = vp_serialize_dataframe_for_llm(vp_df_misperid, vp_column_contexts)
        
        # summary = gpt_4o_summary_base(mp_serialized, vp_serialized)
        summary = llama31instruct_summary_template_with_reportid(mp_serialized, vp_serialized)
        print("SUMMARY\n")
        print(summary)
        print("\nEND SUMMARY")
        path = f"missing_people_cases_summarisation/summaries/real/{misperid}/"
        
        with open(path + func_name + '.txt', "w+") as f:
            f.write(summary)
        
        # raise ValueError("Just test")
    
if __name__=="__main__":
    mp_df = pd.read_csv("missing_people_cases_summarisation/DATA/mp_data.csv")
    vp_df = pd.read_csv("missing_people_cases_summarisation/DATA/vp_data.csv")
    vp_df.columns = vp_df.columns.str.replace('.', '_')
    vp_df.columns = vp_df.columns.str.lower()
    
    print(mp_df.columns.to_list(), len(mp_df.columns.to_list()))
    print(vp_df.columns.to_list(), len(vp_df.columns.to_list()))
    simple_summarisation_soring_pipeline("llama31instruct_summary_template", None, mp_df, vp_df)