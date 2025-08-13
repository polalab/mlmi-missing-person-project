import pandas as pd
from utils.ask_open_ai import ask_open_ai
import ast
import re


def analyze_entity_coverage(summary, entities):
    # Normalize summary (lowercase, clean whitespace)
    summary_clean = re.sub(r'\s+', ' ', summary.lower().strip())
    
    exact_matches = []
    partial_matches = []
    missing = []
    
    for entity in entities:
        entity_clean = entity.lower().strip()
        
        # Check for exact match
        exact_found = False
        if ' ' in entity_clean:
            # Multi-word entity - check as complete phrase
            exact_found = entity_clean in summary_clean
        else:
            # Single word - check with word boundaries to avoid partial word matches
            pattern = r'\b' + re.escape(entity_clean) + r'\b'
            exact_found = bool(re.search(pattern, summary_clean))
        
        if exact_found:
            exact_matches.append(entity)
            continue
        
        # Check for partial match
        partial_info = None
        entity_words = entity_clean.split()
        
        if len(entity_words) == 1:
            # Single word - check if it appears as substring
            if entity_clean in summary_clean:
                # Find all occurrences to show context
                matches = []
                start = 0
                while True:
                    pos = summary_clean.find(entity_clean, start)
                    if pos == -1:
                        break
                    # Get some context around the match
                    context_start = max(0, pos - 10)
                    context_end = min(len(summary_clean), pos + len(entity_clean) + 10)
                    context = summary_clean[context_start:context_end].strip()
                    matches.append(context)
                    start = pos + 1
                
                partial_info = {
                    'entity': entity,
                    'found_parts': [entity_clean],
                    'contexts': matches
                }
        else:
            # Multi-word - find which words are present
            found_words = []
            found_contexts = []
            
            for word in entity_words:
                if len(word) > 3:  # Skip short words like "of", "in", "at"
                    if re.search(r'\b' + re.escape(word) + r'\b', summary_clean):
                        found_words.append(word)
                        # Get context for this word
                        match = re.search(r'\b' + re.escape(word) + r'\b', summary_clean)
                        if match:
                            pos = match.start()
                            context_start = max(0, pos - 10)
                            context_end = min(len(summary_clean), pos + len(word) + 10)
                            context = summary_clean[context_start:context_end].strip()
                            found_contexts.append(f"{word}: ...{context}...")
            
            # Consider partial match if at least half the significant words found
            significant_words = sum(1 for word in entity_words if len(word) > 2)
            if significant_words > 0 and len(found_words) >= max(1, significant_words // 2):
                partial_info = {
                    'entity': entity,
                    'found_parts': found_words,
                    'missing_parts': [word for word in entity_words if len(word) > 2 and word not in found_words],
                    'contexts': found_contexts
                }
        
        if partial_info:
            partial_matches.append(partial_info)
        else:
            missing.append(entity)
    
    # Calculate results
    total_entities = len(entities)
    covered_entities = len(exact_matches) + len(partial_matches)
    coverage_percentage = (covered_entities / total_entities * 100) if total_entities > 0 else 0
    
    return {
        'exact_matches': exact_matches,
        'partial_matches': partial_matches,
        'missing': missing,
        'counts': {
            'exact': len(exact_matches),
            'partial': len(partial_matches),
            'missing': len(missing),
            'total': total_entities
        },
        'coverage_percentage': round(coverage_percentage, 2)
    }
    
    
    
def count_unique_entities(summary_extracted_entities, all_entitites):
    hallucinations = summary_extracted_entities - all_entitites
    return {
        'hallucinations': len(hallucinations),
        'words': hallucinations
    }
    



def extract_entites_summary(summary):
    prompt = f'''
    Extract people names and location names from the following text. Make sure to include both names as well as more general descriptors of people as well as addresses and more general descriptions of places. Return as two lines where entities are separated by commas with one empty line between people and location entities lists.
    The text:
    {summary}
    '''
    response = ask_open_ai(prompt=prompt, system_prompt=None).split('\n')
    people =  [item.strip() for item in response[0].split(',')]
    locations = [item.strip() for item in response[2].split(',')]
    
    return set(people), set(locations)



def score(misperid, mp_data_file, vp_data_file, summary):
    mp_df = pd.read_csv(mp_data_file)
    vp_df = pd.read_csv(vp_data_file)
    mp_df = mp_df[mp_df['misperid']==misperid]
    vp_df = vp_df[vp_df['misper_misperid']==misperid]
    
    all_locations_entities = set()
    for location in mp_df['entities_locations']:
        all_locations_entities.update(ast.literal_eval(location))
    for location in vp_df['entities_locations']:
        all_locations_entities.update(ast.literal_eval(location))
    for loc in mp_df['pob']:  # TODO: quick fix
        all_locations_entities.add(loc) 
    for loc in vp_df['VPD_PLACEOFBIRTH']:
        all_locations_entities.add(loc) 
    
        
    all_people_entities = set()
    for person in mp_df['entities_people']:
        all_people_entities.update(ast.literal_eval(person))
    for person in vp_df['entities_people']:
        all_people_entities.update(ast.literal_eval(person))
    for person in vp_df['VPD_CONSENTNAME']:  # TODO: quick fix
        all_people_entities.add(person)
        
    
    
    results_people = analyze_entity_coverage(summary, all_people_entities)
    results_locations  = analyze_entity_coverage(summary, all_locations_entities)
    
    entities_summary_people, entities_summary_locations = extract_entites_summary(summary)
    results_people_hall = count_unique_entities(entities_summary_people, all_people_entities)
    results_locations_hall = count_unique_entities(entities_summary_locations, all_locations_entities)
    
    results_dict =  {
        "people_entities: ": results_people['counts'],
        "people_entities_coverage_percentage: ": results_people['counts'],
        'people_hallucinations': results_people_hall['hallucinations'],
        
        "locations_entities: ": results_locations['counts'],
        "locations_entities_coverage_percentage: ": results_locations['counts'],
        'locations_hallucinations': results_locations_hall['hallucinations'],
    }
    
    results_full =  {
        "people_entities: ": results_people,
        'people_hallucinations': results_people_hall,
        
        "locations_entities: ": results_locations,
        'locations_hallucinations': results_locations_hall,
    }
    
    print(results_people)
    total_accuracy = (results_people['counts']['exact'] + results_locations['counts']['exact']) / (results_people['counts']['total'] + results_locations['counts']['total'])
    total_potential_accuracy = (results_people['counts']['exact'] + results_people['counts']['partial'] + results_locations['counts']['exact'] + results_locations['counts']['partial']) / (results_people['counts']['total'] + results_locations['counts']['total'])
    people_accuracy =  (results_people['counts']['exact']) / (results_people['counts']['total'])
    locations_accuracy = (results_locations['counts']['exact']) / (results_locations['counts']['total'])
    
    results_accuracy = {
        'accuracy': total_accuracy,
        'total_potential_accuracy': total_potential_accuracy,
        'people_accuracy': people_accuracy,
        'people_hallucinations_count': results_people_hall['hallucinations'],
        'locations_accuracy': locations_accuracy,
        'locations_hallucinations_count': results_locations_hall['hallucinations'],
    }
    return results_accuracy, results_dict, results_full