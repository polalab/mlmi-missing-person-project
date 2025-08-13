

import pandas as pd
import pickle
import utils
import numpy as np
from utils.serialize import serialize_for_llm, serialize_row
from utils.question_list import vul_questions
from utils.parsing_responses import parse_api_response_just_narrative
from utils.regex_find_entitites import regex_find_people_locations
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import ast
import re
import random


word_count =[ 5, 6, 10, 12, 12, 12, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 28, 28, 28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 31, 31, 32, 32, 32, 32, 32, 32, 32, 32, 33, 33, 33, 33, 33, 33, 33, 33, 34, 34, 34, 34, 35, 35, 35, 35, 35, 35, 36, 36, 36, 36, 36, 36, 37, 37, 37, 37, 37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 39, 39, 39, 40, 40, 40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 41, 42, 42, 43, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 45, 45, 45, 45, 45, 45, 45, 45, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 48, 49, 49, 49, 50, 50, 50, 51, 51, 51, 51, 52, 52, 52, 53, 53, 53, 55, 55, 55, 57, 58, 59, 59, 63, 63, 64, 64, 64, 64, 65, 65, 65, 65, 66, 66, 66, 67, 67, 67, 67, 68, 68, 68, 69, 69, 69, 70, 70, 70, 71, 71, 71, 72, 72, 72, 72, 72, 73, 73, 73, 73, 74, 74, 75, 75, 75, 75, 75, 75, 76, 76, 76, 76, 76, 78, 78, 78, 79, 79, 79, 80, 80, 80, 80, 81, 81, 81, 82, 82, 82, 83, 83, 84, 84, 84, 85, 85, 85, 86, 86, 86, 86, 87, 87, 88, 88, 88, 88, 89, 89, 89, 89, 89, 90, 90, 91, 91, 92, 92, 92, 93, 93, 93, 94, 94, 94, 94, 94, 95, 97, 98, 98, 98, 99, 99, 99, 99, 101, 101, 102, 103, 103, 104, 104, 105, 105, 106, 106, 106, 106, 106, 106, 107, 107, 107, 107, 108, 108, 108, 108, 108, 109, 109, 109, 109, 109, 109, 110, 110, 110, 110, 110, 110, 110, 111, 111, 111, 111, 111, 111, 111, 111, 112, 112, 112, 112, 112, 112, 112, 112, 112, 112, 113, 113, 113, 113, 113, 113, 113, 113, 113, 113, 114, 114, 114, 114, 114, 114, 114, 114, 114, 115, 115, 115, 115, 115, 115, 115, 115, 115, 116, 116, 116, 116, 116, 116, 116, 116, 116, 116, 116, 116, 117, 117, 117, 117, 117, 117, 117, 117, 117, 117, 117, 117, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 118, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 122, 123, 123, 123, 123, 123, 123, 123, 124, 124, 124, 124, 124, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 126, 126, 126, 126, 126, 126, 126, 126, 126, 126, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 128, 128, 128, 128, 128, 128, 128, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 130, 130, 130, 130, 130, 131, 131, 131, 131, 131, 131, 131, 132, 132, 132, 132, 133, 133, 133, 134, 134, 134, 134, 134, 134, 134, 135, 135, 135, 135, 136, 137, 137, 137, 138, 138, 138, 138, 138, 139, 139, 139, 139, 139, 140, 141, 141, 142, 143, 147, 147]


# based on the preliminary tests
values_names_ent = [0, 1, 2, 3, 4]
weights_names_ent = [0.25, 0.4, 0.15, 0.1, 0.1]

values_people_ent = [0, 1, 2, 3, 4, 5, 6, 7]
weights_people_ent = [0.05, 0.25, 0.25, 0.2, 0.1, 0.08, 0.05, 0.02] 
values_address_ent = [0, 1, 2, 3, 4, 5, 6]
weights_address_ent = [0.1, 0.05, 0.35, 0.3, 0.1, 0.05, 0.05]
values_location_ent = [0, 1, 2, 3]
weights_location_ent = [0.4, 0.35, 0.15, 0.1]



def sample_characters():
    return random.choice(word_count) * 6

def create_prompt(locations,location_types, pattern_types, people, extract_entities, characters_no):

    prompt = f'''
    You are an assistant that helps with generating fake past missing person cases. You are a past record for a given individual. 

    1. Based on the information provided, generate a short narrative (approximately {characters_no} characters) describing the circumstances surrounding a past missing person incident. Make sure the incident is plausible given the record.
    The description should include:
        {f"- SOME of the following people that are connected to the missing person (these people are not the main character): {people};" if people else ""}
        {f"- ALL of the following location type(s): {location_types};" if location_types else ""}{f" with SOME of the specific locations mentioned: {locations};" if location_types and locations else f"- The specific locations mentioned: {locations};" if locations else ""}
        {f"- ALL of the following behavioral pattern(s): {pattern_types};" if pattern_types else ""}
    
    All of the people and locations must come from the lists provided.
    
    Keep the language as factual as possible. Focus on the possible circumstances and do not mention all the information provided in the text file. 
    Do not mention the time of the year or refer to dates. Focus just on the reasons the person went missing or simply report what happened during the disappearance. 
    Do not mention the provided information from the record explicitly. For example do not mention the occupation of the person. 
    Refer to the person as MP or by the name. 

    For example, if  
    location types: water
    locations: Edward Street, Kilsyth, footbridge
    people: Zoe, friend, father
    patterns: goes to water areas  
    
    then an example response might be:
    
    MP was last seen near the footbridge at the end of Edward Street, Kilsyth. After speaking with a friend by phone, MP’s father arrived at the location and found MP sitting on the wrong side of the bridge barriers. 
    While approaching, MP slipped from the bridge support and fell approximately 20–25 feet onto the embankment below. 
    Emergency services were called, and MP was rescued with minor injuries.
    
    
    Make sure the length of your response is approximately {characters_no} characters long.
    {
    """
    2. Then, extract named entities, specifically: - People (excluding the missing person - just include others mentioned) - Places (such as cities, landmarks, streets, buildings, addresses) just from the generated narrative for a given record and not from the given details. 

    3. Output the created circumstances people = ["Person1", "Person2"] places = ["Place1", "Place2"] For example: people = ["Iain Ferguson", "family members", "father"] places = ["Edward Street", "Kilsyth", "Monklands"]

    Output the narrative without any additional text just 
    narrative=...
    people=[...]
    places=[...]
    Replace the '...' with the relevant output. Do not introduce any more brackets. The lists should be provided in square brackets as per example. And separated by new lines."""
    
    if extract_entities else
    
    """2. Output the narrative without any additional text just 
    narrative=...
    
    Replace the '...' with the relevant output. Do not introduce any more brackets.
    
    """
    }
    The record: '''
    return prompt



def create_question_prompt():
    prompt = f''' 
    
    1. Based on the information regarding a missing person case below, answer the following 25 questions. Please answer 1 if the answer is "yes" and 0 if the answer in "no".
    
    Question list:
    {vul_questions}
    
    2. If the answer was 1("yes"), give a possible (up to 100 characters) explanation regarding this choice. For example, for a different case answer to question 3 was yes and the explanation was: "Although MP is wise, he is vulnerable due to being 14 years of age." 
    
    3. Output the answers in the following format:
    q_(question_number);(boolean answer);(explanation or NULL) 
    Do not add any other text. Just start from q_1 and finish on line starting with q_25. Do not add any extra interpunction or lines.
    
    The information regarding the case:
    
    '''
    
    return prompt

fake_responses = {
    0: "narrative= Harold Williams, a retired teacher from Glasgow, was known for his daily morning walks which he would often start from his home on Great Western Road. He would follow a familiar route through the nearby Kelvingrove Park, pausing occasionally to feed the ducks. On one such morning, however, Harold did not return home as expected. Relatives became concerned when he missed a scheduled family lunch. It was later discovered he had been seen conversing with a woman named Sheila Brooks outside a caf\u00e9 on Byres Road. Witnesses say he seemed disoriented, suggesting he might have taken a wrong path. Eventually, Harold was found safe inside a bookshop at the other end of Great Western Road, engrossed in a novel he'd happened upon. He was puzzled by the commotion his absence had caused.\n\npeople= [\"Sheila Brooks\", \"relatives\", \"witnesses\"]\nplaces= [\"Great Western Road\", \"Kelvingrove Park\", \"Byres Road\", \"bookshop\"]",
    1: "narrative= Harold Williams, a retired teacher, was last seen leaving his home on Great Western Road. He had mentioned plans to visit an old friend, Margaret Dunlop, who lived near Kelvingrove Park. Witnesses recalled seeing Harold boarding a bus headed towards the city center. Concern grew when Margaret revealed that Harold never arrived at her residence. A local shopkeeper, Tom Reid, reported seeing a man matching Harold's description wandering near the Buchanan Bus Station, appearing confused. Police initiated a search, eventually locating him near the entrance of Glasgow University. Harold, who seemed disoriented, explained he lost track while reminiscing about his teaching days at the university. Officers ensured his safe return home.\n\npeople= [\"Margaret Dunlop\", \"Tom Reid\"]\nplaces= [\"Great Western Road\", \"Kelvingrove Park\", \"Buchanan Bus Station\", \"Glasgow University\"]",
    2: "narrative= Harold Williams was last seen leaving Mitchell Library, where he often spent his afternoons. Witnesses recall him chatting with an acquaintance, Mrs. Eleanor Black, before heading towards the nearby park. Concern arose when Harold failed to return home, as he usually called his neighbor, Mr. Kenneth Moore, if running late. A search team combed through the Kelvinbridge area, suspecting he might have taken a walk along the familiar river trail. Harold was found safe at a friend's flat on Clarence Drive, having lost track of time during an impromptu reunion with an old colleague, Douglas Reid, who lived there.\n\npeople= [\"Eleanor Black\", \"Kenneth Moore\", \"Douglas Reid\"]\nplaces= [\"Mitchell Library\", \"Kelvinbridge\", \"Clarence Drive\"]",
    3: "narrative = \"Harold Williams, a retired teacher from Glasgow, was last seen leaving his home on Great Western Road. Neighbors reported seeing him heading toward Kelvingrove Park. Harold often visited the park for morning walks, describing it as his peaceful retreat. Concern arose when a passerby, Mrs. Emily Thomson, found his satchel and favorite book on a bench near the park's flower garden. His daughter, Lucy Williams, launched a search, fearing he might have become disoriented. Police and community volunteers scoured the area until Harold was eventually found safe at a nearby caf\u00e9, The Willow Bistro, where staff recognized him and contacted his family.\"\n\npeople = [\"Mrs. Emily Thomson\", \"Lucy Williams\"]\nplaces = [\"Great Western Road\", \"Kelvingrove Park\", \"The Willow Bistro\"]",
    4: "narrative= Harold Williams was last seen leaving his residence on Great Western Road, expressing an interest in visiting an old friend, Margaret Thompson, who lived near the River Kelvin. Concerned about his sudden absence, his daughter Sarah contacted the local authorities after he failed to return home. Witnesses later reported seeing Harold near the Kelvin Walkway, looking disoriented. Meanwhile, James, a local shopkeeper, recalled a brief interaction where Harold mentioned searching for a forgotten memory. Realizing his direction, the police discovered Harold at Kelvin Hall, unharmed but slightly confused, reminiscing about his teaching days. The staff at Kelvin Hall assisted until his family arrived to take him home.\n\npeople= [\"Margaret Thompson\", \"Sarah\", \"James\"]\nplaces= [\"Great Western Road\", \"River Kelvin\", \"Kelvin Walkway\", \"Kelvin Hall\"]",
    5: "narrative= Harold Williams, a retired teacher from Glasgow, was last seen leaving his home on Great Western Road. Known for his daily routine, it was unusual when he didn\u2019t show up at the local library where he often spent his afternoons. His neighbor, Mrs. Thompson, grew concerned after noticing his garden gate left ajar, something Harold was meticulous about. After a thorough check of nearby locations, including Kelvin Park where he often walked, a tip from a fellow club member, Mr. Duffy, led authorities to the Western Baths Club. There, staff recalled seeing Harold earlier, seemingly lost in thought but unharmed. His sudden departure from familiar settings appeared to be a momentary lapse, with no harm intended.\n\npeople= [\"Mrs. Thompson\", \"Mr. Duffy\", \"staff\"]\nplaces= [\"Great Western Road\", \"Kelvin Park\", \"Western Baths Club\"]",
    6: "narrative= Harold Williams, a retired teacher, was last seen by neighbors leaving his home at 67 Great Western Road. Concern grew when he didn't return calls. During the investigation, it was discovered Harold had been visiting an old friend, Charles Dunbar, who lived at 156 Great Western Road, just a few blocks away. It turns out Harold had decided to stay overnight unexpectedly after a long evening of reminiscing. The next morning, Charles found him enjoying coffee in the garden, unaware that Harold's absence had sparked concern. Police traced him there, and the mystery was quickly resolved with a relieved sigh from family and neighbors.\n\npeople= [\"Charles Dunbar\", \"neighbors\", \"family\"]\nplaces= [\"Great Western Road\", \"Glasgow\"]"
  }

# response = client.responses.create(
#     model="gpt-4o",
#     input=f'{prompt} {serialized}'
# )

# print(response.output_text)

class FakeResponse:
    def __init__(self, i):
        self.output_text = fake_responses[i]
    
ENTITIES_EXTRACTION = False
    
class OpenAIGeneration:
    def __init__(self):
        load_dotenv()
        self.client =  OpenAI(api_key=os.getenv("OPEN_API_KEY"))
        self.prompt_questions = create_question_prompt()
    
    
            
    def generate_descriptions(self, df_file, misperid):
        with open(df_file, "rb") as f:
            df = pickle.load(f)
        f_errors = open("utils/errors.txt", "a")
        responses = []
        narratives = []
        
        vul_questions_df_list = []
        
        entities_landmarks = []
        entities_addresses = []
        entities_location_types = []
        entities_people_names = []
        entities_people_desc = []
        entities_people_relat = []
        entities_pattern_types = []
        
            
        for i, row in df.iterrows():
            serialized = serialize_row(row, misperid) 
            
            char_no =  sample_characters()
            
            with open(f"../data/{misperid}/connected_locations.txt", 'r', encoding='utf-8') as file:
                locations_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_location_ent, p=weights_location_ent)
                
                if sample_size > len(locations_all):
                    sample_size = random.randint(0, len(locations_all))
                landmarks = random.sample(locations_all, sample_size) 
            
            with open(f"../data/{misperid}/connected_addresses.txt", 'r', encoding='utf-8') as file:
                locations_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_address_ent, p=weights_address_ent)
                
                if sample_size > len(locations_all):
                    sample_size = random.randint(0, len(locations_all))
                addresses = random.sample(locations_all, sample_size)  
            
            with open(f"../data/{misperid}/location_patterns.txt", 'r', encoding='utf-8') as file:
                locations_type_all = [line.strip() for line in file if line.strip()]
                max_sample_size = random.randint(0, min(len(locations_type_all), 3))
                location_types = random.sample(locations_type_all, max_sample_size) # Maximum 2 themes per report
           
            with open(f"../data/{misperid}/patterns.txt", 'r', encoding='utf-8') as file:
                pattern_types_all = [line.strip() for line in file if line.strip()]
                max_sample_size = random.randint(0, min(len(pattern_types_all), 3))
                pattern_types = random.sample(pattern_types_all, max_sample_size) # Maximum 2 patterns per report
           
            with open(f"../data/{misperid}/connected_people_desc.txt", 'r', encoding='utf-8') as file:
                connected_people_desc_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_people_ent, p=weights_people_ent)
                if sample_size > len(connected_people_desc_all):
                    sample_size = random.randint(0, len(connected_people_desc_all))
                people_desc = random.sample(connected_people_desc_all, sample_size)
            
            
            # complex mech. for names basically choose which list to sample from
            
            with open(f"../data/{misperid}/connected_people_names.txt", 'r', encoding='utf-8') as file:
                connected_people_names_all = [line.strip() for line in file if line.strip()]
            with open(f"../data/{misperid}/connected_people_relat.txt", 'r', encoding='utf-8') as file:
                connected_people_relat_all = [line.strip() for line in file if line.strip()]
            
            people_sample_size = np.random.choice(values_names_ent, p=weights_names_ent)
            people_names = []
            people_relat = []
            for i in range(people_sample_size):
                if random.random() < 0.5 and len(connected_people_relat_all)>0:
                    relat_random = random.choice(connected_people_relat_all)
                    people_relat.append(relat_random)
                    connected_people_relat_all.remove(relat_random)
                elif len(connected_people_names_all)>0:
                    name_random = random.choice(connected_people_names_all)
                    people_names.append(name_random)
                    connected_people_names_all.remove(name_random)
                elif len(connected_people_relat_all)>0:
                    relat_random = random.choice(connected_people_relat_all)
                    people_relat.append(relat_random)
                    connected_people_relat_all.remove(relat_random)
                    
                    
            
            
            locations_in = landmarks + addresses
            people_in = people_desc + people_names + people_relat
            prompt = create_prompt(locations_in, location_types, pattern_types, people_in, ENTITIES_EXTRACTION, char_no)
            print("LISTS:", people_in,  locations_in, location_types, pattern_types)
            print("INDIV:", people_desc,people_names, people_relat,  landmarks, addresses, pattern_types)

            response = self.generate_description_make_api_call(prompt, serialized, i, char_no)
            print(response)
            # raise ValueError
            responses.append({
                "response": response
            })
            
            for attempt in range(1, 4):
                try: 
                    if ENTITIES_EXTRACTION:
                        pass
                        # narrative, people, places = self.parse_api_response(response)
                        # df.loc[i, 'entities_locations'] = df.at[i, 'entities_locations'].union(places)
                        # df.loc[i, 'entities_people'] = df.at[i, 'entities_people'].union(people)
                        # people_list.append(people)
                        # places_list.append(places) 
                    else:
                       
                        
                        narrative = parse_api_response_just_narrative(response)
                        # print("\n")
                        # print("LLL", people_names, people_desc, people_relat, landmarks, addresses)
                        # print("XXX", narrative)
                        # print("\n")
                        
                        print("IN:", narrative, people_names, people_desc, people_relat, landmarks, addresses)
                        people_names_used, people_desc_used, people_relat_used, landmarks_used, addresses_used, location_types_used = regex_find_people_locations(narrative, people_names, people_desc, people_relat, landmarks, addresses, location_types)
                        print("OUT:",  people_names_used, people_desc_used, people_relat_used, landmarks_used, addresses_used)
                        
                        landmarks_used_str = ','.join(landmarks_used)
                        entities_addresses_str = ','.join(addresses_used)
                        entities_location_str = ','.join(location_types_used)
                        entities_people_names_str = ','.join(people_names_used)
                        entities_people_desc_str = ','.join(people_desc_used)
                        entities_people_relat_str = ','.join(people_relat_used)
                        entities_pattern_types_str = ','.join(pattern_types)
                        
                        

                    break
                except Exception as e:
                    print(f"Attempt {attempt} failed: {e} for row {i}.")
                    f_errors.write(response)
                    narrative=''
                    landmarks_used_str = ''
                    entities_addresses_str = ''
                    entities_location_str = ''
                    entities_people_names_str = ''
                    entities_people_desc_str = ''
                    entities_people_relat_str = ''
                    entities_pattern_types_str = ''
                    
            
           
            
            question_responses = self.generate_vul_questions_api_call(serialized + f'\n Circumstances: {narrative}')
            questions_row = self.parse_api_response_vul_questions(question_responses)
            vul_questions_df_list.append(questions_row)
            narratives.append(narrative)
            
            entities_landmarks.append(landmarks_used_str)
            entities_addresses.append(entities_addresses_str)
            entities_location_types.append(entities_location_str)
            entities_people_names.append(entities_people_names_str)
            entities_people_desc.append(entities_people_desc_str)
            entities_people_relat.append(entities_people_relat_str)
            entities_pattern_types.append(entities_pattern_types_str)
                        
            
            
        df['circumstances'] = narratives
        
        df['entities_landmarks'] = entities_landmarks
        df['entities_addresses'] = entities_addresses
        df['entities_location_types'] = entities_location_types
        df['entities_people_names'] = entities_people_names
        df['entities_people_desc'] = entities_people_desc
        df['entities_people_relat'] = entities_people_relat
        df['entities_pattern_types'] = entities_pattern_types
        # print(entities_landmarks)
        # raise ValueError
       
        # df['entities_landmarks'] = ['; '.join(lst) for lst in entities_landmarks]
        # df['entities_addresses'] = ['; '.join(lst) for lst in entities_addresses]
        # df['entities_location_types'] = ['; '.join(lst) for lst in entities_location_types]
        # df['entities_people_names'] = ['; '.join(lst) for lst in entities_people_names]
        # df['entities_people_desc'] = ['; '.join(lst) for lst in entities_people_desc]
        # df['entities_people_relat'] = ['; '.join(lst) for lst in entities_people_relat]
        # df['entities_pattern_types'] = ['; '.join(lst) for lst in entities_pattern_types]


        
        
        vul_questions_df = pd.DataFrame(vul_questions_df_list)
        
        
        dir_path = os.path.join(os.path.dirname(df_file), "add_circumstances")
        os.makedirs(dir_path, exist_ok=True)
        json_path =  os.path.join(dir_path, "responses.json")
        
        with open(json_path, "w") as outfile:
            json.dump(responses, outfile, indent=2)
            
        
        pickle_path = os.path.join(dir_path, "dataframe_circumstances.pkl")
        df.to_pickle(pickle_path)
        
        csv_path = os.path.join(dir_path, "dataframe_circumstances.csv")
        df.to_csv(csv_path)
        f_errors.close()
        
        csv_path_vul_questions_only = os.path.join(dir_path, "dataframe_vul_questions_only.csv")
        vul_questions_df.to_csv(csv_path_vul_questions_only)
    
        mp_full_data = pd.concat([df, vul_questions_df], axis=1)
        pickle_path = os.path.join(dir_path, "mp_full_data.pkl")
        mp_full_data.to_pickle(pickle_path)
    

        csv_path_vul_full_data = os.path.join(dir_path, "mp_full_data.csv")
        mp_full_data.to_csv(csv_path_vul_full_data)
    
        
    def generate_description_make_api_call(self, prompt, serialized, i, max_tokens):

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f'{prompt} {serialized}'}
            ],
            max_tokens=max_tokens//2  # "1 token ~= 4 chars in English" from https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        )
        return response.choices[0].message.content
                
    
    def generate_description_make_api_call_fake(self, serialized, i):
        print("Using Fake of API.")
        return FakeResponse(i).output_text
    
    def generate_vul_questions_api_call(self, serialized):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a careful reasoning assistant who answers missing person risk questions."},
                {"role": "user", "content": f'{self.prompt_questions}{serialized}'}
            ]
        )
        return response.choices[0].message.content

    def parse_api_response(self, s):
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

    def parse_api_response_vul_questions(self, s):
        f = open("vul_qs.txt", 'a')
        f.write(s)
        f.close()
        row = {}

        for i, line in enumerate(s.strip().splitlines()):
            try:
                key, flag, value = line.strip().split(';', 2)
            except:
                print(f"Cannot split line {line}")
                continue
            if key.startswith('q_'):
                try:
                    row[key] = int(flag)
                    row[f"{key}_explanation"] = value
                except:
                    row[key] = 0
                    row[f"{key}_explanation"] = "NULL"
            if i == 24:
                break
        
        return pd.Series(row)

        
if __name__ == "__main__":
    id = 292
    # a = open(f"../data/{id}/processed/adresses.txt")
    # addresses = a.read()
    # print(addresses)
    o = OpenAIGeneration()
    
    
    o.generate_descriptions(f"../data/{id}/processed/dataframe.pkl" , id)
    