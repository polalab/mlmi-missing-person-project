vul_questions = '''1. Is there any identified risk of suicide? 
2. Is criminality suspected to be a factor in the disappearance?
3. Is the Missing Person vulnerable due to age, infirmity or other similar factor?
4. Are there any known adverse effects if prescribed medication is not available to the Missing Person?
5. Does the Missing Person have dementia, medical or mental health conditions, physical illnesses or disabilities?
6. Does the Missing Person have problems interacting safely with others when finding themselves in unfamiliar circumstances?
7. Is there a dependency on drugs, alcohol, medication or other substances?
8. Is the Missing Person on the Child Protection Register?
9. Do the current/previous weather conditions present additional risk? Consider all circumstances including age and clothing.
10. Are there family/relationship problems or recent history of family conflict and/or abuse? 
11. Is the Missing Person a victim or perpetrator of domestic violence?
12. Is there an ongoing personal issue linked to racial, sexual, homophobic, the local community or any cultural issues?
13. Was the Missing Person involved in a violent and/or hate crime incident prior to disappearance?
14. Are there any school, college, university, employment or financial problems?
15. Is forced marriage or honour based abuse an issue?
16. Is the Missing Person the victim of sexual exploitation, human trafficking or prostitution? If so, is going missing likely to place the Missing Person at risk of considerable harm.
17. Are the circumstances of going missing different from normal behaviour patterns?
18. Is there any known reason for the Missing Person to go missing?
19. Are there any indications that preparations have been made for absence?
20. What was the Missing Person intending to do when last seen? Did they fail to complete their intentions?
21. Has the Missing Person disappeared previously and were they exposed to harm on such occassions?
22. Is the missing person a risk to others? And if so in what way?
23. Are their other unlisted factors which the officer or supervisor considers relevant in the assessment of risk?
24. Does the Missing Person have a mental health condition (excluding dementia)? 
25. Does this Missing Person have dementia or a specific progressive neurological disorder?'''



vpd_mapping = {
    "vpd_serious_and_organised_crime_exploitation": "1. Involvement in serious and organised crime or exploitation",
    "vpd_stalking_and_harassment": "2. Subject to stalking or harassment",
    "vpd_suicide_concern": "3. Concerns about risk of suicide",
    "vpd_violence_used": "4. Violence has been used",
    "vpd_weapon_used__acra_only_": "5. Weapon has been used (ACRA only)",
    "vpd_bullying": "6. Subject to bullying",
    "vpd_child_at_locus": "7. Child present at the scene",
    "vpd_neglect": "8. Subject to neglect",
    "vpd_self_neglect": "9. Exhibiting self-neglect",
    "vpd_child_criminal_exploitation__cce_": "10. Child criminal exploitation (CCE)",
    "vpd_child_sexual_exploitation__cse_": "11. Child sexual exploitation (CSE)",
    "vpd_community_triage_service": "12. Referred to Community Triage Service",
    "vpd_distress_brief_intervention__dbi_": "13. Referred for Distress Brief Intervention (DBI)",
    "vpd_dsdas": "14. Domestic abuse referral (DSDAS)",
    "vpd_child_victim": "15. Child is a victim",
    "vpd_child_witnessed": "16. Child witnessed the incident",
    "vpd_female_genital_mutilation__fgm_": "17. Victim of Female Genital Mutilation (FGM)",
    "vpd_forced_marriage__fm_": "18. At risk of or subject to forced marriage",
    "vpd_gambling": "19. Gambling issues present",
    "vpd_honour_based_abuse__hba_": "20. Victim of honour-based abuse (HBA)",
    "vpd_human_trafficking": "21. Victim of human trafficking",
    "vpd_looked_after_accommodated_child__laac_": "22. Looked After or Accommodated Child (LAAC)",
    "vpd_missing_person": "23. Reported as a missing person",
    "vpd_online_child_sexual_abuse_and_exploitation__ocsae_": "24. Online child sexual abuse or exploitation (OCSAE)",
    "vpd_pregnancy__unborn_baby_": "25. Pregnancy or concern for unborn baby",
    "vpd_sexual_harm": "26. Victim of sexual harm",
    "vpd_elderly": "27. Elderly person involved or at risk",
    "vpd_attempted_suicide": "28. Attempted suicide",
    "vpd_financial": "29. Financial issues present",
    "vpd_sight_loss": "30. Sight loss or impairment",
    "vpd_physical_disability": "31. Physical disability",
    "vpd_psychological_harm": "32. Exposed to or at risk of psychological harm",
    "vpd_self_harm": "33. History or risk of self-harm",
    "vpd_isolation": "34. Social isolation",
    "vpd_hearing_loss": "35. Hearing loss or impairment",
    "vpd_alcohol_consumption": "36. Problematic alcohol consumption",
    "vpd_learning_disability": "37. Learning disability",
    "vpd_communication_needs": "38. Communication difficulties or needs",
    "vpd_mental_health_issues": "39. Mental health issues",
    "vpd_drug_consumption": "40. Problematic drug use",
    "vpd_other": "41. Other significant concern not listed",
    "vpd_radicalisation": "42. At risk of or involved in radicalisation"
}