from utils import serialize
from utils.mappings import mp_column_contexts, vp_column_contexts, twenty_five_mp_questions
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity






    


    


    





    










    
















                    














    





            






            

            






                    












        

    
    
def compare_string_sets_sentence_transformers(mp_df, vp_df, set_truth, set_summ, threshold=0.6):
    set_truth = {re.sub(r'[^\w\s]', ' ', s.lower().strip())  for s in set_truth}
    set_summ =  {re.sub(r'[^\w\s]', ' ', s.lower().strip()) for s in set_summ}
    print(set_truth, set_summ)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []

    def find_similarity(ent_truth, ent_summ):
        embeddings_truth = model.encode(ent_truth)
        ermbeddings_summ = model.encode(ent_summ)
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
                similarity = find_similarity(ent, ent_in_summ)
                
                if similarity >= threshold:
                    print("partial", similarity, ent, ent_in_summ)
                    partial_list.append((ent, ent_in_summ))
                    partial +=1
                    break
                else:
                    missing_list.append(ent)
                    missing+=1
                    
                
    for ent_summ in set_summ:
        if ent_summ not in set_truth:
            found = False
            for ent in set_truth:
                similarity = find_similarity(ent, ent_in_summ)
                
                if similarity >= threshold:
                    print(similarity, ent, ent_summ)
                    found = True
                    break
                
            if found==False:
                insert_other +=1
                insert_other_list.append(ent_summ)
                
                serialized = serialize.mp_serialize_dataframe_for_llm_cirumstancesonly(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm_nominalsynopsisonly(vp_df) 
                serialized_sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', serialized)  
                found_in_text = False
                for sentence in serialized_sentences:

                    similarity =find_similarity(sentence, ent_in_summ)

                    if similarity >=0.3:
                        print(similarity, sentence, ent_summ)
                    if  similarity >= threshold:
                        
                        false_but_in_text +=1
                        false_but_in_text_list.append((ent_summ, sentence))
                        found_in_text=True
                        break
                    
                if found_in_text==False:
                    hallucination +=1
                    hallucination_list.append(ent_summ)
     
                    
    print("===========================")

    print(partial_list)
    print(false_but_in_text_list)

    return {
        'potential_positive': positive+partial,
        'positive': positive,
        'partial': partial,
        'missing': missing,
        'insert_all': insert_other,
        'insert_but_in_text': false_but_in_text,
        'insert_hallucination': hallucination,
        
    }
    
    

    





def compare_string_sets_location_themes(mp_df, vp_df, set_truth, set_summ,  min_word_overlap=1):
    set_truth = {s.lower().strip() for s in set_truth}
    set_summ =  {s.lower().strip() for s in set_summ}
    
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        return set(re.findall(r'\b\w+\b', text.lower()))
    
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)
        overlap = words_a.intersection(words_b)
        return overlap, len(overlap)
    
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
                overlapping_words, overlap_count = find_word_overlap(ent, ent_in_summ)
                if overlap_count >= min_word_overlap:
                    partial_list.append((ent, ent_in_summ))
                    partial +=1
                    break
            else:
                missing_list.append(ent)
                missing+=1
    for ent_summ in set_summ:
        if ent_summ not in set_truth:
            
            found = False
            for ent in set_truth:
                overlapping_words, overlap_count = find_word_overlap(ent, ent_summ)
                
                if overlap_count >= min_word_overlap:
                    found = True
                    break
            if found==False:
                insert_other +=1
                insert_other_list.append(ent_summ)
                
                serialized = serialize.mp_serialize_dataframe_for_llm(mp_df, mp_column_contexts, twenty_five_mp_questions) + serialize.vp_serialize_dataframe_for_llm(vp_df, vp_column_contexts) 
                
                if ent_summ in serialized:
                    false_but_in_text +=1
                    false_but_in_text_list.append(ent_summ)
                else:
                    hallucination +=1
                    hallucination_list.append(ent_summ)
                    
    print("exact:", exact_matches, len(exact_matches))
    print("partial:", partial_list)
    print(false_but_in_text_list)
    print(hallucination_list)
    return {
        'potential_positive': positive+partial,
        'positive': positive,
        'partial': partial,
        'missing': missing,
        'insert_all': insert_other,
        'insert_but_in_text': false_but_in_text,
        'insert_hallucination': hallucination,
        
    }
    
    
    
def compare_string_sets(mp_df, vp_df, set_truth, set_summ, min_word_overlap=1):
    set_truth = {str(s).lower().strip() for s in set_truth}
    set_summ =  {str(s).lower().strip() for s in set_summ}
    
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        return set(re.findall(r'\b\w+\b', text.lower()))
    
    def find_word_overlap(str_a, str_b):
        words_a = get_words(str_a)
        words_b = get_words(str_b)
        overlap = words_a.intersection(words_b)
        return overlap, len(overlap)
    
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
        if ent in set_summ:
            positive+=1
            exact_matches.append(ent)
            
        else:
            for ent_in_summ in set_summ:
                ent_in_summ = re.sub(r'[^\w\s]', ' ', ent_in_summ)
                overlapping_words, overlap_count = find_word_overlap(ent, ent_in_summ)
                if overlap_count >= min_word_overlap:
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
                overlapping_words, overlap_count = find_word_overlap(ent, ent_summ)
                
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
    print("missing:", missing_list)
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
    
    
def compare_string_sets_location_types(mp_df, vp_df, set_truth, set_summ, loc_type_dict, min_word_overlap=1):
    set_truth = {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_truth}
    set_summ =  {re.sub(r'[^\w\s]', ' ',    str(s).lower().strip()) for s in set_summ}
    model = SentenceTransformer("all-MiniLM-L6-v2")
    partial_matches = []
    missing_items = []
    
    def get_words(text):
        s =  set(re.findall(r'\b\w+\b', text.lower()))

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
                if find_similarity(ent, ent_in_summ) >= 0.6:
                    cosine_sim_truth.append(ent_in_summ)
                    found_partial = True
                    break
            
            if found_partial==False:  
                missing_list.append(ent)
                
    
    for ent_summ in set_summ:
        if ent_summ not in exact_matches + cosine_sim_truth + partial_matches:
            total_inserted.append(ent_summ)
            found = False
                            

            locations_extracted = loc_type_dict[ent_summ]
            above_for_all = True
            for t in locations_extracted:
                cos = find_similarity(ent_summ, t[0])

                if cos < 0.4:
                    above_for_all = False
                    break
            if above_for_all:
                cosine_sim_loc_extract.append((ent_summ, t[0]))
            
            
            

            for t in locations_extracted:
                overlapping_words, _, all = find_word_overlap(t[0], t[1])
                if all:
                    loc_in_extracted_sentence.append((t[0], t[1])) 
                    break
                

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
        "cosine_sim_loc_extract": len(cosine_sim_loc_extract),
        "loc_in_extracted_sentence": len(loc_in_extracted_sentence),
        "pxtraced_location_not_in_text_hall": len(extraced_location_not_in_text_hall),
        "pxtraced_location_in_text_hall": len(extraced_location_in_text_hall),
        "extracted_sentence_not_in_text_hall": len(extracted_sentence_not_in_text_hall),
        "extracted_sentence_in_text_hall": len(extracted_sentence_in_text_hall)
        
    }
    