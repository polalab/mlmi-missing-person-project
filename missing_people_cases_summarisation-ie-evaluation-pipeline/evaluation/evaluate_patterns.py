import extraction.summarisation_functions as summ_func
import pandas as pd
from extraction.utils.compare_sets import compare_string_sets_patterns_types
import math
import csv
from io import StringIO
import re
import ast
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def find_max_similarity(pattern_to_sentences):
    pattern, sentences = pattern_to_sentences

    if isinstance(sentences, str):
        sentences = [s.strip() for s in re.split(r'[,.?!]', sentences) if s.strip()]

    if not sentences:
        print("Error: No valid sentences to compare.")
        return 0, (pattern, "EMPTY RECORD")

    embeddings = model.encode([pattern] + sentences)
    
    pattern_embed = embeddings[0].reshape(1, -1)
    sentence_embeddings = embeddings[1::]
    
    cosine_scores = cosine_similarity(pattern_embed, sentence_embeddings)
    max_index = np.argmax(cosine_scores)
    
    max_score = cosine_scores[0, max_index]
    best_sentence = sentences[max_index]
   
    return max_score, (pattern, best_sentence, max_score)



def evaluate_pattern_types(mp_df_full, vp_df_full, misper_id):

    mp_df = mp_df_full[mp_df_full['misperid']==misper_id]
    vp_df = vp_df_full[vp_df_full['misper_misperid']==misper_id]
    try_count = 1
    
    # 10 tries
    pattern_type_summ_set = {}
    temp = 0.1
    average_of_mean_max_cos_to_sentence = []
    for i in range (10):     
        print("try:", try_count, misper_id)
        try:       
            summ_func.patterns_advanced_extraction_pipleine("full_advanced_pattern_types_3.1", mp_df, vp_df, misper_id, temp=temp)
            
            ids_hallucinated = 0
            no_ids = 0
            average_of_mean_max_cos_to_sentence = []
            max_cos_to_sentence_tuples = []
            pattern_type_summ = []
            with open(f"summaries/fake/{misper_id}/patterns/full_advanced_pattern_types_3.1.txt", "r") as file:
                for line in file:
                    pattern_to_sentence = []
                    
                    line = line.strip()
                    if line:
                        try:
                            reader = csv.reader(StringIO(line))
                            pat = next(reader)
                            pattern_type =  re.sub(r'[^\w\s]', ' ', pat[0].lower())
                            pattern_ids =  ast.literal_eval(','.join(pat[1::]))
                            pattern_type_summ.append(pattern_type)
                           
                            no_ids = len(pattern_ids)
                            for id in pattern_ids:
                                circumstances = ''
                                if id in mp_df['reportid'].to_list():
                                    circumstances =  mp_df[mp_df['reportid']==id].iloc[0]['circumstances']
                                    if isinstance(circumstances, float) and math.isnan(circumstances):
                                        print("UWAGA NAN", id, misper_id)
                                        circumstances = ''
                                    pattern_to_sentence.append((pattern_type, circumstances))
                                elif id in vp_df['VPD_NOMINALINCIDENTID_PK'.lower()].to_list():
                                    circumstances= vp_df[vp_df['VPD_NOMINALINCIDENTID_PK'.lower()]==id].iloc[0]['VPD_NOMINALSYNOPSIS'.lower()]
                                    if isinstance(circumstances, float) and math.isnan(circumstances):
                                        print("UWAGA NAN", id, misper_id)
                                        circumstances = ''
                                    pattern_to_sentence.append((pattern_type,circumstances))
                                else:
                                    ids_hallucinated +=1
                                    
                          
                            if pattern_to_sentence:
                                avg_max_sims = []
                                for p_t_s in pattern_to_sentence:
                                    score, tuple_pattern_to_sent = find_max_similarity(p_t_s)
                                    avg_max_sims.append(score) 
                                    max_cos_to_sentence_tuples.append(tuple_pattern_to_sent)
                                avg_max_sim = np.mean([avg_max_sims])
                                
                            else:
                                avg_max_sim = np.nan
                            average_of_mean_max_cos_to_sentence.append(avg_max_sim)
                            
                        except Exception as e:
                            raise ValueError(f"could not parse properly {e}")
            
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
        
    
    all_pattern_types = mp_all_unique_entities_pattern_types.union(vp_all_unique_entities_pattern_types)
    
    # print("max_cos_to_sentence_tuples", max_cos_to_sentence_tuples)
    result = compare_string_sets_patterns_types(mp_df, vp_df, all_pattern_types, pattern_type_summ_set)
    result['try_count'] = try_count
    result['average_of_mean_max_cos_to_sentence'] = np.mean(average_of_mean_max_cos_to_sentence) if len(average_of_mean_max_cos_to_sentence) else np.nan
    result['no_ids'] = no_ids
    result['truth_set'] = all_pattern_types
    result['summ_set'] = pattern_type_summ_set
    result['max_cos_to_sentence_tuples'] = max_cos_to_sentence_tuples
    return result 

def run_eval_pattern_types(mp_df_full,vp_df_full, misperids):
    results = []
    for misper_id in misperids:
        out_dict = evaluate_pattern_types(mp_df_full, vp_df_full, misper_id)
        out_dict['misperid'] = misper_id
        results.append(out_dict)
        df = pd.DataFrame(results)
        df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns.pkl")
        df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns.csv")
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
    # print(misperids)
    # misperids = misperids
    # print(misperids)

    result = run_eval_pattern_types(mp_df_full, vp_df_full, misperids)
    
    # print(result)
    
    df = pd.DataFrame(result)
    df.to_pickle("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns.pkl")
    df.to_csv("/home/pzl22/rds/hpc-work/llama-work/missing_people_cases_summarisation/RESULTS/patterns.csv")
    