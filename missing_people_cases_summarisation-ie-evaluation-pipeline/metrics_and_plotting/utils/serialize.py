import pandas as pd


def mp_serialize_dataframe_for_llm(df, column_contexts, question_mapping):
    """
    Serialize a MP dataframe.
    
    Parameters:
    - df: pandas DataFrame
    - column_contexts: descriptions of the columns
    - question_mapping: 25 questions at the end
    
    Returns:
    - str: Formatted string suitable for LLM input for MP data
    """
    for i in range(1, 26):
        q_col = f'q_{i}'
        q_exp_col = f'q_{i}_explanation'
        if q_col in df.columns:
            column_contexts[q_col] = question_mapping[f'q_{i}']
            column_contexts[q_exp_col] = f"Explanation: {i}"
    
    
    output_parts = []
    output_parts.append("MISSING PERSON RECORDS: ")
    
    basic_info =  ['misperid', 'forenames', 'surname', 'dob', 'age', 'sex', 'pob', 'occdesc']
    location_info = ['mf_address', 'missing_from', 'TL_address', 'residence_type']
    timing_info = ['missing_since', 'date_reported_missing', 'day_reported_missing', 'when_traced', 'length_missing_mins']
    risk_info = ['initial_risk_level', 'current_final_risk_level']
    people_info = ['reported_missing_by']

    for _, row in df.iterrows():
        output_parts.append(f"\nREPORT:  {row['reportid']}:")
        
        for col in basic_info:
            output_parts.append(f"  {column_contexts[col]}: {row[col]}")
        
        if any(col in df.columns for col in location_info):
            output_parts.append("Location Information:")
            for col in location_info:
                output_parts.append(f"  {column_contexts[col]}: {row[col]}")
        

        if any(col in df.columns for col in timing_info):
            output_parts.append("Timing Information:")
            for col in timing_info:
                output_parts.append(f"  {column_contexts[col]}: {row[col]}")
        

        if any(col in df.columns for col in risk_info):
            output_parts.append("Risk Assessment:")
            for col in risk_info:
                output_parts.append(f"  {column_contexts[col]}: {row[col]}")
        

        if any(col.lower() in df.columns for col in people_info):
            output_parts.append("Reported missing by:")
            for col in people_info:
                output_parts.append(f"  {column_contexts[col]}: {row[col]}")
                    

        output_parts.append(f"Circumstances: {row['circumstances']}")
        output_parts.append(f"Return Method: {row['return_method_desc']}")
        

        question_cols = [col for col in df.columns if col.startswith('q_') and not col.endswith('_explanation')]
        output_parts.append("Risk Assessment Questions:")
        for q_col in question_cols:
            q_text = question_mapping[q_col]
            answer = "No" if row[q_col]==0 else "Yes"
            output_parts.append(f"  {q_text}: {answer}")
                
                
            exp_col = f"{q_col}_explanation"
            if exp_col in df.columns and pd.notna(row[exp_col]):
                output_parts.append(f"    Explanation: {row[exp_col]}")
    
    return "\n".join(output_parts)

def vp_serialize_dataframe_for_llm(df, column_contexts):


    output_parts = []
    output_parts.append("VULNERABILITY RECORDS: ")
    
    basic_info = [r.lower() for r in [ 'VPD_FORENAME','VPD_SURNAME','VPD_KNOWNAS','VPD_MAIDEN_NAME', 'VPD_PERSONGENDER', 'VPD_PLACEOFBIRTH', 'VPD_PERSONETHNICAPPEARANCE', 'VPD_PERSONLANGUAGE', 'VPD_INTERPRETERREQID_FK', 'VPD_SCRA', 
                  'VPD_VPTYPEID_FK']]
        
    record_info =  [r.lower() for r in ['VPD_CREATEDON', 'VPD_LASTUPDATEDON', 'VPD_CREATEDON_1', 'VPD_CONSENTNAME','VPD_NOCONSENTREASON','VPD_GPCONSENT', 'VPD_NOGPCONSENTREASON', 'VPD_NOTINFORMEDREASON',  'VPD_THREEPOINTTEST', 'VPD_YOUTHATTITUDE', 'VPD_PARENTATTITUDE', 'VPD_NOMINALSVIEW']]

    risk_info =  [r.lower() for r in ['VPD_DISABILITY', 'VPD_DISABILITYDESC', 'VPD_WELLBEINGCOMMENTS', 'VPD_CHILDPROTECTION', 'VPD_REPEATVICTIM', 'VPD_REPEATPERPETRATOR' , 'vpd_serious_and_organised_crime_exploitation', 'vpd_stalking_and_harassment', 
                 'vpd_suicide_concern', 'vpd_violence_used', 'vpd_weapon_used__acra_only_', 'vpd_bullying', 
                 'vpd_child_at_locus', 'vpd_neglect', 'vpd_self_neglect', 'vpd_child_criminal_exploitation__cce_', 
                 'vpd_child_sexual_exploitation__cse_', 'vpd_community_triage_service', 'vpd_distress_brief_intervention__dbi_',
                 'vpd_dsdas', 'vpd_child_victim', 'vpd_child_witnessed', 'vpd_female_genital_mutilation__fgm_', 'vpd_forced_marriage__fm_', 
                 'vpd_gambling', 'vpd_honour_based_abuse__hba_', 'vpd_human_trafficking', 'vpd_looked_after_accommodated_child__laac_',
                 'vpd_missing_person', 'vpd_online_child_sexual_abuse_and_exploitation__ocsae_', 'vpd_pregnancy__unborn_baby_', 
                 'vpd_sexual_harm', 'vpd_elderly', 'vpd_attempted_suicide', 'vpd_financial', 'vpd_sight_loss', 'vpd_physical_disability',
                 'vpd_psychological_harm', 'vpd_self_harm', 'vpd_isolation', 'vpd_hearing_loss', 'vpd_alcohol_consumption', 'vpd_learning_disability',
                 'vpd_communication_needs', 'vpd_mental_health_issues', 'vpd_drug_consumption', 'vpd_other', 'vpd_radicalisation']]    



    
    for _, row in df.iterrows():
        output_parts.append(f"\nREPORT:  {row['VPD_NOMINALINCIDENTID_PK'.lower()]}:")
        

        for col in basic_info:
            if pd.notna(row[col]):


                output_parts.append(f"  {column_contexts[col]}: {row[col]}")
        

        if any(col in df.columns for col in risk_info):
            output_parts.append("Record:")
            for col in record_info:
                if pd.notna(row[col]):
                    if row[col] in (0,'0'):
                        output_parts.append(f"  {column_contexts[col]}: {'No'}")
                    elif row[col] in (1,'1'):
                        output_parts.append(f"  {column_contexts[col]}: {'Yes'}")
                    else:
                        output_parts.append(f"  {column_contexts[col]}: {row[col]}")
            
        

        output_parts.append(f"Description: {row['VPD_NOMINALSYNOPSIS'.lower()]}")
        

        if any(col in df.columns for col in risk_info):
            output_parts.append("Risks:")
            for col in risk_info:
                if pd.notna(row[col]):
                    if row[col] in (0,'0'):
                        output_parts.append(f"  {column_contexts[col]}: {'No'}")
                    elif row[col] in (1,'1'):
                        output_parts.append(f"  {column_contexts[col]}: {'Yes'}")
                    else:
                        output_parts.append(f"  {column_contexts[col]}: {row[col]}")
    return "\n".join(output_parts)





def mp_serialize_dataframe_for_llm_cirumstancesonly(df, column_contexts, question_mapping):
    """
    Serialize a MP dataframe.
    
    Parameters:
    - df: pandas DataFrame
    - column_contexts: descriptions of the columns
    - question_mapping: 25 questions at the end
    
    Returns:
    - str: Formatted string suitable for LLM input for MP data
    """
    for i in range(1, 26):
        q_col = f'q_{i}'
        q_exp_col = f'q_{i}_explanation'
        if q_col in df.columns:
            column_contexts[q_col] = question_mapping[f'q_{i}']
            column_contexts[q_exp_col] = f"Explanation: {i}"
    
    
    output_parts = []
    output_parts.append("MISSING PERSON RECORDS: ")

    for _, row in df.iterrows():
        output_parts.append(f"\nREPORT:  {row['reportid']}:")
        output_parts.append(f"Circumstances: {row['circumstances']}")
    
    return "\n".join(output_parts)

def vp_serialize_dataframe_for_llm_nominalsynopsisonly(df):


    output_parts = []
    output_parts.append("VULNERABILITY RECORDS: ")
    
    for _, row in df.iterrows():
        output_parts.append(f"\nREPORT:  {row['VPD_NOMINALINCIDENTID_PK'.lower()]}:")

        output_parts.append(f"Description: {row['VPD_NOMINALSYNOPSIS'.lower()]}")
    return "\n".join(output_parts)