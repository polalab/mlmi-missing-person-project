from . import serialize
from .mappings import mp_column_contexts, vp_column_contexts, twenty_five_mp_questions
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
# import nltk
import numpy as np
# nltk.download('stopwords')
import re



def compare_string_sets_people(mp_df, vp_df, set_truth, set_summ, min_word_overlap=1):
    set_truth = {re.sub(r'[^\w\s]', '', str(s).lower().strip())for s in set_truth}
    set_summ =  {re.sub(r'[^\w\s]', '', str(s).lower().strip()) for s in set_summ}
    
    def get_words(text):
        # split by word
        s = set(re.findall(r'\b\w+\b', text.lower()))
        s=s-set(['nearby', 'other'])
        return s
    
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)

        overlap = words_a.intersection(words_b)
        overlap_all_a = True if len(overlap) == max(len(words_a), len(words_b)) else False
        return overlap, len(overlap), overlap_all_a
    


    partial_list=[]
    exact_matches = []
    missing_list = []
    insert_other_list = []
    false_but_in_text_list = []
    hallucination_list = []
    
    # first check for matches in the truth set
    for ent in set_truth:
        matched = False
        # find all fully matching
        for ent_in_summ in set_summ:
            _, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)
            if all_matched:
                print("full", ent_in_summ)
                matched = True
                exact_matches.append(ent)
        
        # if not matched look for partial matches
        if not matched:
            for ent_in_summ in set_summ:
                _, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)
                if overlap_count >= min_word_overlap:
                    partial_list.append((ent, ent_in_summ))
                    print("part", ent_in_summ)
                    matched = True
                    break
        #otherwise treat as missing
        if matched == False:
            print("missing", ent)
            missing_list.append(ent)
    
    
    print(exact_matches, partial_list, missing_list)
    for ent_summ in set_summ:
        # if hasn't been matched before 
        if ent_summ not in partial_list + exact_matches:
            found=False
            # may be the case that it hasn't been checked before (if at least two similar entities)
            for ent in set_truth:
                overlapping_words, overlap_count, _ = find_word_overlap(ent, ent_summ)
                if overlap_count >= min_word_overlap:
                    found = True
                    break
            if found==False:
                insert_other_list.append(ent_summ)
                # serialized="Charlotte Saunders, a 14-year-old, was reported missing from her home on Ruthven Road, Kingussie. Charlotte's foster mother, Joan, worried about her absence, informed the authorities when she did not return home. She was last seen by her friend, Sam, playing with a stranger at North Bank Dykes known for its open trails and proximity to a national park."
                serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
                serialized = re.sub(r'[^\w\s]', ' ', serialized.lower())
                # print(serialized)

                if ent_summ in serialized:
                    false_but_in_text_list.append(ent_summ)
                else:
                    hallucination_list.append(ent_summ)
    print("setsumm:", set_summ)     
    print("settruth:", set_truth)          
    print("exact:", exact_matches, len(exact_matches))
    print("partial:", partial_list)
    print(false_but_in_text_list)
    print("insert_but_in_text", false_but_in_text_list)
    print("hall:",hallucination_list)

    return {
        'potential_positive': len(set(exact_matches))+len(set(partial_list)),
        'positive': len(set(exact_matches)),
        'partial': len(set(partial_list)),
        'missing': len(set(missing_list)),
        'insert_all':len(set(false_but_in_text_list)) + len(set(hallucination_list)),
        'insert_but_in_text': len(set(false_but_in_text_list)),
        'insert_hallucination': len(set(hallucination_list)),
    }
 

def compare_string_sets(mp_df, vp_df, set_truth, set_summ, min_word_overlap=1):
    set_truth = {str(s).lower().strip() for s in set_truth}
    set_summ =  {str(s).lower().strip() for s in set_summ}
    
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        s = set(re.findall(r'\b\w+\b', text.lower()))
        s=s-set(['nearby', 'other'])
        return s
    
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)

        overlap = words_a.intersection(words_b)
        overlap_all_a = True if len(overlap) == len(words_a) else False
        return overlap, len(overlap), overlap_all_a
    
    positive = 0
    partial = 0
    partial_list=[]
    exact_matches = []
    missing = 0
    missing_list = []
    insert_other = 0
    insert_other_list = []
    false_but_in_text = 0
    false_but_in_text_list = []
    
    hallucination = 0
    hallucination_list = []
    for ent in set_truth:
        ent = ent.lower()
        ent = re.sub(r'[^\w\s]', ' ', ent)
        for ent_in_summ in set_summ:
            overlapping_words, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)

            if all_matched:
                positive+=1
                exact_matches.append(ent)
                
            else:
                ent_in_summ = re.sub(r'[^\w\s]', ' ', ent_in_summ)
                if overlap_count >= min_word_overlap:
                    partial_list.append((ent, ent_in_summ))
                    partial +=1
                    break
                else:
                    missing_list.append(ent)
                    missing+=1
    
    for ent_summ in set_summ:
        ent_summ = re.sub(r'[^\w\s]', ' ', ent_summ)
        if ent_summ not in partial_list + exact_matches:
            found = False
            for ent in set_truth:
                ent =  re.sub(r'[^\w\s]', ' ', ent)
                overlapping_words, overlap_count, _ = find_word_overlap(ent, ent_summ)
                
                if overlap_count >= min_word_overlap:
                    found = True
                    break
            if found==False:
                insert_other +=1
                insert_other_list.append(ent_summ)
                
                serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
                serialized = re.sub(r'[^\w\s]', ' ', serialized.lower())
                print(serialized)

                if ent_summ in serialized:
                    false_but_in_text +=1
                    false_but_in_text_list.append(ent_summ)
                else:
                    hallucination +=1
                    hallucination_list.append(ent_summ)
    print("setsumm:", set_summ)     
    print("settruth:", set_truth)          
    print("exact:", exact_matches, len(exact_matches))
    print("partial:", partial_list)
    print(false_but_in_text_list)
    print("insert_but_in_text", false_but_in_text_list)
    print("hall:",hallucination_list)

    return {
        'potential_positive': positive+partial,
        'positive': positive,
        'partial': partial,
        'missing': missing,
        'insert_all': insert_other,
        'insert_but_in_text': false_but_in_text,
        'insert_hallucination': hallucination,
        
    }
    

def compare_string_sets_sentence_transformers(mp_df, vp_df, set_truth, set_summ,threshold_patterns=0.7, threshold_sentence=0.5):
    set_truth = {s.lower().strip() for s in set_truth}
    set_summ =  {s.lower().strip() for s in set_summ}
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []

    def find_similarity(ent_truth, ent_summ):
        embeddings_truth = model.encode(ent_truth)
        ermbeddings_summ = model.encode(ent_in_summ)
        similarity = cosine_similarity([embeddings_truth], [ermbeddings_summ])
        return similarity
    
    positive = 0
    partial = 0
    partial_list=[]
    exact_matches = []
    missing = 0
    missing_list = []
    insert_other = 0
    insert_other_list = []
    false_but_in_text = 0
    false_but_in_text_list = []
    
    hallucination = 0
    hallucination_list = []
    for ent in set_truth:
        if ent in set_summ:
            positive+=1
            exact_matches.append(ent)
            
        else:
            
            for ent_in_summ in set_summ:                
                similarity = find_similarity(ent, ent_summ)
                
                if similarity >= threshold_patterns:
                    partial_list.append((ent, ent_in_summ))
                    partial +=1
                    break
            else:
                missing_list.append(ent)
                missing+=1
    for ent_summ in set_summ:
        ent_summ = re.sub(r'[^\w\s]', ' ', ent_summ)
        if ent_summ not in set_truth:
            
            found = False
            for ent in set_truth:
                similarity = find_similarity(ent, ent_summ)
                
                if similarity >= threshold_patterns:
                    found = True
                    break
                
            if found==False:
                insert_other +=1
                insert_other_list.append(ent_summ)
                
                serialized = serialize.mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df) + serialize.vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df, vp_column_contexts) 
                serialized_sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', serialized)
            
                found_in_text = False
                for sentence in serialized_sentences:
                    similarity =find_similarity(sentence, ent_in_summ)
                    # print(similarity, ent_in_summ, sentence)
                    if  similarity >= threshold_sentence:
                        false_but_in_text +=1
                        false_but_in_text_list.append((ent_summ, sentence))
                        found_in_text=True
                        break
                    
                if found_in_text==False:
                    hallucination +=1
                    hallucination_list.append(ent_summ)
     
                    
    print("setsumm:", set_summ)     
    print("settruth:", set_truth)          
    print("exact:", exact_matches, len(exact_matches))
    print("partial:", partial_list)
    print(false_but_in_text_list)
    print("insert_but_in_text", false_but_in_text_list)
    print("hall:",hallucination_list)
    
    return {
        'potential_positive': positive+partial,
        'positive': positive,
        'partial': partial,
        'missing': missing,
        'insert_all': insert_other,
        'insert_but_sim_sentence_in_text': false_but_in_text,
        'insert_hallucination': hallucination,
        
        'truth_set': set_truth,
        'summ_set': set_summ,
        'similar_patterns': set(partial_list),
        'similar_sentences': set(false_but_in_text_list)
        
    }
    
    
    
    
def compare_string_sets_location_types(mp_df, vp_df, set_truth, set_summ, loc_type_dict, min_word_overlap=1):
    set_truth = {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_truth}
    set_summ =  {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_summ}
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        s =  set(re.findall(r'\b\w+\b', text.lower()))
        # remove if area since missleading
        if 'area' in s:
            s.remove('area')
        return s    
            
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)

        overlap = words_a.intersection(words_b)
        overlap_all_a = True if len(overlap) == len(words_a) else False
        return overlap, len(overlap), overlap_all_a
    
    def find_similarity(ent_truth, ent_summ):
        embeddings_truth = model.encode(ent_truth)
        ermbeddings_summ = model.encode(ent_summ)
        similarity = cosine_similarity([embeddings_truth], [ermbeddings_summ])
        return similarity
    
    exact_matches = []
    partial_matches = []
    cosine_sim_truth = []
    missing_list = []
    
    total_inserted = []
    cosine_sim_loc_extract = []
    loc_in_extracted_sentence = []
    extracted_sentence_not_in_text_hall = []
    extracted_sentence_in_text_hall =[]
    extraced_location_not_in_text_hall = []
    extraced_location_in_text_hall = []
    
    serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
    serialized = re.sub(r'[^\w\s]', ' ', serialized.lower())
    

    for ent in set_truth:
        # print("A", ent)
        matched = False
        for ent_in_summ in set_summ:
            overlapping_words, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)
            if all_matched:
                print("full", ent_in_summ)
                matched = True
                exact_matches.append(ent)
        
        if not matched:
            for ent_in_summ in set_summ:
                overlapping_words, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)

                if overlap_count >= min_word_overlap:
                    partial_matches.append((ent, ent_in_summ))
                    print("part", ent_in_summ)
                    matched = True
                    break
        if not matched:
            for ent_in_summ in set_summ:
                if find_similarity(ent, ent_in_summ) >= 0.6:
                    cosine_sim_truth.append(ent_in_summ)
                    matched = True
                    break
        
        if matched == False:
            print("missing", ent)
            missing_list.append(ent)
            
    
    for ent_summ in set_summ:
        if ent_summ not in exact_matches + cosine_sim_truth + partial_matches:
            total_inserted.append(ent_summ)
            found = False
                            
            # Check similarity between the extracted location and the location's type
            locations_extracted = loc_type_dict[ent_summ]
            above_for_all = True
            for t in locations_extracted:
                cos = find_similarity(ent_summ, t[0])
                # cosine similarity between type and location 
                cosine_sim_loc_extract.append(cos)
            
            # if the location is in the extracted sentence
            for t in locations_extracted:
                overlapping_words, _, all = find_word_overlap(t[0], t[1])
                if all:
                    loc_in_extracted_sentence.append((t[0], t[1])) 
                    break
                
            # if the location is in the text at all
            for t in locations_extracted:
                extracted_loc = re.sub(r'[^\w\s]', ' ', t[0].lower())
                extracted_sent = re.sub(r'[^\w\s]', ' ', t[1].lower())
                if extracted_loc not in serialized:
                    extraced_location_not_in_text_hall.append(extracted_loc)
                else:
                    extraced_location_in_text_hall.append((extracted_loc, extracted_sent))
                    
                if extracted_sent not in serialized:
                    extracted_sentence_not_in_text_hall.append((extracted_loc, extracted_sent))
                else:
                    extracted_sentence_in_text_hall.append((extracted_loc, extracted_sent))
            
    print(set_summ)
    print(set_truth)
    print("exact_matches", exact_matches)
    print("partial_matches",partial_matches)
    print("cosine_sim_truth",cosine_sim_truth)
    print("missing_list" ,missing_list)
    
    print("total_inserted",total_inserted)
    print("cosine_sim_loc_to the extract ", cosine_sim_loc_extract)
    print("loc_in_extracted_sentence", loc_in_extracted_sentence)
    print("pxtraced_location_not_in_text_hall", extraced_location_not_in_text_hall)
    print('pxtraced_location_in_text_hall', extraced_location_in_text_hall)
    print("extracted_sentence_not_in_text_hall",extracted_sentence_not_in_text_hall)
    print("extracted_sentence_in_text_hall",extracted_sentence_in_text_hall)

    return {
        "exact_matches": len(exact_matches),
        "partial_matches": len(partial_matches),
        "cosine_sim_truth": len(cosine_sim_truth),
        "missing_from_truth": len(missing_list),
        "len_summ": len(set_summ),
        "len_truth": len(set_truth),
        "total_inserted": len(total_inserted),
        "cosine_sim_loc_extract": np.average(cosine_sim_loc_extract),
        "loc_in_extracted_sentence": len(loc_in_extracted_sentence),
        "pxtraced_location_not_in_text_hall": len(extraced_location_not_in_text_hall),
        "pxtraced_location_in_text_hall": len(extraced_location_in_text_hall),
        "extracted_sentence_not_in_text_hall": len(extracted_sentence_not_in_text_hall),
        "extracted_sentence_in_text_hall": len(extracted_sentence_in_text_hall)
        
    }
    
    
    
    
def compare_string_sets_advanced_pattern_types(mp_df, vp_df, set_truth, explanation_to_quote, set_summ, min_word_overlap=1):
    set_truth = {re.sub(r'[^a-zA-Z0-9\s]', ' ',    str(s).lower().strip()) for s in set_truth}
    set_summ =  {re.sub(r'[^a-zA-Z0-9\s]', ' ',    str(s).lower().strip()) for s in set_summ}
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        s =  set(re.findall(r'\b\w+\b', text.lower()))
        # remove if area since missleading
        if 'pattern' in s:
            s.remove('pattern')
        return s    
            
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)

        overlap = words_a.intersection(words_b)
        overlap_all_a = True if len(overlap) == len(words_a) else False
        return overlap, len(overlap), overlap_all_a
    
    def find_similarity(ent_truth, ent_summ):
        embeddings_truth = model.encode(ent_truth)
        ermbeddings_summ = model.encode(ent_summ)
        similarity = cosine_similarity([embeddings_truth], [ermbeddings_summ])
        return similarity
    
    exact_matches = []
    partial_matches = []
    cosine_sim_truth = []
    missing_list = []
    
    total_inserted = []
    cosine_sim_pat_extract = []
    pat_in_extracted_sentence = []
    extracted_sentence_not_in_text_hall = []
    extracted_sentence_in_text_hall =[]
    extraced_pattern_not_in_text_hall = []
    extraced_pattern_in_text_hall = []
    
    serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
    serialized = re.sub(r'[^a-zA-Z0-9\s]', ' ', serialized.lower())
    

    for ent in set_truth:
        # print("A", ent)
        matched = False
        for ent_in_summ in set_summ:
            overlapping_words, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)
            if all_matched:
                print("full", ent_in_summ)
                matched = True
                exact_matches.append(ent)
        
        if not matched:
            for ent_in_summ in set_summ:
                overlapping_words, overlap_count, all_matched = find_word_overlap(ent, ent_in_summ)

                if overlap_count >= min_word_overlap:
                    partial_matches.append((ent, ent_in_summ))
                    print("part", ent_in_summ)
                    matched = True
                    break
        if not matched:
            for ent_in_summ in set_summ:
                if find_similarity(ent, ent_in_summ) >= 0.4:
                    cosine_sim_truth.append((ent, ent_in_summ))
                    matched = True
                    break
        
        if matched == False:
            print("missing", ent)
            missing_list.append(ent)
            
    
    for ent_summ in set_summ:
        if ent_summ not in exact_matches + cosine_sim_truth + partial_matches:
            total_inserted.append(ent_summ)
            found = False
                            
            # Check similarity between the extracted explanation and quote
            locations_extracted = explanation_to_quote[ent_summ]
            above_for_all = True
            for t in locations_extracted:
                cos = find_similarity(ent_summ, t[0])
                # cosine similarity between type and location 
                cosine_sim_pat_extract.append(cos)
            
            # if the location is in the extracted sentence
            for t in locations_extracted:
                overlapping_words, _, all = find_word_overlap(t[0], t[1])
                if all:
                    pat_in_extracted_sentence.append((t[0], t[1])) 
                    break
                
            # if the location is in the text at all
            for t in locations_extracted:
                extracted_loc = re.sub(r'[^a-zA-Z0-9\s]', ' ', t[0].lower().strip())
                extracted_sent = re.sub(r'[^a-zA-Z0-9\s]', ' ', t[1].lower().strip())
                if extracted_loc not in serialized:
                    extraced_pattern_not_in_text_hall.append(extracted_loc)
                else:
                    extraced_pattern_in_text_hall.append((extracted_loc, extracted_sent))
                    
                if extracted_sent not in serialized:
                    extracted_sentence_not_in_text_hall.append((extracted_loc, extracted_sent))
                else:
                    extracted_sentence_in_text_hall.append((extracted_loc, extracted_sent))
            
    print(set_summ)
    print(set_truth)
    print("exact_matches", exact_matches)
    print("partial_matches",partial_matches)
    print("cosine_sim_truth",cosine_sim_truth)
    print("missing_list" ,missing_list)
    
    print("total_inserted",total_inserted)
    print("cosine_sim_pat_to the extract ", cosine_sim_pat_extract)
    print("pat_in_extracted_sentence", pat_in_extracted_sentence)
    print("extraced_pattern_not_in_text_hall", extraced_pattern_not_in_text_hall)
    print('extraced_pattern_in_text_hall', extraced_pattern_in_text_hall)
    print("extracted_sentence_not_in_text_hall",extracted_sentence_not_in_text_hall)
    print("extracted_sentence_in_text_hall",extracted_sentence_in_text_hall)

    return {
        "exact_matches": len(exact_matches),
        "partial_matches": len(partial_matches),
        "len_cosine_sim_truth": len(cosine_sim_truth),
        "missing_from_truth": len(missing_list),
        "len_summ": len(set_summ),
        "len_truth": len(set_truth),
        "total_inserted": len(total_inserted),
        "cosine_sim_pat_extract": np.average(cosine_sim_pat_extract),
        "pat_in_extracted_sentence": len(pat_in_extracted_sentence),
        "pxtraced_pattern_not_in_text_hall": len(extraced_pattern_not_in_text_hall),
        "pxtraced_pattern_in_text_hall": len(extraced_pattern_in_text_hall),
        "extracted_sentence_not_in_text_hall": len(extracted_sentence_not_in_text_hall),
        "extracted_sentence_in_text_hall": len(extracted_sentence_in_text_hall),
        'set_summ': set_summ,
        'set_truth': set_truth,
        'cosine_sim_truth': cosine_sim_truth
        
    }
           
    
    
def compare_string_sets_patterns_types(mp_df, vp_df, set_truth, set_summ, min_word_overlap=1):
    set_truth = {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_truth}
    set_summ =  {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_summ}
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        s =  set(re.findall(r'\b\w+\b', text.lower()))
        # remove if dissappearance since missleading and remove all stopwords
        s = s-set(['dissappearance'])
        stop_words = set(stopwords.words('english'))
        return s - stop_words
        
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)

        overlap = words_a.intersection(words_b)
        overlap_all_a = True if len(overlap) == len(words_a) else False
        return overlap, len(overlap), overlap_all_a
    
    def find_similarity(ent_truth, ent_summ):
        embeddings_truth = model.encode(ent_truth)
        ermbeddings_summ = model.encode(ent_summ)
        similarity = cosine_similarity([embeddings_truth], [ermbeddings_summ])
        return similarity
    
    exact_matches = []
    partial_matches = []
    cosine_sim_truth = []
    missing_list = []
    
    total_inserted = []
    
    
    serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
    serialized = re.sub(r'[^\w\s]', ' ', serialized.lower())
    for ent in set_truth:
        found_partial = False
        ent = ent.lower()
        if ent in set_summ:
            exact_matches.append(ent)
            
        else:
            for ent_in_summ in set_summ:
                ent_in_summ = re.sub(r'[^\w\s]', ' ', ent_in_summ)
                _, overlap_count, _ = find_word_overlap(ent, ent_in_summ)
                if overlap_count >= min_word_overlap:
                    partial_matches.append(ent_in_summ)
                    found_partial=True
                    break
            for ent_in_summ in set_summ:
                ent_in_summ = re.sub(r'[^\w\s]', ' ', ent_in_summ)
                if find_similarity(ent, ent_in_summ) >= 0.5:
                    cosine_sim_truth.append(ent_in_summ)
                    found_partial = True
                    break
            
            if found_partial==False:  
                missing_list.append(ent)
                
    
    for ent_summ in set_summ:
        if ent_summ not in exact_matches + cosine_sim_truth + partial_matches:
            total_inserted.append(ent_summ)
            
                        
            
            
        
               
    print(set_summ)
    print(set_truth)
    print("exact_matches", exact_matches)
    print("partial_matches",partial_matches)
    print("cosine_sim_truth",cosine_sim_truth)
    print("missing_list" ,missing_list)
    
    print("total_inserted",total_inserted)

    return {
        "exact_matches": len(exact_matches),
        "partial_matches": len(partial_matches),
        "cosine_sim_truth": len(cosine_sim_truth),
        "missing_from_truth": len(missing_list),
        "len_summ": len(set_summ),
        "len_truth": len(set_truth),
        "total_inserted": len(total_inserted)
    }
    