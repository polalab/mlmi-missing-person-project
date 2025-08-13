import extraction.summarisation_functions as summ_func
import pandas as pd
from extraction.utils.compare_sets import compare_string_sets_advanced_pattern_types
import math
import csv
from io import StringIO
import re

def evaluate_patterns_advanced(mp_df_full, vp_df_full, misper_id):

    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # 10 tries
    pattern_type_summ_set = {}
    explanation_to_quote ={}
    temp = 0.1
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.patterns_advanced_extraction_pipleine_full("advanced_pattern_types_3.1", mp_df, vp_df, misper_id, temp=temp)
            
            pattern_type_summ = []
            explanation_to_quote = {}

            with open(f"summaries/fake/{misper_id}/patterns/advanced_pattern_types_3.1.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            reader = csv.reader(StringIO(line))
                            pat = next(reader)
                            #report_id,explanation,pattern_name,quote
                            pattern_name =  re.sub(r'[^a-zA-Z0-9\s]', ' ', pat[2].lower().strip())
                            explanation = re.sub(r'[^a-zA-Z0-9\s]', ' ', pat[1].lower().strip())
                            quote =  re.sub(r'[^a-zA-Z0-9\s]', ' ', pat[3].lower().strip())

                            if pattern_name in explanation_to_quote.keys():
                                explanation_to_quote[pattern_name].add((explanation, quote))
                            else:
                                explanation_to_quote[pattern_name] = set([(explanation, quote)])
                            pattern_type_summ.append(pattern_name)
                        except:
                            raise ValueError("could not parse properly")
            pattern_type_summ_set = set(pattern_type_summ)
            

            if 'nan' in pattern_type_summ_set:
                pattern_type_summ_set.remove('nan')
            # print("B")
            pattern_type_summ_set = {x for x in pattern_type_summ_set if not (isinstance(x, float) and math.isnan(x))}
            # print("C")
            if len(pattern_type_summ_set)==0: 
                continue
            else:
                break
        except Exception as e:
            print(e)
            temp+=0.1
            temp = min(temp, 0.5)
            try_count+=1
    
    ent_types = ['entities_landmarks',
                'entities_addresses',
                'entities_location_types',
                'entities_people_names',
                'entities_people_desc',
                'entities_people_relat',
                'entities_pattern_types']

    mp_df_entities = mp_df[['circumstances'] + ent_types ]
    vp_df_entities = vp_df[['vpd_nominalsynopsis'] + ent_types]

    for ent_type in ent_types:
        mp_df_entities.loc[:, ent_type] = mp_df_entities[ent_type].astype(str).str.split(',')
        mp_df_entities.loc[:, ent_type] = mp_df_entities[ent_type].apply(lambda x: [item.strip() for item in x])
    for ent_type in ent_types:
        vp_df_entities.loc[:, ent_type] = vp_df_entities[ent_type].astype(str).str.split(',')
        vp_df_entities.loc[:, ent_type] = vp_df_entities[ent_type].apply(lambda x: [item.strip() for item in x])


    for ent_type in ent_types:
        all_unique_values = set()
        for val in mp_df_entities[ent_type]:
            all_unique_values.update(val)
        if 'nan' in all_unique_values:
            all_unique_values.remove('nan')

        var_name = f'mp_all_unique_{ent_type}'
        globals()[var_name] = all_unique_values
        
    for ent_type in ent_types:
        all_unique_values = set()
        for val in vp_df_entities[ent_type]:
            all_unique_values.update(val)
        if 'nan' in all_unique_values:
            all_unique_values.remove('nan')

        var_name = f'vp_all_unique_{ent_type}'
        globals()[var_name] = all_unique_values
        
    
    all_patterns = mp_all_unique_entities_pattern_types.union(vp_all_unique_entities_pattern_types)
    result = compare_string_sets_advanced_pattern_types(mp_df, vp_df, all_patterns, explanation_to_quote, pattern_type_summ_set)
    result['try_count'] = try_count
    result['len_recognized_patterns'] = len(explanation_to_quote.keys())
    return result 

def run_eval_patternadvanced_types(mp_df_full,vp_df_full, misperids):
    results = []
    for misper_id in misperids:
        out_dict = evaluate_patterns_advanced(mp_df_full, vp_df_full, misper_id)
        out_dict['misperid'] = misper_id
        results.append(out_dict)
        df = pd.DataFrame(results)
        df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns_advanced.pkl")
        df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns_advanced.csv")
    return results

if __name__=="__main__":
    # print(os.getcwd())
    import torch
    torch.cuda.empty_cache()
    mp_df_full = pd.read_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/DATA/fake/fake_mp_data.csv")
    vp_df_full = pd.read_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/DATA/fake/fake_vp_data.csv")
    vp_df_full.columns = vp_df_full.columns.str.lower()
    
    misperids = mp_df_full['misperid'].drop_duplicates().to_list()
    
    misperids = sorted(misperids)

    misperids = misperids[160:]
    
    result = run_eval_patternadvanced_types(mp_df_full, vp_df_full, misperids)
    
    # print(result)
    
    df = pd.DataFrame(result)
    df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns_advanced.pkl")
    df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns_advanced.csv")
    