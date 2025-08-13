import pandas as pd
import json
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import numpy as np
from dateutil.relativedelta import relativedelta
from utils import random_generators

class GenerateInitialDF:
    def __init__(self, misperid, initial_json_path):
        with open(initial_json_path, 'r') as f:
            self.person = json.load(f)

        self.misperid = misperid
        self.dir_path = Path(f"../data/{misperid}/processed")
        self.dir_path.mkdir(parents=False, exist_ok=True)
    
    
    def generate_missing_record(self):        
        person = self.person
        n = random.randint(5, 50)
        start_date = datetime.strptime(person["reports_starting_from"], "%Y-%m-%d")

        # Make home adress 10 times as likely as the other assosiated adresses
        associated_address_pool = (
            [addr for addr in person["addresses"] if addr["type"] in ("Home","home")] * len(person["addresses"]) * 10 +
            [addr for addr in person["addresses"] if addr["type"] not in ("Home","home")]
        )
        
        home_adress = ''
        for addr in person["addresses"]:
            if addr["type"] == "home":
                home_adress = addr
                break

        # Create weighted traced location pool if it exists
        traced_locations = person.get("traced_locations", [])
        weighted_traced_locations = []
        if traced_locations:
            weighted_traced_locations = (
                [traced_locations[0]] * 5 +
                traced_locations[1:4] * 3 +
                traced_locations[4:]
            )
        people_reporting = person['people_reporting']
    
        return_methods_desc = ['Traced by family', 'Traced by member of the public',  'Traced by staff'] + 6*['Traced by Police']
        
        # Generate missing records
        missing_data = []
        used_assosiated_addresses = set()
        used_tl_addresses = set()
        current_time = start_date

        print(f"Starting, {n+1}")
        for i in range(1, n+1):
            gap_days = random.randint(1, 180)
            missing_since = current_time + timedelta(days=gap_days)
            
            # print("missing_since", missing_since)
            if missing_since > datetime.now():
                print(f"Stopping at {i}")
                break
            length_missing_mins = random.randint(60, 10080)
            # print("length_missing_mins", length_missing_mins)
            try:
                report_delay = timedelta(hours=int(np.clip(np.random.normal(14.4, 11), 0,  min(72,length_missing_mins// 60 -5))))
            except:
                report_delay = 0
            # print("report_delay", report_delay)
            reported_missing = missing_since + report_delay
            # print("reported_missing", reported_missing)
            when_traced = missing_since + timedelta(minutes=length_missing_mins)
            # print("when_traced", when_traced)
            
            # if i == 3:
            #     return
            
            selected_reported_missing_by = random.choice(people_reporting)
            
            sample_initial_risk_level = random.choice(['High', 'Medium', 'Low'])
            current_final_risk_level = random.choice([sample_initial_risk_level]*9 + ['Medium', 'High', 'Low'])

            selected_address = random.choice(associated_address_pool)
            used_assosiated_addresses.add(selected_address["address"])
            tl_adress = random.choice(weighted_traced_locations)
            
            record = {
                "reportid": random_generators.generate_unique_id("reportid", limit=100000),
                "misperid": self.misperid,
                "initial_risk_level": sample_initial_risk_level,
                "current_final_risk_level": current_final_risk_level, 
                "forenames": person['forenames'],
                "surname": person['surname'],
                "dob": person['date_of_birth'],
                "pob": person['place_of_birth'],
                "age": str(relativedelta(missing_since, datetime.strptime(person['date_of_birth'], '%Y-%m-%d')).years),
                "sex": "F" if person['sex']=="Female" else "Male",
                "residence_type": "Home Address", # TODO: Maybe change if need for different addresses
                "occdesc": person["occupation"],
                "nominalpersionid": person['nominalid'],
                "missing_since": missing_since,
                "date_reported_missing": reported_missing,
                "day_reported_missing": reported_missing.strftime("%A"),
                "length_missing_mins": length_missing_mins,
                "when_traced": when_traced,
                "mf_address": selected_address["address"],
                "missing_from": selected_address["type"],
                "reported_missing_by": selected_reported_missing_by,
                "TL_address": tl_adress,
            }
            print(record["age"])
            used_tl_addresses.add(tl_adress)
            
            if tl_adress == home_adress:
                record["return_method_desc"] = selected_address["Returned of own accord"]
            else:
                record["return_method_desc"] = random.choice(return_methods_desc)
            
            
            missing_data.append(record)
            current_time = missing_since + timedelta(minutes=length_missing_mins)

        person["addresses"] = [
            addr for addr in person["addresses"] if addr["address"] in used_assosiated_addresses
        ]
        
        person["traced_locations"] = [
            addr for addr in person["traced_locations"] if addr in used_tl_addresses
        ]

        return pd.DataFrame(missing_data)
    
    
    def generate_missing_records(self):
        with open(f'{self.dir_path}/adresses.txt', "w") as f:
            addresses = self.person["traced_locations"]
            [f.write(a + '\n') for a in addresses]

        df = self.generate_missing_record()        
        df.to_pickle(f'{self.dir_path}/dataframe.pkl') 
        
        with open(f'{self.dir_path}/dataframe.json', "w") as f:
            json_data = df.astype(str).to_json(orient='records', indent=2)
            f.write(json_data)
        
        
        with open(f'{self.dir_path}/serialized.txt', "w")as f:
            [f.write(s) for s in self.serialize_for_llm(df)]
                
            
    def serialize_for_llm(self, df):
        serialized_prompts = []
        n = 1
        for _, row in df.iterrows():
            prompt=(
                f"Disappearance Record:\n"
                f"Report number: {row['reportid']}\n"
                f"Name: {row['forenames']} {row['surname']}\n"
                f"Date of Birth: {row['dob']}\n"
                f"Sex: {row['sex']}\n"
                f"Place of Birth: {row['pob']}\n"
                f"Occupation: {row['occdesc']}\n"
                f"Missing Since: {row['missing_since']}\n"
                f"Date Reported Missing: {row['date_reported_missing']}\n"
                f"Day Reported Missing: {row['day_reported_missing']}\n"
                f"Length Missing (minutes): {row['length_missing_mins']}\n"
                f"When Traced: {row['when_traced']}\n"
                f"Missing From Address: {row['mf_address']} ({row['missing_from']})\n"
                f"Traced at Address: {row['TL_address']}\n"
                f"Traced by: {row['return_method_desc']}\n\n")
        
            serialized_prompts.append(prompt)
            n+=1
        return serialized_prompts
        

if __name__ == "__main__":
    misperid = 7738
    g = GenerateInitialDF(misperid, f"data/{misperid}/initial.json")
    g.generate_missing_records()
    
    