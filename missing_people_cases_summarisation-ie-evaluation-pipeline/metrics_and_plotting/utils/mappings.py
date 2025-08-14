mp_column_contexts = {
    'misperid': 'Missing person identifier',
    'initial_risk_level': 'Initial assessed risk level when reported missing',
    'current_final_risk_level': 'Final risk level assessment',
    'forenames': 'Given names of missing person',
    'surname': 'Family name of missing person',
    'dob': 'Date of birth',
    'pob': 'Place of birth',
    'age': 'Age at time of going missing',
    'sex': 'Gender/sex of missing person',
    'residence_type': 'Type of residence (home, care facility, etc.)',
    'occdesc': 'Occupation description',
    'nominalpersionid': 'Nominal person identifier',
    'missing_since': 'Date/time when person went missing',
    'date_reported_missing': 'Date when missing person was reported',
    'day_reported_missing': 'Day of week when reported missing',
    'length_missing_mins': 'Duration missing in minutes',
    'when_traced': 'Date/time when person was found/traced',
    'mf_address': 'Missing from address',
    'missing_from': 'Location description where person went missing',
    'reported_missing_by': 'Who reported the person missing',
    'TL_address': 'Traced location address',
    'return_method_desc': 'Description of how person was found/returned',
    'circumstances': 'Circumstances surrounding the missing person case',
}

twenty_five_mp_questions = {
    "q_1": "Is there any identified risk of suicide?",
    "q_2": "Is criminality suspected to be a factor in the disappearance?",
    "q_3": "Is the Missing Person vulnerable due to age, infirmity or other similar factor?",
    "q_4": "Are there any known adverse effects if prescribed medication is not available to the Missing Person?",
    "q_5": "Does the Missing Person have dementia, medical or mental health conditions, physical illnesses or disabilities?",
    "q_6": "Does the Missing Person have problems interacting safely with others when finding themselves in unfamiliar circumstances?",
    "q_7": "Is there a dependency on drugs, alcohol, medication or other substances?",
    "q_8": "Is the Missing Person on the Child Protection Register?",
    "q_9": "Do the current/previous weather conditions present additional risk? Consider all circumstances including age and clothing.",
    "q_10": "Are there family/relationship problems or recent history of family conflict and/or abuse?",
    "q_11": "Is the Missing Person a victim or perpetrator of domestic violence?",
    "q_12": "Is there an ongoing personal issue linked to racial, sexual, homophobic, the local community or any cultural issues?",
    "q_13": "Was the Missing Person involved in a violent and/or hate crime incident prior to disappearance?",
    "q_14": "Are there any school, college, university, employment or financial problems?",
    "q_15": "Is forced marriage or honour based abuse an issue?",
    "q_16": "Is the Missing Person the victim of sexual exploitation, human trafficking or prostitution? If so, is going missing likely to place the Missing Person at risk of considerable harm.",
    "q_17": "Are the circumstances of going missing different from normal behaviour patterns?",
    "q_18": "Is there any known reason for the Missing Person to go missing?",
    "q_19": "Are there any indications that preparations have been made for absence?",
    "q_20": "What was the Missing Person intending to do when last seen? Did they fail to complete their intentions?",
    "q_21": "Has the Missing Person disappeared previously and were they exposed to harm on such occasions?",
    "q_22": "Is the missing person a risk to others? And if so in what way?",
    "q_23": "Are their other unlisted factors which the officer or supervisor considers relevant in the assessment of risk?",
    "q_24": "Does the Missing Person have a mental health condition (excluding dementia)?",
    "q_25": "Does this Missing Person have dementia or a specific progressive neurological disorder?"
}

vp_column_contexts = {
    'vpd_nominalincidentid_pk': 'Nominal person identifier',
    'vpd_consentname': "Name of the person who gave consent for the person to be added to the database",
    'vpd_noconsentreason': "Reason consent was not obtained",
    'vpd_createdon': "Date of the creation of the particular record",
    'vpd_lastupdatedon': "Date the record was last updated",
    'vpd_nominalsynopsis': "Description",
    'vpd_gpconsent': "Consent was given to contact the GP",
    'vpd_vptypeid_fk': "Vulnerability type",
    'vpd_incidentid_fk': "Incident type",
    'vpd_wellbeingcomments': "Wellbeing concerns",
    'vpd_notinformedreason': "Reason why the person was not informed",
    'vpd_nogpconsentreason': "Reason for not getting GP consent",
    'vpd_scra': "Scottish Children’s Reporter Administration",
    'vpd_threepointtest': "Three point test result",
    'vpd_youthattitude': "Reported attitude or behavior of the youth",
    'vpd_parentattitude': "Attitude or behavior of the parent(s)",
    'vpd_nominalsview': "Point of view of the individual",
    'vpd_childprotection': "Child protection concerns or status",
    'vpd_forename': "First name ",
    'vpd_surname': "Last name ",
    'vpd_maiden_name': "Maiden name",
    'vpd_createdon_1': "Date and time when the first record for a given person was created",
    'vpd_placeofbirth': "Place of birth",
    'vpd_personlanguage': "Language",
    'vpd_interpreterreqid_fk': "Key for interpreter",
    'vpd_disability': "Has disability",
    'vpd_disabilitydesc': "Disability",
    'vpd_personethnicappearance': "Ethnic appearance",
    'vpd_persongender': "Gender",
    'vpd_knownas': "Known as",
    'vpd_repeatvictim': "Repeat victim",
    'vpd_repeatperpetrator': "Repeat perpetrator",
    'misper_misperid': "Misperid",
    'vpd_serious_and_organised_crime_exploitation': "1. Involvement in serious and organised crime or exploitation",
    'vpd_stalking_and_harassment': "2. Subject to stalking or harassment",
    'vpd_suicide_concern': "3. Concerns about risk of suicide",
    'vpd_violence_used': "4. Violence has been used",
    'vpd_weapon_used__acra_only_': "5. Weapon has been used (ACRA only)",
    'vpd_bullying': "6. Subject to bullying",
    'vpd_child_at_locus': "7. Child present at the scene",
    'vpd_neglect': "8. Subject to neglect",
    'vpd_self_neglect': "9. Exhibiting self-neglect",
    'vpd_child_criminal_exploitation__cce_': "10. Child criminal exploitation (CCE)",
    'vpd_child_sexual_exploitation__cse_': "11. Child sexual exploitation (CSE)",
    'vpd_community_triage_service': "12. Referred to Community Triage Service",
    'vpd_distress_brief_intervention__dbi_': "13. Referred for Distress Brief Intervention (DBI)",
    'vpd_dsdas': "14. Domestic abuse referral (DSDAS)",
    'vpd_child_victim': "15. Child is a victim",
    'vpd_child_witnessed': "16. Child witnessed the incident",
    'vpd_female_genital_mutilation__fgm_': "17. Victim of Female Genital Mutilation (FGM)",
    'vpd_forced_marriage__fm_': "18. At risk of or subject to forced marriage",
    'vpd_gambling': "19. Gambling issues present",
    'vpd_honour_based_abuse__hba_': "20. Victim of honour-based abuse (HBA)",
    'vpd_human_trafficking': "21. Victim of human trafficking",
    'vpd_looked_after_accommodated_child__laac_': "22. Looked After or Accommodated Child (LAAC)",
    'vpd_missing_person': "23. Reported as a missing person",
    'vpd_online_child_sexual_abuse_and_exploitation__ocsae_': "24. Online child sexual abuse or exploitation (OCSAE)",
    'vpd_pregnancy__unborn_baby_': "25. Pregnancy or concern for unborn baby",
    'vpd_sexual_harm': "26. Victim of sexual harm",
    'vpd_elderly': "27. Elderly person involved or at risk",
    'vpd_attempted_suicide': "28. Attempted suicide",
    'vpd_financial': "29. Financial issues present",
    'vpd_sight_loss': "30. Sight loss or impairment",
    'vpd_physical_disability': "31. Physical disability",
    'vpd_psychological_harm': "32. Exposed to or at risk of psychological harm",
    'vpd_self_harm': "33. History or risk of self-harm",
    'vpd_isolation': "34. Social isolation",
    'vpd_hearing_loss': "35. Hearing loss or impairment",
    'vpd_alcohol_consumption': "36. Problematic alcohol consumption",
    'vpd_learning_disability': "37. Learning disability",
    'vpd_communication_needs': "38. Communication difficulties or needs",
    'vpd_mental_health_issues': "39. Mental health issues",
    'vpd_drug_consumption': "40. Problematic drug use",
    'vpd_other': "41. Other significant concern not listed",
    'vpd_radicalisation': "42. At risk of or involved in radicalisation"
}















































































