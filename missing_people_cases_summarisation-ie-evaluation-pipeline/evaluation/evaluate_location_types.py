import extraction.summarisation_functions as summ_func
import pandas as pd
from extraction.utils.compare_sets import compare_string_sets_location_types
import math
import csv
from io import StringIO
import re

def evaluate_location_types(mp_df_full, vp_df_full, misper_id):

    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # 10 tries
    location_type_summ_set = {}
    location_to_type = {}
    temp = 0.1
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.locations_advanced_extraction_pipleine_addresses_types("locations_types_3.1", mp_df, vp_df, misper_id, temp=temp)
            
            location_type_summ = []
            location_to_type = {}

            with open(f"summaries/fake/{misper_id}/locations/locations_types_3.1.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            reader = csv.reader(StringIO(line))
                            loc = next(reader)
                            location_type =  re.sub(r'[^\w\s]', ' ', loc[2].lower().strip())
                            location_itself = re.sub(r'[^\w\s]', ' ', loc[1].lower().strip())
                            quote =  re.sub(r'[^\w\s]', ' ', loc[3].lower().strip())

                            if location_type in location_to_type.keys():
                                location_to_type[location_type].add((location_itself, quote))
                            else:
                                location_to_type[location_type] = set([(location_itself, quote)])
                            location_type_summ.append(location_type)
                        except:
                            raise ValueError("could not parse properly")
            location_type_summ_set = set(location_type_summ)
            

            if 'nan' in location_type_summ_set:
                location_type_summ_set.remove('nan')
            # print("B")
            location_type_summ_set = {x for x in location_type_summ_set if not (isinstance(x, float) and math.isnan(x))}
            # print("C")
            if len(location_type_summ_set)==0: 
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
        
    
    all_location_types = mp_all_unique_entities_location_types.union(vp_all_unique_entities_location_types)
    result = compare_string_sets_location_types(mp_df, vp_df, all_location_types, location_type_summ_set, location_to_type)
    result['try_count'] = try_count
    return result 

def run_eval_location_types(mp_df_full,vp_df_full, misperids):
    results = []
    for misper_id in misperids:
        out_dict = evaluate_location_types(mp_df_full, vp_df_full, misper_id)
        out_dict['misperid'] = misper_id
        results.append(out_dict)
        df = pd.DataFrame(results)
        df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/location_types.pkl")
        df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/location_types.csv")
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
    # print(misperids[205:])
    
    result = run_eval_location_types(mp_df_full, vp_df_full, misperids)
    
    # print(result)
    
    df = pd.DataFrame(result)
    df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/location_types.pkl")
    df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/location_types.csv")
    