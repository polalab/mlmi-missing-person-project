import pandas as pd
import json

def serialize_for_llm(df):
    serialized_prompts = []
    n = 1
    for _, row in df.iterrows():
        prompt = serialize_row(row)
        serialized_prompts.append(prompt)
        n+=1
    return serialized_prompts

def serialize_row(row, misperid):
    with open(f"../data/{misperid}/initial.json", 'r') as f:
        person = json.load(f)
    prompt=(
            f"Disappearance Record:\n"
            f"Report number: {row['reportid']}\n"
            f"Name: {row['forenames']} {row['surname']}\n"
            f"Date of Birth: {row['dob']}\n"
            f"Age: {row['age']}\n"
            f"Sex: {row['sex']}\n"
            f"Disability: {person['disability_status']}\n")
    if int(row['age']) <=18:
        prompt += f"Foster case: {person['foster care']}\n"
    prompt += (
            f"Place of Birth: {row['pob']}\n"
            f"Occupation: {row['occdesc']}\n"
            f"Initial risk level: {row['initial_risk_level']}\n"
            f"Final risk level {row['current_final_risk_level']}\n"
            f"Missing Since: {row['missing_since']}\n"
            f"Date Reported Missing: {row['date_reported_missing']}\n"
            f"Day Reported Missing: {row['day_reported_missing']}\n"
            f"Length Missing (minutes): {row['length_missing_mins']}\n"
            f"When Traced: {row['when_traced']}\n"
            f"Missing From Address: {row['mf_address']} ({row['missing_from']})\n"
            f"Traced at Address: {row['TL_address']}\n"
            f"Traced by: {row['return_method_desc']}\n")
    
    return prompt

# def serialize_for_questions(row):
    