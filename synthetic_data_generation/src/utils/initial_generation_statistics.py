# Define age groups and their probabilities - 70% that from vulnerable age groups
age_groups = [
    {"name": "youth", "min_age": 10, "max_age": 17, "weight": 0.35},
    {"name": "adult", "min_age": 18, "max_age": 75, "weight": 0.30},
    {"name": "senior", "min_age": 76, "max_age": 99, "weight": 0.35}
]

age_groups_dict = {
    group["name"]: {k: v for k, v in group.items() if k != "name"}
    for group in age_groups
}

group_weights = [group["weight"] for group in age_groups]

# Maiden name probability for females (0 for male)
mainden_name_probability = 0.5 


# Disability Status
disability_statuses = [
    "No", "Not Known", "Hearing Impairment", "Visual Impairment", "Mobility Impairment",
    "Cognitive Impairment", "Chronic Illness", "Other"
]
disability_weights = [0.4, 0.4, 0.05, 0.05, 0.05, 0.02, 0.02, 0.01]

disability_statuses_dementia = [
    "No", "Not Known", "Hearing Impairment", "Visual Impairment", "Mobility Impairment",
    "Cognitive Impairment", "Chronic Illness", "Other", "Dementia"
]
disability_weights_dementia = [0.05,0.05, 0.03, 0.03, 0.03, 0.02, 0.02, 0.01, 0.86]


# For how many years back do the reports go 
senior_age_threshold = 70
youth_age_threshold_for_reports = 25
start_range_for_samples_senior = 15
start_range_for_samples_youth = 6
start_range_for_samples_other = 10

# chance of <18 be in foster care
is_in_foster_care_chance = 0.6
# chance of <18 be in child protection services
is_child_protection_chance = 0.5

# has nickname
has_nickname_chance = 0.5

# relationships family
relationships_other = ["friend", "other", "colleague"]

relationships_family_female_adult = ["mother", "sister", "aunt", "grandmother", "daughter"] + relationships_other
relationships_family_male_adult = ["father", "brother", "uncle", "grandfather", "son"]  + relationships_other


relationships_family_female_youth = ["mother", "sister", "aunt", "grandmother"] + relationships_other
relationships_family_male_youth = ["father", "brother", "uncle", "grandfather"]  + relationships_other

relationships_family_female_foster = ["foster mother"] + relationships_other
relationships_family_male_foster = ["foster father"] + relationships_other

relationships_family_female_elderly = ["sister", "daughter"] + relationships_other
relationships_family_male_elderly = ["brother", "son"] + relationships_other

relationships_family = ['sister', 'mother', 'aunt', 'uncle', 'father']
relationships_noduplicates = ["mother", "father", "foster mother", "foster father"]

def relationships(age, sex, foster_care):
    def is_in_group(age, group_name):
        group = age_groups_dict.get(group_name)
        if group:
            return group["min_age"] <= age <= group["max_age"]
        raise ValueError("Invalid group name")

    if is_in_group(age, "youth"):
        if foster_care:
            return relationships_family_female_foster if sex == "Female" else relationships_family_male_foster
        else:
            return relationships_family_female_youth if sex == "Female" else relationships_family_male_youth

    elif is_in_group(age, "senior"):
        return relationships_family_female_elderly if sex == "Female" else relationships_family_male_elderly

    elif is_in_group(age, "adult"):
        return relationships_family_female_adult if sex == "Female" else relationships_family_male_adult
    

# Based on: https://www.scotlandscensus.gov.uk/census-results/at-a-glance/languages/
languages = ["English", "Polish", "Chinese", "Gaelic", "Urdu", "Punjabi", "Spanish", "French", "German"]
language_weights = [
    0.80, # English
    0.025, 0.025, 0.025, 0.025,
    0.025, 0.025, 0.025, 0.025
]

    
ethnic_groups = [
    "Asian Indian",
    "Asian Pakistani",
    "Asian Bangladeshi",
    "Asian Chinese",
    "Asian other",
    "Black Caribbean",
    "Black British",
    "Black African",
    "Mixed",
    "White English",
    "White Welsh",
    "White Scottish",
    "White Northern Irish",
    "White Irish",
    "White Romani",
    "White other",
]
ethnic_group_weights = [
    0.04,  # Asian Indian
    0.04,  # Asian Pakistani
    0.03,  # Asian Bangladeshi
    0.03,  # Asian Chinese
    0.03,  # Asian other
    0.04,  # Black Caribbean
    0.04,  # Black British
    0.04,  # Black African
    0.05,  # Mixed
    0.20,  # White English (slightly reduced to balance)
    0.10,  # White Welsh
    0.15,  # White Scottish (increased likelihood)
    0.05,  # White Northern Irish
    0.04,  # White Irish
    0.02,  # White Romani
    0.04,  # White other
]
youth_places = [
    "school",
    "university",
    "college",
    "cafe",
    "library", 
    "shopping mall",
    "movie theater",
    "gym",
    "sports club",
    "youth center",
    "after-school program",
    "summer camp",
    "tutoring center",
    "dance studio",
    "music lessons",
    "part-time job",
    "volunteer organization",
    "friend's house",
    "playground",
    "skate park",
    "arcade",
    "fast food restaurant",
    "study group",
    "extracurricular activities"
]

elderly_places = [
    "senior center",
    "nursing home",
    "assisted living facility",
    "adult day care",
    "medical clinic",
    "hospital",
    "pharmacy",
    "grocery store",
    "community center",
    "church",
    "synagogue",
    "mosque",
    "library",
    "park",
    "doctor's office",
    "physical therapy clinic",
    "dialysis center",
    "senior housing",
    "retirement community",
    "bingo hall",
    "book club",
    "volunteer work",
    "grandchild's school events",
    "regular walking route",
    "neighborhood cafe"
]

adult_places = [
    "workplace",
    "office",
    "gym",
    "fitness center",
    "regular bar",
    "coffee shop",
    "grocery store",
    "daycare pickup",
    "school pickup",
    "parent-teacher meetings",
    "neighborhood association",
    "book club",
    "hobby group",
    "sports league",
    "church",
    "synagogue",
    "mosque",
    "volunteer organization",
    "community center",
    "library",
    "doctor's office",
    "dentist office",
    "hair salon",
    "regular restaurant",
    "dog park",
    "running group",
    "yoga class",
    "evening classes",
    "professional networking events",
    "homeowners association",
    "carpool group",
    "lunch meeting",
    "regular commute",
    "childcare facility",
    "medical appointments"
]
uk_cities = [
    "Bath", "Birmingham", "Bradford", "Brighton & Hove", "Bristol", "Cambridge", 
    "Canterbury", "Carlisle", "Chelmsford", "Chester", "Chichester", "Colchester", 
    "Coventry", "Derby", "Doncaster", "Durham", "Ely", "Exeter", "Gloucester", 
    "Hereford", "Kingston-upon-Hull", "Lancaster", "Leeds", "Leicester", "Lichfield", 
    "Lincoln", "Liverpool", "London", "Manchester", "Milton Keynes", "Newcastle-upon-Tyne", 
    "Norwich", "Nottingham", "Oxford", "Peterborough", "Plymouth", "Portsmouth", 
    "Preston", "Ripon", "Salford", "Salisbury", "Sheffield", "Southampton", 
    "Southend-on-Sea", "St Albans", "Stoke on Trent", "Sunderland", "Truro", 
    "Wakefield", "Wells", "Westminster", "Winchester", "Wolverhampton", "Worcester", 
    "York", "Armagh", "Bangor", "Belfast", "Lisburn", "Londonderry", "Newry", 
    "Aberdeen", "Dundee", "Dunfermline", "Edinburgh", "Glasgow", "Inverness", 
    "Perth", "Stirling", "Bangor", "Cardiff", "Newport", "St Asaph", "St Davids", 
    "Swansea", "Wrexham"
]
# from: https://www.gov.uk/government/publications/list-of-cities/list-of-cities-html


# -------PATTERNS-------------
location_patterns = [
    "water-related",
    "family-related",
    "workplace",
    "school-related",
    "travel-related",
    "vehicle-related",
    "hospital-related",
    "mental health-related",
    "domestic violence-related",
    "child custody-related",
    "wilderness",
    "forest",
    "national park",
    "mountain",
    "desert",
    "urban",
    "suburban",
    "rural",
    "home",
    "neighbor’s house",
    "friend’s house",
    "relative’s house",
    "vacation spot",
    "hotel/motel",
    "campground",
    "airport",
    "bus station",
    "train station",
    "shopping mall",
    "grocery store",
    "restaurant",
    "bar/nightclub",
    "concert venue",
    "sports arena",
    "parking lot",
    "beach",
    "lake",
    "river",
    "ocean",
    "dock/marina",
    "hiking trail",
    "hunting area",
    "fishing area",
    "snow area",
    "cabin",
    "abandoned building",
    "construction site",
    "warehouse",
    "factory",
    "military base",
    "boarding school",
    "juvenile center",
    "religious site",
    "church",
    "cemetery",
    "public park",
    "playground",
    "school bus stop",
    "gas station",
    "highway",
    "back road",
    "truck stop",
    "rest area",
    "bridge",
    "tunnel",
    "alleyway",
    "rooftop",
    "basement",
    "attic",
    "closet",
    "shed",
    "barn",
    "farm",
    "field",
    "orchard",
    "swamp",
    "cave",
    "cliff",
    "mine",
    "well",
    "storm drain",
    "sewer",
    "underground bunker",
    "amusement park",
    "fairground",
    "zoo",
    "petting zoo",
    "ski resort",
    "resort",
    "island",
    "cruise ship",
    "boat",
    "ferry",
    "bus",
    "train",
    "airplane",
    "elevator",
    "escalator",
    "locker room",
    "bathroom",
    "stairwell",
    "roadhouse",
    "casino",
    "internet café",
    "rehab center",
    "shelter",
    "safe house",
    "illegal site",
    "drug house",
    "gang territory",
    "cult location",
    "remote cabin",
    "foreign country",
    "border area"
] # generated by prompting GPT 4o via chat using: "You are generating fake data for missing person records. Come up with a list of at least 100 general themes of locations that may occur for people. For example, water-related or family-related. Give them in a Python list"

missing_person_patterns = [
    "mental health issues",
    "domestic violence escape",
    "travelled without telling family",
    "foul weather incident",
    "lost while hiking",
    "left behind no note",
    "job loss stress",
    "financial difficulties",
    "relationship breakdown",
    "sudden religious conversion",
    "seeking solitude",
    "withdrawn from university",
    "left personal items behind",
    "identity crisis",
    "abduction suspicion",
    "overdue return from walk",
    "left phone at home",
    "believed to be in another city",
    "suicidal ideation",
    "withdrew cash before leaving",
    "left in middle of night",
    "missed work with no contact",
    "last seen at train station",
    "possible ferry boarding",
    "was couch-surfing",
    "mental health facility patient",
    "known to frequent remote areas",
    "missing after night out",
    "recently moved to area",
    "suspected to be squatting",
    "active on social media before vanishing",
    "vehicle found abandoned",
    "missing after outdoor festival",
    "part of survivalist community",
    "undiagnosed mental illness",
    "chronic illness stress",
    "withdrew from family",
    "had spoken of disappearing",
    "linked to organized protest",
    "involved in legal dispute",
    "left passport and documents",
    "estranged from relatives",
    "unpaid debts",
    "possibly involved in cult",
    "left job unexpectedly",
    "in touch with unknown online group",
    "foreign travel suspected",
    "has gone missing before",
    "no contact with close friends",
    "left home during argument",
    "believed to be camping",
    "last seen near river",
    "disconnected from support services",
    "has history of trauma",
    "visiting remote island",
    "cut off communications",
    "recent bereavement",
    "romantic rejection",
    "new romantic partner unknown to others",
    "recent discharge from care facility",
    "personality changes before disappearance",
    "involved in criminal activity",
    "possible witness to crime",
    "interested in starting new life",
    "used aliases in past",
    "fear of deportation",
    "illegal employment status",
    "living off-grid",
    "disowned by family",
    "concerns over addiction",
    "recently outed LGBTQ+ identity",
    "religious or spiritual pilgrimage",
    "obsession with online game or group",
    "believed to be squatting",
    "dissociative fugue episode",
    "believed to be homeless",
    "recent escape from abusive household",
    "possibly joined commune",
    "contacted a stranger before vanishing",
    "disappeared after online interaction",
    "left during storm",
    "disconnected utilities before leaving",
    "believed to be in forested area",
    "disappeared after hiking trip",
    "possible sea kayaking accident",
    "interested in hermit lifestyle",
    "had maps of Highlands",
    "recently released from prison",
    "associated with political fringe group",
    "was paranoid about surveillance",
    "noted to act erratically",
    "last transaction at rural shop",
    "did not collect medication",
    "vanished during seasonal work",
    "suspected visa issues",
    "avoiding social services",
    "planned to sleep rough",
    "known to avoid authorities",
    "lived in converted van",
    "left creative works behind",
    "expressed desire to disappear",
    "unknown medical condition",
    "missing since court appearance",
    "possible boating incident"
] # generated using gpt-4o model via chat using You are generating fake data for missing person records. Come up with a list of at least 100 general themes of patterns that may occur for people. They should be general enough not to be specific to any age group. They should be possible for a person in Scotland. Give them in a Python list


