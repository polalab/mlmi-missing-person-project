import json
from faker import Faker
import random
from datetime import date, timedelta
import csv
import os
import re
from utils import random_generators
import utils.initial_generation_statistics as igs


fake = Faker('en_GB')

def get_postcode_area(postcode):
    """
    Extracts the postcode area
    """
    if postcode and isinstance(postcode, str):
        match = re.match(r'^([A-Z]{1,2})', postcode.strip().upper())
        if match:
            return match.group(1)
    return None

def load_addresses_from_csv(csv_filepath, type=None):
    addresses_data = []
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            building_type = row.get('building', '').strip().lower()
            if type:
                if building_type != type:
                    continue
        
            house_number = row.get('addr:housenumber', '').strip()
            street = row.get('addr:street', '').strip()
            city = row.get('addr:city', '').strip()
            postcode = row.get('addr:postcode', '').strip()
            full_address = f"{house_number if house_number else ''} {street}, {city +',' if city else ''} {postcode}"


            address_postcode_area = get_postcode_area(postcode)
            if address_postcode_area: # Only include addresses with a valid postcode area
                addresses_data.append({
                    "address": full_address.strip(', ').strip(),
                    "postcode_area": address_postcode_area
                })
    return addresses_data

def generate_person_data(num_records=1, address_csv_filepath='addresses2.csv'):
    all_person_data = []
    misperids_generated = []
    # Load all addresses from the CSV with their postcode areas
    all_available_addresses_data = load_addresses_from_csv(address_csv_filepath)
    if not all_available_addresses_data:
        print(f"Warning: No valid addresses with postcode areas found in {address_csv_filepath}. Addresses will not be generated.")
        return json.dumps([], indent=4)

    # Get all unique postcode areas from the loaded CSV addresses
    unique_postcode_areas = list(set(item['postcode_area'] for item in all_available_addresses_data))
    if not unique_postcode_areas:
        print("Error: No unique postcode areas found in the provided CSV addresses.")
        return json.dumps([], indent=4)

    for _ in range(num_records):
        # Select a random base postcode area for this person
        chosen_postcode_area = random.choice(unique_postcode_areas)

        # Filter all available addresses to only those matching the chosen postcode area
        filtered_addresses_for_person = [
            item for item in all_available_addresses_data
            if item['postcode_area'] == chosen_postcode_area
        ]

        if not filtered_addresses_for_person:
            print(f"Warning: No addresses found for postcode area {chosen_postcode_area}. Skipping address generation for this person.")
            person_addresses = []
        else:
            person_addresses = []

            sex = random.choice(["Male", "Female"])
            misperid = random_generators.generate_unique_id('misperid')
            misperids_generated.append(misperid)
            person_dir = os.path.join("../data", str(misperid)) # Create path: data/{misperid}
            os.makedirs(person_dir, exist_ok=True) # Create the misperid directory
            nominalid = random_generators.generate_unique_id('nominalid')
            
            first_name = fake.first_name_male() if sex == "Male" else fake.first_name_female()
            last_name = fake.last_name()
            ethnical_appearance = random.choices(igs.ethnic_groups, weights=igs.ethnic_group_weights, k=1)[0]

            chosen_group = random.choices(igs.age_groups, weights=igs.group_weights, k=1)[0]
            dob_date_obj = fake.date_of_birth(minimum_age=chosen_group["min_age"], maximum_age=chosen_group["max_age"])
            dob = dob_date_obj.strftime('%Y-%m-%d')
            today = date.today()
            age = today.year - dob_date_obj.year - ((today.month, today.day) < (dob_date_obj.month, dob_date_obj.day))
            maiden_name = "" if sex == "Male" or age <= 18 else (fake.last_name() if random.random() < igs.mainden_name_probability else "")

                
            place_of_birth = random.choice(igs.uk_cities)
            
            # Make dementia very probable with elderly group 
            if age >= igs.senior_age_threshold:
                disability_status = random.choices(igs.disability_statuses_dementia, weights=igs.disability_weights_dementia, k=1)[0]
            else:
                disability_status = random.choices(igs.disability_statuses, weights=igs.disability_weights, k=1)[0]


            # Sample Dates
            start_range_for_samples = max(dob_date_obj, today - timedelta(days=365 * (igs.start_range_for_samples_senior if age >= igs.senior_age_threshold else (igs.start_range_for_samples_youth if age < igs.youth_age_threshold_for_reports else igs.start_range_for_samples_other))))
            end_range_for_samples = today - timedelta(days=1)
            if start_range_for_samples > end_range_for_samples:
                start_range_for_samples = end_range_for_samples
            start_records_date_obj = fake.date_between(start_date=start_range_for_samples, end_date=end_range_for_samples)
            reports_starting_from = start_records_date_obj.strftime('%Y-%m-%d')

            # Occupation
            occupation = ""
            if age >=18:
                occupation = fake.job()
            if age >= igs.senior_age_threshold:
                occupation = f"Retired {occupation}"
            
            
            # Language
            language = random.choices(igs.languages, weights=igs.language_weights, k=1)[0]

                
            is_foster_care = False
            is_child_protection = False
            if age < 18: # Check if the person is a youth
                # 60% chance for youth to be in foster care
                if random.random() < igs.is_in_foster_care_chance:
                    is_foster_care = True
                if random.random() < igs.is_child_protection_chance:
                    is_child_protection = True
                    
            has_nickname = False
            if random.random() < igs.has_nickname_chance:
                has_nickname = random.choice([fake.color_name(), fake.word().capitalize(), fake.first_name()])

            # Ensure we have at least one home address from the filtered list
            home_address_data = random.choice(filtered_addresses_for_person)
            person_addresses.append({"address": home_address_data['address'], "type": "Home"})

            # Get the appropriate place types based on age
            relevant_place_types = []
            if age < 18: # Youth
                relevant_place_types = igs.youth_places
            elif age >= igs.senior_age_threshold: # Elderly
                relevant_place_types = igs.elderly_places 
            else: # Adults 
                relevant_place_types = igs.adult_places 

            # Sample two additional unique addresses from the filtered list
            available_for_sampling = [
                item for item in filtered_addresses_for_person
                if item['address'] != home_address_data['address']
            ]
            if len(available_for_sampling) < 2:
                available_for_sampling += random.sample(all_available_addresses_data, 2) 
            random.shuffle(available_for_sampling) # Shuffle to make selection random

            for i in range(random.randint(1, len(available_for_sampling))):
                chosen_address_data = available_for_sampling[i]
                # Assign a random type from the relevant_place_types list
                address_type = random.choice(relevant_place_types)
                person_addresses.append({"address": chosen_address_data['address'], "type": address_type})
            
            traced_locations = [a['address'] for a in filtered_addresses_for_person]
            if len(traced_locations) >10:
                 traced_locations = random.sample(traced_locations, 10)
            else:
                for i in range(len(traced_locations), 11):
                    traced_locations.append(random.choice(all_available_addresses_data)['address'])
            
            with open(f"../data/{str(misperid)}/connected_addresses.txt", 'w+') as f:
                for item in person_addresses:
                    f.write(f"{item['address']}\n")
            with open(f"../data/{str(misperid)}/connected_locations.txt", 'w+') as f:
                for item in person_addresses:
                    f.write(f"{item['type']}\n")
        
        # Connected Names Generation
        num_people= random.randint(5, 50)

        reported_names = []
        connected_people_names = []
        connected_people_desc = []
        connected_people_relat = []
        
        relationships_no_duplicates_used = set()
        for i in range(num_people):
            relationship_type = ""
            gender_connected = random.choice(["Male", "Female"])
            relationship_type = random.choice(igs.relationships(age, gender_connected, is_foster_care))
            
            if relationship_type in igs.relationships_noduplicates:
                if relationship_type not in relationships_no_duplicates_used:
                    relationships_no_duplicates_used.add(relationship_type)
                else: 
                    relationship_type = "other"
                
            if relationship_type in igs.relationships_family and random.random() < 0.9:
                relationship_last_name  = last_name
            else:
                relationship_last_name = fake.last_name()
                
            if gender_connected == "Female":
                relationship_first_name = fake.first_name_female()
            else:
                relationship_first_name = fake.first_name_male()
            
            reported_names.append(relationship_first_name + ' ' + relationship_last_name)

            rand = random.random()
            if rand < 0.3 and relationship_type != "other":
                # 30% chance: report both name and relationship
                if random.random() < 0.5:
                    connected_people_relat.append(f"{relationship_type} - {relationship_first_name} {relationship_last_name}")
                else:
                    connected_people_relat.append(f"{relationship_first_name} {relationship_last_name} ({relationship_type})")
            elif rand < 0.65 and relationship_type != "other":
                # Next 35%: report only the relationship
                connected_people_desc.append(relationship_type)
            elif rand < 0.825:
                # Next 17.5%: report full name
                connected_people_names.append(f"{relationship_first_name} {relationship_last_name}")
            else:
                # Final 17.5%: report just the first name
                connected_people_names.append(relationship_first_name)

        print(connected_people_names, connected_people_relat, connected_people_desc)
        with open(f"../data/{str(misperid)}/connected_people_names.txt", "w+") as f:
            f.write("\n".join(connected_people_names))
        with open(f"../data/{str(misperid)}/connected_people_relat.txt", "w+") as f:
            f.write("\n".join(connected_people_relat))
        with open(f"../data/{str(misperid)}/connected_people_desc.txt", "w+") as f:
            f.write("\n".join(connected_people_desc))
            
        # sample between 1 and 5 themes in location patterns
        location_patterns = random.sample(igs.location_patterns, random.randint(1, 6))
        with open(f"../data/{str(misperid)}/location_patterns.txt", "w+") as f:
                    f.write("\n".join(location_patterns))
        
        # sample between 1 and 5 patterns
        patterns = random.sample(igs.missing_person_patterns, random.randint(1, 6))
        with open(f"../data/{str(misperid)}/patterns.txt", "w+") as f:
                    f.write("\n".join(patterns))
        
        
        person_data = {
            "forenames": first_name,
            "surname": last_name,
            "maidenname": maiden_name,
            "nickname": "" if has_nickname==False else has_nickname,
            "misperid": misperid,
            "nominalid": nominalid,
            "sex": sex,
            "date_of_birth": dob,
            "age": age,
            "foster care": is_foster_care,
            "child_protection": is_child_protection,
            "ethnical_appearance": ethnical_appearance,
            "person_language": language,
            "place_of_birth": place_of_birth,
            "disability_status": disability_status if disability_status in ['No', 'Not Known'] else "Yes (please specify)",
            "disability_desc": "" if disability_status in ['No', 'Not Known'] else disability_status,
            "occupation": occupation,
            "reports_starting_from": reports_starting_from,
            "addresses": person_addresses,
            "traced_locations": traced_locations,
            "people_reporting": reported_names[:random.randint(1,10)],
        }
        all_person_data.append(person_data)

    return json.dumps(all_person_data, indent=4), all_person_data, misperids_generated

if __name__ == "__main__":

    num_records = 10    
    print(f"--- Generating {num_records} People Data")
    multiple_people_json = generate_person_data(
        num_records=num_records,
        address_csv_filepath='utils/adresses.csv',
    )
    print(multiple_people_json[0])
    
    generated_misperids = []
    
    for person_record in multiple_people_json[1]:
        misperid = person_record['misperid']
        generated_misperids.append(misperid)
        person_dir = os.path.join("../data", str(misperid)) # Create path: data/{misperid}
        # os.makedirs(person_dir, exist_ok=True) # Create the misperid directory

        file_path = os.path.join(person_dir, "initial.json") # Create path: data/{misperid}/persona.json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(person_record, f, indent=4) # Save the dictionary as JSON


