import extraction.summarisation_functions as summ_func
import pandas as pd
from extraction.utils.compare_sets import compare_string_sets, compare_string_sets_people
import math


def evaluate_people(mp_df_full, vp_df_full, misper_id):

    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # Maximum 10 tries
    people_summ_set = {}
    temp = 0.1
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.people_advanced_extraction_pipleine_assosiation_network("people_assograph_3.1", mp_df, vp_df, misper_id, temp=temp)
            people_summ = pd.read_csv(f"summaries/fake/{misper_id}/assosiation_network/people_assograph_3.1.txt", names=['person', 'asso', 'relat', 'id'], header=0)
                        
            people_summ_set = set((people_summ['asso'] + ' ' + people_summ['relat']).to_list())
            if 'nan' in people_summ_set:
                people_summ_set.remove('nan')
            
            # if 'nan' in people_summ_relat_set:
            #     people_summ_relat_set.remove('nan')
        
            people_summ_set = {x for x in people_summ_set if not (isinstance(x, float) and math.isnan(x))}
            # people_summ_relat_set = {x for x in people_summ_relat_set if not (isinstance(x, float) and math.isnan(x))}
            
            
            if len(people_summ_set)==0: 
                continue
            else:
                break
        except Exception as e:
            print("error", e)
            # increase the randomness
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
    mp_people_all = mp_all_unique_entities_people_names.union(mp_all_unique_entities_people_desc, mp_all_unique_entities_people_relat)
    vp_people_all = vp_all_unique_entities_people_names.union(vp_all_unique_entities_people_desc, vp_all_unique_entities_people_relat)
    people_all = mp_people_all.union(vp_people_all)
    people_all.add(mp_df['forenames'].iloc[0] + ' ' + mp_df['surname'].iloc[0])

    
    print("misper", misper_id, "|", people_summ_set, "|" ,people_all)
    result = compare_string_sets_people(mp_df, vp_df, people_all, people_summ_set, min_word_overlap=1)
    
    
    print(people_all)
    print("|", people_summ_set)
    print("\n")
    result['try_count'] = try_count
    result['truth_set'] = people_all
    result['summ_set'] = people_summ_set
    return result
    
    
def run_eval_people(mp_df_full,vp_df_full, misperids):
    results = []
    for misper_id in misperids:
        out_dict = evaluate_people(mp_df_full, vp_df_full, misper_id)
        out_dict['misperid'] = misper_id
        results.append(out_dict)
        df = pd.DataFrame(results)
        df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/people.pkl")
        df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/people.csv")
    return results

if __name__=="__main__":
    # print(os.getcwd())
    import torch
    torch.cuda.empty_cache()
    mp_df_full = pd.read_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/DATA/fake/fake_mp_data.csv")
    vp_df_full = pd.read_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/DATA/fake/fake_vp_data.csv")
    vp_df_full.columns = vp_df_full.columns.str.lower()
    
    misperids = mp_df_full['misperid'].drop_duplicates().to_list()
    
    misperids = sorted(misperids)[166:]
    print(misperids)
    
    result = run_eval_people(mp_df_full, vp_df_full, misperids)
    
    # print(result)
    
    df = pd.DataFrame(result)
    df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/people.pkl")
    df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/people.csv")
    