import pandas as pd
import json
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import numpy as np
import pickle
import os
from openai import OpenAI
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
from utils import parsing_responses
from utils import random_generators
from utils import question_list
from utils.regex_find_entitites import regex_find_people_locations



characted_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 18, 18, 20, 24, 27, 29, 30, 31, 32, 33, 34, 37, 37, 38, 38, 38, 39, 41, 41, 42, 46, 50, 50, 51, 51, 55, 55, 56, 57, 58, 60, 61, 68, 71, 71, 72, 75, 79, 81, 81, 82, 82, 83, 83, 84, 85, 85, 86, 88, 89, 90, 94, 94, 94, 95, 96, 96, 96, 97, 100, 101, 104, 104, 106, 106, 107, 112, 112, 112, 115, 116, 116, 117, 118, 118, 121, 123, 123, 125, 126, 127, 128, 132, 137, 137, 138, 146, 149, 152, 155, 160, 163, 166, 172, 172, 175, 176, 184, 186, 186, 193, 197, 212, 213, 213, 217, 219, 230, 232, 244, 252, 271, 292, 314, 317, 437, 466]

def sample_characters():
    return random.choice(characted_count)

# based on the preliminary tests
values_names_ent = [0, 1, 2, 3]
weights_names_ent = [0.620253164556962, 0.3291139240506329, 0.046413502109704644, 0.004219409282700422]
values_people_ent = [0, 1, 2, 3, 4]
weights_people_ent = [0.6329113924050633, 0.28270042194092826, 0.07172995780590717, 0.008438818565400843, 0.004219409282700422]
values_address_ent = [0, 1, 2, 3, 4]
weights_address_ent = [0.8354430379746836, 0.1350210970464135, 0.016877637130801686, 0.008438818565400843, 0.004219409282700422]
values_location_ent = [0, 1, 2]
weights_location_ent = [0.9578059071729957, 0.0379746835443038, 0.004219409282700422]


class GenerateInitialDF_VP():
    def __init__(self, misperid):
        load_dotenv()
        self.misperid = str(misperid)
        self.mp_df = self.load_mp_data()
        with open(f"../data/{misperid}/initial.json", 'r') as f:
             self.person = json.load(f)
             
        self.dir_path = Path(f"../data/{misperid}/processed/vpd")
        self.dir_path.mkdir(parents=False, exist_ok=True)
        
        self.client =  OpenAI(api_key=os.getenv("OPEN_API_KEY"))
        
        
        
        # sample date from 2 years before
        first_mp_record_ts = int(self.mp_df.iloc[0]['missing_since'].timestamp())
        first_vp_record_min_ts = int(pd.to_datetime(self.mp_df.iloc[0]['missing_since'] - timedelta(days=365*2)).timestamp())
        random_timestamp = random.randint(first_vp_record_min_ts, first_mp_record_ts)
        
        print(random_timestamp)
        self.first_vp_record = datetime.fromtimestamp(random_timestamp)
        
        if int(self.mp_df.iloc[0]['age']) < 18:
            self.youthattitude_ask = True 
            self.parentsattitude_ask = True 
            self.vpd_childprotection = True
        else: 
            self.youthattitude_ask = None 
            self.parentsattitude_ask = None 
            self.vpd_childprotection = None
            self.maiden_name = True
        
        self.vpd_subjectvulnerable = 1
        self.vpd_chsno = None
        self.record_start_date = "28-Nov-2022 14:48:11.000Z[UTC]"
        
    def load_mp_data(self):


        pkl_path = f"../data/{self.misperid}/processed/dataframe.pkl"
        try:
            df = pd.read_pickle(pkl_path)
        except:
            raise ValueError(f"Circumstances don't exsist yet for {self.misperid}")
        return df
       
    def generate_vp_record(self):
        n = random.randint(2, 20)
        print(f"Generating {n} records.")
        
        entities = {}
        entities['people'] = set()
        entities['locations'] = set()
        
        
        # Generate vp records
        vp_data = []

        
        vp_created_on = self.first_vp_record
        
        incidentid = random_generators.generate_unique_id("incidentid", limit=10000, lowerlimit=1000) # first incident id
        upperlimit = 1000000
        repeated_victim = False
        repeated_perpetrator = False 
        for i in range(1, n+1):
                        
            # TODO: This is a quick fix, if neecessary think of a simpler approach. -- This is fixed later.
            try:
                incidentid = random_generators.generate_unique_id("incidentid", limit=upperlimit, lowerlimit=incidentid) # so that it is always higher than the last one
            except:
                upperlimit += 100
                incidentid = random_generators.generate_unique_id("incidentid", limit=upperlimit, lowerlimit=incidentid) # so that it is always higher than the last one
            
            gap_days = random.randint(1, 180)
            gap_min = random.randint(1, 24*60)
            print(gap_days)
            print(vp_created_on)
            vp_created_on  = vp_created_on + timedelta(days=gap_days, minutes=gap_min)
            print(vp_created_on)
                        
            with open(f"../data/{self.misperid}/connected_locations.txt", 'r', encoding='utf-8') as file:
                locations_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_location_ent, p=weights_location_ent)
                
                if sample_size > len(locations_all):
                    sample_size = random.randint(0, len(locations_all))
                landmarks = random.sample(locations_all, sample_size) 
            
            with open(f"../data/{self.misperid}/connected_addresses.txt", 'r', encoding='utf-8') as file:
                locations_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_address_ent, p=weights_address_ent)
                
                if sample_size > len(locations_all):
                    sample_size = random.randint(0, len(locations_all))
                addresses = random.sample(locations_all, sample_size)  

            with open(f"../data/{self.misperid}/location_patterns.txt", 'r', encoding='utf-8') as file:
                locations_type_all = [line.strip() for line in file if line.strip()]
                max_sample_size = random.randint(0, min(len(locations_type_all), 3))
                location_types = random.sample(locations_type_all, max_sample_size) # Maximum 1 loc theme per report

            with open(f"../data/{self.misperid}/patterns.txt", 'r', encoding='utf-8') as file:
                pattern_types_all = [line.strip() for line in file if line.strip()]
                max_sample_size = random.randint(0, min(len(pattern_types_all), 1))
                pattern_types = random.sample(pattern_types_all, max_sample_size) # Maximum 1 patterns per report

            with open(f"../data/{self.misperid}/connected_people_desc.txt", 'r', encoding='utf-8') as file:
                connected_people_desc_all = [line.strip() for line in file if line.strip()]
                sample_size = np.random.choice(values_people_ent, p=weights_people_ent)
                if sample_size > len(connected_people_desc_all):
                    sample_size = random.randint(0, len(connected_people_desc_all))
                people_desc = random.sample(connected_people_desc_all, sample_size)
                        # complex mech. for names basically choose which list to sample from
            
            with open(f"../data/{self.misperid}/connected_people_names.txt", 'r', encoding='utf-8') as file:
                connected_people_names_all = [line.strip() for line in file if line.strip()]
            with open(f"../data/{self.misperid}/connected_people_relat.txt", 'r', encoding='utf-8') as file:
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
            
            if random.random() < 0.05:
                repeated_victim = True  # 5% chance turned repeated victim -- then stay like that
            
            if random.random() < 0.05:
                repeated_perpetrator = True
            if vp_created_on > datetime.now():
                break

            try:
                last_updated_on = vp_created_on + timedelta(minutes=int(np.clip(np.random.normal(3 * 60, 6000), 0, 2 * 24 * 60)))  # sample from gaussian with mean at 3h 
            except:
                last_updated_on = 0
                
            
            # consent name
            consent_names = [self.person['forenames'] + ' ' +self.person['surname']] + self.person['people_reporting']
            l = len(consent_names) - 1
            
            weights = [0.5] + [0.5/l]*l
            consent_name = random.choices(consent_names, weights=weights, k=1)[0]
    
            no_consent_reason = ""
            if consent_name != self.person['forenames'] + ' ' + self.person['surname']:
                no_consent_reason= random.choices(['No consent was given for information to be shared.', 'Unable to locate', 'Would not engage with police', ''], weights=[0.2, 0.2, 0.2, 0.4], k=1)[0]
            
            # attitude
            youthattitude = ""
            parentattitude = ""
            if self.person['age'] < 18:
                prompt = f'''You are asked to create a fake record for a vulnerable person. Given the following details, in maximum 100 characters state could be the attitude of the young person towards Police.
                            For example,
                            `[Name] did not appear bothered by the charge` or `Violent` or `No issues.
                            Keep the response short, make sure it is below 100 characters long.
                            Details:
                            Name: { self.person['forenames']}
                            Repeated victim: {repeated_victim}
                            Repeated perpetrator: {repeated_perpetrator}
                            Was the consent given for input the database: {"Yes" if no_consent_reason=='' else "No" + '-' + no_consent_reason}
                        '''
                youthattitude = self.ask_open_ai(prompt,50).split('.', 1)[0] + '.' # SAVE ONLY UNTIL FIRST SENTENCEs
                
                
                prompt = f'''
                Given that this was the youth attitude towards engagement with police {youthattitude}, state what could have been the parents attitude. Do not repeat the information from the youth attitude. Keep the language very fatual.
                
                '''
                parentattitude = self.ask_open_ai(prompt, 50).split('.', 1)[0] + '.'
                # raise NameError(youthattitude)
            
            
            # Nominals View
            prompt = f'''You are asked to create a fake record for a vulnerable person. Given the following details, in maximum 10 words state could be the view of the person regarding the situation. For example,
                            `[Name] deemed not to have capacity to fully understand due to dementia.` or `None` or `[Name] satisfied with police forwarding details'.
                            Keep the language very factual, do not repeat the information below.
                            Keep the response  below 100 characters long.
                            Details:
                            Name: { self.person['forenames']}
                            Repeated victim: {repeated_victim}
                            Repeated perpetrator: {repeated_perpetrator}
                            Was the consent given for input the database: {"Yes" if no_consent_reason=='' else "No" + '-' + no_consent_reason}
                            {"Disability: " + self.person['disability_desc'] if self.person['disability_desc']!="" else ""}'''
            nominalsview = self.ask_open_ai(prompt, 50).split('.', 1)[0] + '.'

            
            
            # Wellbeing Comment
            prompt = f'''You are asked to create a fake record for a vulnerable person. Given the following details, in maximum 10 words come up with a wellbeing comment for the individual. For example,
                            `[Name] is safe and well in the care of the school.` or `has been involved in criminal activity and has committed a crime.` or `[Name]has frequent panic attacks'.
                            Keep the language very factual, do not repeat the information below.
                            Keep the response  below 100 characters long.
                            Details:
                            Name: { self.person['forenames']}
                            Age: { self.person['age']}
                            Repeated victim: {repeated_victim}
                            Repeated perpetrator: {repeated_perpetrator}
                            Was the consent given for input the database: {"Yes" if no_consent_reason=='' else "No" + '-' + no_consent_reason}
                            {"Disability: " + self.person['disability_desc'] if self.person['disability_desc']!="" else ""}'''
            wellbeing_commment = self.ask_open_ai(prompt, 50).split('.', 1)[0] + '.'
            

            missing_record = False
            if random.random() < 0.1:
                missing_record = True
            
            
            GENERATE_ENTITIES = False
            char_no = random.choice(characted_count)
            
            prompt = f'''
                You are an assistant that helps with generating fake vulnerable person reports.
                1. Based on the information provided, generate a short narrative (approximately {char_no} characters) describing why the report has been created. 
                    The description should include:
                {f"- SOME of the following people that are connected to the person (these people are not the main character): {people_in};" if people_in else ""}
                {f"- ALL of the following location type(s): {location_types};" if location_types else ""}{f" with SOME of the specific locations mentioned: {location_types};" if location_types and locations_in else f"- The specific locations mentioned: {locations_in};" if locations_in else ""}
                {f"- ALL of the following behavioral pattern(s): {pattern_types};" if pattern_types else ""}
            
                
                For example,
                location types: not specified
                locations: not specified
                people: not specified
                patterns: self harm
                
                then an example response might be:

                narrative=[Name] was feeling low and self harmed.
                
                or 
                
                Second example - if  
                location types: schools
                locations:  Castleview
                people: friend
                patterns: getting confused
                
                then an example response might be:

                narrative=[Name] left his home after speaking on a phone with a friend and walked into  primary school near Castleview in a confused state'.
                
                
                Note: 
                Keep the language very factual, do not repeat the information below.                
                Make sure this is {"not a" if not missing_record else ""} a missing person record.
                Make sure the length of your response is approximately {char_no} characters long.
                
                Output the narrative without any additional text, just like:
                narrative=...
                
                Replace the '...' with the relevant output.
                
                        
                Details:
                Name: { self.person['forenames']}
                Age: { self.person['age']}
                Repeated victim: {repeated_victim}
                Repeated perpetrator: {repeated_perpetrator}
                Wellbeing commment: {wellbeing_commment}
                Was the consent given for input the database: {"Yes" if no_consent_reason=='' else "No" + '-' + no_consent_reason}
                {"Disability: " + self.person['disability_desc'] if self.person['disability_desc']!="" else ""}'''

           
            # try generation max 5 times
            nominal_synopsis = ""
            landmarks_used_str = ""
            entities_addresses_str = ""
            entities_location_str = ""
            entities_people_names_str = ""
            entities_people_desc_str = ""
            entities_people_relat_str = ""
            entities_pattern_types_str =""
            
            if char_no == 0:
                nominal_synopsis = ""
            else:
                for attempt in range(1, 5):
                    try:
                        print(f"Attempt {attempt}")
                        if GENERATE_ENTITIES:
                            nominal_synopsis, people, places = parsing_responses.parse_api_response_narrative_people_places(self.ask_open_ai(prompt, 250, "gpt-4o"))
                            people.append(consent_name)
                        else:
                            output = self.ask_open_ai(prompt, int(char_no//2), "gpt-4o")  # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
                            
                            
                            nominal_synopsis = parsing_responses.parse_api_response_just_narrative(output)
                            
                            print("IN:", nominal_synopsis, people_names, people_desc, people_relat, landmarks, addresses)
                            people_names_used, people_desc_used, people_relat_used, landmarks_used, addresses_used, location_types_used = regex_find_people_locations(nominal_synopsis, people_names, people_desc, people_relat, landmarks, addresses, location_types)
                            print("OUT:",  people_names_used, people_desc_used, people_relat_used, landmarks_used, addresses_used, location_types_used)
                            landmarks_used_str = ','.join(landmarks_used)
                            entities_addresses_str = ','.join(addresses_used)
                            entities_location_str = ','.join(location_types_used)
                            entities_people_names_str = ','.join(people_names_used)
                            entities_people_desc_str = ','.join(people_desc_used)
                            entities_people_relat_str = ','.join(people_relat_used)
                            entities_pattern_types_str = ','.join(pattern_types)
                            
                            
                            # print(output)
                        break
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {e}")
                        if attempt < 5:
                            print(f"Retrying...")
                        else:
                            print(f"All 5 attempts failed. Raising the last error.")
                            raise ValueError("couldn't parse")
            
    
            prompt = f''' 
    
            1. Based on the information regarding a missing person case below, answer the following 25 questions. Please answer 1 if the answer is "yes" and 0 if the answer in "no".
            
            Question list:
            {question_list.vpd_mapping.values()}
            
            
            2. Output the answers in the following format:
            q_(question_number);(boolean answer)
            Do not add any other text. Just start from q_1 and finish on line starting with q_42. Do not add any extra interpunction or lines.
            
            The information regarding the case:

            Name: {self.person['forenames']}
            Age: {self.person['age']}
            Repeated victim: {repeated_victim}
            Repeated perpetrator: {repeated_perpetrator}
            Wellbeing commment: {wellbeing_commment}
            Description of the incident: {nominal_synopsis}
            Was the consent given for input the database: {"Yes" if no_consent_reason=='' else "No" + '-' + no_consent_reason}
            {"Disability: " + self.person['disability_desc'] if self.person['disability_desc']!="" else ""}    

            '''
            
            questions_answers = self.ask_open_ai(prompt, 300)
            
            questions_answers_parsed = parsing_responses.parse_api_response_vdp_questions(questions_answers)
            # raise NameError(questions_answers_parsed)
    
            record = {
                "VPD_NOMINALINCIDENTID_PK": 30000 + int(str(self.person['nominalid']) + str(self.person['misperid']) + str(i)),
                "VPD_CONSENTNAME": consent_name,
                "VPD_NOCONSENTREASON": no_consent_reason,
                "VPD_CREATEDON": vp_created_on,
                "VPD_LASTUPDATEDON": last_updated_on,
                "VPD_NOMINALSYNOPSIS": nominal_synopsis,
                "VPD_GPCONSENT": random.choice([1,2,4,100]),
                "VPD_VPTYPEID_FK": 1,
                "VPD_INCIDENTID_FK": incidentid,
                "VPD_WELLBEINGCOMMENTS": wellbeing_commment,
                "VPD_NOTINFORMEDREASON": no_consent_reason,
                "VPD_NOGPCONSENTREASON": no_consent_reason,
                "VPD_SCRA": 100,
                "VPD_THREEPOINTTEST": random.choice([1,2]),
                "VPD_YOUTHATTITUDE": youthattitude,
                "VPD_PARENTATTITUDE": parentattitude,
                "VPD_NOMINALSVIEW": nominalsview,
                "VPD_CHILDPROTECTION": None if self.person['age']>=18 else self.person['child_protection'] if self.person['child_protection'] else None,
                "VPD_RECORD_START_DATE": self.record_start_date,
                "VPD_FORENAME": self.person['forenames'],
                "VPD_SURNAME":  self.person['surname'],
                "VPD_MAIDEN_NAME": self.person['maidenname'],
                "VPD_CREATEDON_1": self.first_vp_record,
                "VPD_PLACEOFBIRTH": self.person['place_of_birth'],
                "VPD_PERSONLANGUAGE": self.person['person_language'],
                "VPD_INTERPRETERREQID_FK": 1,
                "VPD_DISABILITY": self.person['disability_status'],
                "VPD_DISABILITYDESC": self.person['disability_desc'],
                "VPD_PERSONETHNICAPPEARANCE": self.person['ethnical_appearance'],
                "VPD_PERSONGENDER": self.person['sex'],
                "VPD_KNOWNAS": self.person['nickname'] if self.person['nickname'] else "",
                "VPD_REPEATVICTIM": "N" if not repeated_victim else "Y",
                "VPD_REPEATPERPETRATOR": "N" if not repeated_perpetrator else "Y",
                "misper_misperid": self.person['misperid'],
                'entities_landmarks': landmarks_used_str,
                'entities_addresses': entities_addresses_str,
                'entities_location_types': entities_location_str,
                'entities_people_names': entities_people_names_str,
                'entities_people_desc': entities_people_desc_str,
                'entities_people_relat':  entities_people_relat_str,
                'entities_pattern_types': entities_pattern_types_str,
            
            }
            
            
            for key in questions_answers_parsed.keys():
                record[key] = questions_answers_parsed[key]
            
            vp_data.append(record)
            
        df =  pd.DataFrame(vp_data)
    
        pickle_path = os.path.join(self.dir_path, "vpd_full_data.pkl")
        df.to_pickle(pickle_path)
    

        csv_path_vul_full_data = os.path.join(self.dir_path, "vpd_full_data.csv")
        df.to_csv(csv_path_vul_full_data)
            
            
            
            
        return df

    def print_all_attributes(self):
        """
        Prints all attributes (instance variables) of the object.
        """
        print(f"--- Attributes for misperid: {self.misperid} ---")
        for attr, value in vars(self).items():
            # Exclude the DataFrame itself for cleaner output, unless specifically needed
            if attr == 'mp_df':
                print(f"  {attr}: <Pandas DataFrame>")
            else:
                print(f"  {attr}: {value}")
        print("---------------------------------------")
    
    def ask_open_ai(self, prompt, maxtokens, model="gpt-4o-mini"):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=maxtokens        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
            
# test
# if __name__ == "__main__":
#     # client =  OpenAI(api_key=os.getenv("OPEN_API_KEY"))
#     g = GenerateInitialDF_VP(9585)
#     df = g.generate_vp_record()