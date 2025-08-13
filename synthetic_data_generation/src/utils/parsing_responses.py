import re
import ast
from utils import question_list

def parse_api_response_narrative_people_places(s):
        try:
            pattern = r'narrative\s*=\s*(?:"(.*?)"|((?:(?!\s*people\s*=|\n).)+))'
            match = re.search(pattern, s, re.DOTALL)

            if match:
                narrative = match.group(1) or match.group(2)
            else:
                print("No narrative found.")
            
            people_match = re.search(r"people\s*=\s*(\[.*?\])", s, re.DOTALL)
            if not people_match:
                raise ValueError("People section not found.")
            people = ast.literal_eval(people_match.group(1))

            places_match = re.search(r"places\s*=\s*(\[.*?\])", s, re.DOTALL)
            if not places_match:
                raise ValueError("Places section not found.")
            places = ast.literal_eval(places_match.group(1))

            if not isinstance(people, list) or not isinstance(places, list):
                raise ValueError("People or places is not a list.")

            return narrative, people, places

        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Error parsing input: {e}")

def parse_api_response_just_narrative(s):
    if s[:10]!='narrative=':
        raise ValueError(f"Error parsing input: {e}")
    
    return s[10::]

        


def parse_api_response_vdp_questions(s):
    parsed_results = {}
    mapping_keys_ordered = list(question_list.vpd_mapping.keys())
    try:
        response_items = s.strip().split() # Split by space
    except:
        for key in mapping_keys_ordered:
            parsed_results[key] = 0
            print(f"Warning: Could not parse the LLM response to VDP questions.")
    

    for i, item in enumerate(response_items):
        if ';' in item:
            q_id, value = item.split(';')
            try:
                q_number = int(q_id.replace('q_', ''))
                if q_number-1 == i:
                    corresponding_key = mapping_keys_ordered[i]
                    parsed_results[corresponding_key] = int(value)
                else:
                    corresponding_key = mapping_keys_ordered[i]
                    parsed_results[corresponding_key] = 0
                    print(f"Warning: Question ID {q_id} out of range for mapping dictionary.")
            except ValueError:
                corresponding_key = mapping_keys_ordered[i]
                parsed_results[corresponding_key] = 0
                
                print(f"Warning: Could not parse question ID or value from '{item}'.")
    return parsed_results
