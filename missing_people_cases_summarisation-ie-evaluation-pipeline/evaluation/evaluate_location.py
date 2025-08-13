import extraction.summarisation_functions as summ_func
import pandas as pd
from extraction.utils.compare_sets import compare_string_sets, compare_string_sets_sentence_transformers
import math
import csv
from io import StringIO


def evaluate_location_types(mp_df_full, vp_df_full, misper_id):

    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # 10 tries
    location_type_summ_set = {}
    temp = 0.1
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.locations_advanced_extraction_pipleine_addresses_types("locations_types_3.1", mp_df, vp_df, misper_id, temp=temp)
            
            location_type_summ = []
            

            with open(f"summaries/fake/{misper_id}/locations/locations_types_3.1.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            reader = csv.reader(StringIO(line))
                            location_type = next(reader)[2]
                            location_type_summ.append(location_type)
                        except:
                            continue
            location_type_summ_set = set(location_type_summ)
            

            if 'nan' in location_type_summ_set:
                location_type_summ_set.remove('nan')
            print("B")
            location_type_summ_set = {x for x in location_type_summ_set if not (isinstance(x, float) and math.isnan(x))}
            print("C")
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
    result = compare_string_sets_sentence_transformers(mp_df, vp_df, all_location_types, location_type_summ_set)
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



def evaluate_locations(mp_df_full, vp_df_full, misper_id):
    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # 10 tries
    location_summ_set = {}
    temp = 0.1
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.locations_extraction_pipleine_addresses_and_landmarks("locations_3.1", mp_df, vp_df, misper_id, temp=temp)
            
            location_summ = []
            with open(f"summaries/fake/{misper_id}/locations/locations_3.1.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            location_type = ','.join( line.split(",")[:-1])
                            print("A", location_type)
                            location_summ.append(location_type)
                        except:
                            continue
                print("d", location_summ)
            location_summ_set = set(location_summ)
            print("wtf", location_summ)
            

            if 'nan' in location_summ:
                location_summ_set.remove('nan')
            print("B")
            location_summ_set = {x for x in location_summ_set if not (isinstance(x, float) and math.isnan(x))}
            print("C")
            if len(location_summ_set)==0: 
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
        
    
    all_locations = mp_all_unique_entities_landmarks.union(mp_all_unique_entities_addresses).union(vp_all_unique_entities_addresses).union(vp_all_unique_entities_landmarks)
    result = compare_string_sets(mp_df, vp_df, all_locations, location_summ_set, min_word_overlap=1)
    result['try_count'] = try_count
    result['truth_set'] = all_locations
    result['summ_set'] = location_summ_set
    return result 

def run_eval_locations(mp_df_full,vp_df_full, misperids):
    results = []
    for misper_id in misperids:
        out_dict = evaluate_locations(mp_df_full, vp_df_full, misper_id)
        out_dict['misperid'] = misper_id
        results.append(out_dict)
        df = pd.DataFrame(results)
        df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/locations.pkl")
        df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/locations.csv")
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
    
    
    run_eval_locations(mp_df_full, vp_df_full, misperids)
    run_eval_location_types(mp_df_full, vp_df_full, misperids)
    
    # print(result)
    
    # df = pd.DataFrame(result)
    # df.to_pickle("RESULTS/locations.pkl")
    # df.to_csv("RESULTS/locations.csv")
    