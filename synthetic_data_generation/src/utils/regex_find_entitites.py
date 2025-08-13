import re
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def preprocess_text(text):
    # tokenize the text
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    
    # remove punctuation and stop words
    cleaned_tokens = [
        token for token in tokens 
        if token not in string.punctuation and token not in stop_words
    ]
    
    return ' '.join(cleaned_tokens)

def find_partial_matches(entities, text):
    
    """Find partial matches and return only the matched portions"""
    partial_matches = []
    processed_text = preprocess_text(text)
    
    for entity in entities:
        # Remove punctuation from entity first, then split into words
        entity_no_punct = ''.join(char for char in entity if char not in string.punctuation)
        entity_words = entity_no_punct.split()
        best_match = None
        
        # Try different combinations starting from full entity down to individual words
        for i in range(len(entity_words)):
            for j in range(len(entity_words), i, -1):
                partial = ' '.join(entity_words[i:j])
                processed_partial = preprocess_text(partial)
                
                # Check if this partial entity appears in the processed text
                if processed_partial in processed_text:
                    best_match = partial
                    break
            if best_match:
                break
        
        if best_match:
            partial_matches.append(best_match)
    
    return partial_matches

def search_entity(entity, text, no_partial_matches=False):
    processed_text = preprocess_text(text)
    processed_entity = preprocess_text(entity)
    
    if no_partial_matches:
        pattern = r'\b' + re.escape(processed_entity) + r'\b'
        return bool(re.search(pattern, processed_text))
    else:
        return processed_entity in processed_text
    

def regex_find_people_locations(narrative, people_names, people_desc, people_relat, landmarks, addresses, location_types):
    people_names_used = find_partial_matches(people_names, narrative)
    people_desc_used = find_partial_matches(people_desc, narrative)
    people_relat_used = find_partial_matches(people_relat, narrative)
    landmarks_used = find_partial_matches(landmarks, narrative)
    addresses_used = find_partial_matches(addresses, narrative)
    location_types_used = find_partial_matches(location_types, narrative)
    return people_names_used, people_desc_used, people_relat_used, landmarks_used, addresses_used, location_types_used
    

# Testing example
if __name__ == "__main__":
    locations = ['Home', 'Dee Street, Banchory, AB31 5HS', 'Golden Knowes Road, Aberdeenshire, AB45 2JE']
    people = ['sister', 'Karen', 'friend']
    
    narrative = "Gemma Atkins was last seen by her sister at Home on Dee Street, Banchory. On the day of her disappearance, she failed to pick up her child from school. Concern grew among family and friends, especially after personal items were discovered left behind at her residence. A friend indicated that Gemma might have been experiencing difficulties and was believed to be homeless. She was eventually located at a residence on Golden Knowes Road, Aberdeenshire. The police confirmed she was safe and unharmed."
    
    location_matches = find_partial_matches(locations, narrative)
    people_matches = find_partial_matches(people, narrative)
    
    # print("Location matches:", location_matches)
    # print("People matches:", people_matches)
    
    
    narrative = 'Janet Dunn was last seen at Home, 312 Greengairs Road. Her brother found her in the bathroom, confused. Traced safely later. '
    people_names = ['Sylvia Bates', 'John Russell', 'Edward Doyle']
    people_desc = ['brother', 'friend', 'grandfather']
    people_relat = []
    landmarks = ['Home']
    addresses = ['Longman Drive, Inverness, IV1 1SU', '312 Greengairs Road, Greengairs, ML6 7TQ']
    print(regex_find_people_locations(narrative, people_names, people_desc, people_relat, landmarks, addresses))
                        