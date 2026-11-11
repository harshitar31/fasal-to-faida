"""Hand-made pincode-CSV -> centroid-CSV district aliases, moved here from
sms/sms_handler.py. build_geo.py uses them as a fallback only when the
target exists in the same state. Prefer adding new fixes to
datasets/geo/overrides.csv instead."""

DISTRICT_ALIASES = {
    # Andhra Pradesh
    "ananthapur":               "Anantapur",
    "karim nagar":              "Karimnagar",
    "k.v.rangareddy":           "Rangareddi",
    "visakhapatnam":            "Vishakhapatnam",

    # Assam
    "dhubri":                   "Dhuburi",
    "mammit":                   "Mamit",

    # Bihar
    "east champaran":           "Purba Champaran",
    "west champaran":           "Pashchim Champaran",
    "kaimur (bhabua)":          "Bhabua",
    "palamau":                  "Palamu",
    "arwal":                    "Jehanabad",       # nearest centroid

    # Chhattisgarh
    "bijapur(cgh)":             "Bijapur",

    # Delhi
    "central delhi":            "Delhi",
    "east delhi":               "Delhi",
    "new delhi":                "Delhi",
    "north delhi":              "Delhi",
    "north west delhi":         "Delhi",
    "south delhi":              "Delhi",
    "south west delhi":         "Delhi",
    "west delhi":               "Delhi",

    # Gujarat
    "ahmedabad":                "Ahmadabad",
    "ahmed nagar":              "Ahmednagar",
    "banaskantha":              "Banas Kantha",
    "gandhi nagar":             "Gandhinagar",
    "sabarkantha":              "Sabar Kantha",
    "surendra nagar":           "Surendranagar",

    # Himachal Pradesh
    "bilaspur (hp)":            "Bilaspur",
    "hamirpur(hp)":             "Hamirpur",
    "lahul & spiti":            "Lahul And Spiti",

    # J&K
    "ananthnag":                "Anantnag (Kashmir South)",
    "baramulla":                "Baramula (Kashmir North)",
    "poonch":                   "Punch",
    "reasi":                    "Rajauri",         # nearest centroid

    # Jharkhand
    "giridh":                   "Giridih",
    "khunti":                   "Ranchi",          # nearest centroid
    "ramgarh":                  "Ranchi",          # nearest centroid
    "seraikela-kharsawan":      "Saraikela Kharsawan",
    "east singhbhum":           "Purba Singhbhum",
    "west singhbhum":           "Pashchim Singhbhum",

    # Karnataka
    "bangalore":                "Bangalore Urban",
    "chickmagalur":             "Chikmagalur",
    "chikkaballapur":           "Chikmagalur",     # nearest centroid
    "dakshina kannada":         "Dakshin Kannad",
    "davangere":                "Davanagere",
    "ramanagar":                "Bangalore Rural",  # nearest centroid
    "krishnagiri":              "Dharmapuri",       # nearest centroid
    "uttara kannada":           "Uttar Kannand",
    "yadgir":                   "Gulbarga",         # nearest centroid
    "bijapur(kar)":             "Bijapur",

    # Kerala
    "kasargod":                 "Kasaragod",
    "pathanamthitta":           "Pattanamtitta",

    # Madhya Pradesh
    "alirajpur":                "Jhabua",           # nearest centroid
    "ashok nagar":              "Ashoknagar",
    "budaun":                   "Badaun",
    "khargone":                 "East Nimar",
    "rajnandgaon":              "Raj Nandgaon",
    "singrauli":                "Sidhi",            # nearest centroid

    # Maharashtra
    "aurangabad(bh)":           "Aurangabad",
    "beed":                     "Bid",
    "buldhana":                 "Buldana",
    "gadchiroli":               "Garhchiroli",
    "gondia":                   "Gondiya",
    "mumbai":                   "Greater Bombay",
    "raigarh(mh)":              "Raigarh",

    # Manipur
    "imphal east":              "East Imphal",
    "imphal west":              "West Imphal",

    # Meghalaya
    "ri bhoi":                  "Ri-Bhoi",

    # Nagaland
    "kiphire":                  "Tuensang",         # nearest centroid
    "longleng":                 "Mokokchung",       # nearest centroid
    "peren":                    "Kohima",           # nearest centroid

    # Odisha
    "balangir":                 "Bolangir",
    "baleswar":                 "Baleshwar",
    "bargarh":                  "Baragarh",
    "debagarh":                 "Deogarh",
    "gadchiroli":               "Garhchiroli",
    "jagatsinghapur":           "Jagatsinghpur",
    "jajapur":                  "Jajpur",
    "kendujhar":                "Keonjhar",
    "khorda":                   "Khordha",
    "nabarangapur":             "Nabarangpur",
    "sonapur":                  "Sonepur",
    "sundergarh":               "Sundargarh",

    # Puducherry
    "pondicherry":              "Puducherry",

    # Punjab
    "nawanshahr":               "Nawan Shehar",
    "ropar":                    "Rupnagar",

    # Rajasthan
    "chittorgarh":              "Chittaurgarh",
    "dholpur":                  "Dhaulpur",
    "jhujhunu":                 "Jhunjhunun",

    # Tamil Nadu
    "tiruchirappalli":          "Tiruchchirappalli",
    "tiruchirapalli":           "Tiruchchirappalli",
    "tiruchi":                  "Tiruchchirappalli",
    "trichy":                   "Tiruchchirappalli",
    "tirunelveli":              "Tirunelveli Kattabo",
    "tiruvallur":               "Thiruvallur",
    "tiruvarur":                "Thiruvarur",
    "kancheepuram":             "Kancheepuram",
    "kanchipuram":              "Kancheepuram",
    "the nilgiris":             "Nilgiris",
    "tuticorin":                "Thoothukudi",
    "kanyakumari":              "Kanniyakumari",
    "chengalpattu":             "Kancheepuram",     # nearest centroid
    "ranipet":                  "Vellore",           # nearest centroid
    "tiruppur":                 "Tirupur",

    # Uttar Pradesh
    "barabanki":                "Bara Banki",
    "bagpat":                   "Baghpat",
    "raebareli":                "Rae Bareli",
    "sant ravidas nagar":       "Sant Ravi Das Nagar",
    "siddharthnagar":           "Siddharth Nagar",
    "shrawasti":                "Shravasti",
    "budaun":                   "Badaun",
    "kanpur nagar":             "Kanpur",
    "kheri":                    "Lakhimpur Kheri",

    # Uttarakhand
    "dehradun":                 "Dehra Dun",
    "nainital":                 "Naini Tal",
    "rudraprayag":              "Rudra Prayag",

    # West Bengal
    "bardhaman":                "Barddhaman",
    "howrah":                   "Haora",
    "malda":                    "Maldah",
    "north dinajpur":           "Uttar Dinajpur",
    "south dinajpur":           "Dakshin Dinajpur",
    "sonipat":                  "Sonepat",

    # Other / Union Territories
    "dadra & nagar haveli":     "Dadra And Nagar Haveli",
    "lakshadweep":              "Kavaratti",
    "east sikkim":              "East",
    "dibang valley":            "Upper Dibang Valley",
    "bilaspur(cgh)":            "Bilaspur",
}
