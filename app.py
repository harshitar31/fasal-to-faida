# =============================================================================
# app.py — Fasal-to-Faida  |  Bech Sahi, Kamaao Zyada
# Agrikon-inspired UI — integrated with live XGBoost price model
#
# pip install streamlit pandas numpy matplotlib joblib xgboost scikit-learn
# streamlit run app.py
# =============================================================================

import io
import random
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(
    page_title="Fasal-to-Faida | Market Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# PALETTE
# =============================================================================
GREEN       = "#1B4332"
GREEN_MID   = "#2D6A4F"
GREEN_LIGHT = "#52B788"
AMBER       = "#E8A020"
AMBER_DARK  = "#C8590A"
BG_WHITE    = "#FFFFFF"
BG_OFFWHITE = "#F7F4EF"
TEXT_DARK   = "#1A1A1A"
TEXT_MUTED  = "#666666"
BORDER      = "#E0DAD0"

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
CROPS  = ["Tomato","Onion","Potato","Wheat","Rice"]

INDIAN_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
    "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
    "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
    "Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
    "Delhi","Jammu & Kashmir","Ladakh","Puducherry",
]

@st.cache_data(show_spinner=False)
def load_state_districts():
    """Build state→[districts] mapping from the pincode CSV."""
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "datasets", "india pincode final.csv")
    try:
        df = pd.read_csv(csv_path, usecols=["Districtname", "statename"], dtype=str)
        df = df.dropna(subset=["Districtname", "statename"])
        # CSV state names are ALL CAPS — title-case them for matching
        df["state_tc"] = df["statename"].str.strip().str.title()
        # Special corrections (title-case mangles some names)
        corrections = {
            "Jammu & Kashmir": "Jammu & Kashmir",
            "Andaman & Nicobar Islands": "Andaman & Nicobar Islands",
            "Dadra & Nagar Haveli And Daman & Diu": "Dadra & Nagar Haveli and Daman & Diu",
        }
        for wrong, right in corrections.items():
            df.loc[df["state_tc"] == wrong, "state_tc"] = right
        mapping = (
            df.groupby("state_tc")["Districtname"]
            .apply(lambda s: sorted(s.str.strip().unique().tolist()))
            .to_dict()
        )
        return mapping
    except Exception:
        return {}

STATE_DISTRICTS = load_state_districts()

# — keep a fallback so the app never breaks even if CSV is missing —
_FALLBACK_DISTRICTS = {
    "Andhra Pradesh": ["Anantapur","Chittoor","East Godavari","Guntur","Krishna","Kurnool","Nellore","Prakasam","Srikakulam","Visakhapatnam","Vizianagaram","West Godavari","YSR Kadapa"],
    "Arunachal Pradesh": ["Anjaw","Changlang","East Kameng","East Siang","Kurung Kumey","Lohit","Longding","Lower Dibang Valley","Lower Subansiri","Namsai","Papum Pare","Tawang","Tirap","Upper Dibang Valley","Upper Siang","Upper Subansiri","West Kameng","West Siang"],
    "Assam": ["Baksa","Barpeta","Biswanath","Bongaigaon","Cachar","Charaideo","Chirang","Darrang","Dhemaji","Dhubri","Dibrugarh","Dima Hasao","Goalpara","Golaghat","Hailakandi","Hojai","Jorhat","Kamrup","Kamrup Metropolitan","Karbi Anglong","Karimganj","Kokrajhar","Lakhimpur","Majuli","Morigaon","Nagaon","Nalbari","Sivasagar","Sonitpur","South Salmara-Mankachar","Tinsukia","Udalguri","West Karbi Anglong"],
    "Bihar": ["Araria","Arwal","Aurangabad","Banka","Begusarai","Bhagalpur","Bhojpur","Buxar","Darbhanga","East Champaran","Gaya","Gopalganj","Jamui","Jehanabad","Kaimur","Katihar","Khagaria","Kishanganj","Lakhisarai","Madhepura","Madhubani","Munger","Muzaffarpur","Nalanda","Nawada","Patna","Purnia","Rohtas","Saharsa","Samastipur","Saran","Sheikhpura","Sheohar","Sitamarhi","Siwan","Supaul","Vaishali","West Champaran"],
    "Chhattisgarh": ["Balod","Baloda Bazar","Balrampur","Bastar","Bemetara","Bijapur","Bilaspur","Dantewada","Dhamtari","Durg","Gariaband","Janjgir-Champa","Jashpur","Kabirdham","Kanker","Kondagaon","Korba","Korea","Mahasamund","Mungeli","Narayanpur","Raigarh","Raipur","Rajnandgaon","Sukma","Surajpur","Surguja"],
    "Goa": ["North Goa","South Goa"],
    "Gujarat": ["Ahmedabad","Amreli","Anand","Aravalli","Banaskantha","Bharuch","Bhavnagar","Botad","Chhota Udaipur","Dahod","Dang","Devbhoomi Dwarka","Gandhinagar","Gir Somnath","Jamnagar","Junagadh","Kheda","Kutch","Mahisagar","Mehsana","Morbi","Narmada","Navsari","Panchmahal","Patan","Porbandar","Rajkot","Sabarkantha","Surat","Surendranagar","Tapi","Vadodara","Valsad"],
    "Haryana": ["Ambala","Bhiwani","Charkhi Dadri","Faridabad","Fatehabad","Gurugram","Hisar","Jhajjar","Jind","Kaithal","Karnal","Kurukshetra","Mahendragarh","Nuh","Palwal","Panchkula","Panipat","Rewari","Rohtak","Sirsa","Sonipat","Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur","Chamba","Hamirpur","Kangra","Kinnaur","Kullu","Lahaul and Spiti","Mandi","Shimla","Sirmaur","Solan","Una"],
    "Jharkhand": ["Bokaro","Chatra","Deoghar","Dhanbad","Dumka","East Singhbhum","Garhwa","Giridih","Godda","Gumla","Hazaribagh","Jamtara","Khunti","Koderma","Latehar","Lohardaga","Pakur","Palamu","Ramgarh","Ranchi","Sahibganj","Seraikela Kharsawan","Simdega","West Singhbhum"],
    "Karnataka": ["Bagalkot","Ballari","Belagavi","Bengaluru Rural","Bengaluru Urban","Bidar","Chamarajanagar","Chikkaballapur","Chikkamagaluru","Chitradurga","Dakshina Kannada","Davanagere","Dharwad","Gadag","Hassan","Haveri","Kalaburagi","Kodagu","Kolar","Koppal","Mandya","Mysuru","Raichur","Ramanagara","Shivamogga","Tumakuru","Udupi","Uttara Kannada","Vijayapura","Yadgir"],
    "Kerala": ["Alappuzha","Ernakulam","Idukki","Kannur","Kasaragod","Kollam","Kottayam","Kozhikode","Malappuram","Palakkad","Pathanamthitta","Thiruvananthapuram","Thrissur","Wayanad"],
    "Madhya Pradesh": ["Agar Malwa","Alirajpur","Anuppur","Ashoknagar","Balaghat","Barwani","Betul","Bhind","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Dindori","Guna","Gwalior","Harda","Hoshangabad","Indore","Jabalpur","Jhabua","Katni","Khandwa","Khargone","Mandla","Mandsaur","Morena","Narsinghpur","Neemuch","Panna","Raisen","Rajgarh","Ratlam","Rewa","Sagar","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Sidhi","Singrauli","Tikamgarh","Ujjain","Umaria","Vidisha"],
    "Maharashtra": ["Ahmednagar","Akola","Amravati","Aurangabad","Beed","Bhandara","Buldhana","Chandrapur","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur","Mumbai City","Mumbai Suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad","Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindhudurg","Solapur","Thane","Wardha","Washim","Yavatmal"],
    "Manipur": ["Bishnupur","Chandel","Churachandpur","Imphal East","Imphal West","Senapati","Tamenglong","Thoubal","Ukhrul"],
    "Meghalaya": ["East Garo Hills","East Jaintia Hills","East Khasi Hills","North Garo Hills","Ri Bhoi","South Garo Hills","South West Garo Hills","South West Khasi Hills","West Garo Hills","West Jaintia Hills","West Khasi Hills"],
    "Mizoram": ["Aizawl","Champhai","Kolasib","Lawngtlai","Lunglei","Mamit","Saiha","Serchhip"],
    "Nagaland": ["Dimapur","Kiphire","Kohima","Longleng","Mokokchung","Mon","Peren","Phek","Tuensang","Wokha","Zunheboto"],
    "Odisha": ["Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh","Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi","Kandhamal","Kendrapara","Kendujhar","Khordha","Koraput","Malkangiri","Mayurbhanj","Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"],
    "Punjab": ["Amritsar","Barnala","Bathinda","Faridkot","Fatehgarh Sahib","Fazilka","Ferozepur","Gurdaspur","Hoshiarpur","Jalandhar","Kapurthala","Ludhiana","Mansa","Moga","Muktsar","Nawanshahr","Pathankot","Patiala","Rupnagar","SAS Nagar","Sangrur","Tarn Taran"],
    "Rajasthan": ["Ajmer","Alwar","Banswara","Baran","Barmer","Bharatpur","Bhilwara","Bikaner","Bundi","Chittorgarh","Churu","Dausa","Dholpur","Dungarpur","Hanumangarh","Jaipur","Jaisalmer","Jalore","Jhalawar","Jhunjhunu","Jodhpur","Karauli","Kota","Nagaur","Pali","Pratapgarh","Rajsamand","Sawai Madhopur","Sikar","Sirohi","Sri Ganganagar","Tonk","Udaipur"],
    "Sikkim": ["East Sikkim","North Sikkim","South Sikkim","West Sikkim"],
    "Tamil Nadu": ["Ariyalur","Chennai","Coimbatore","Cuddalore","Dharmapuri","Dindigul","Erode","Kallakurichi","Kanchipuram","Kanyakumari","Karur","Krishnagiri","Madurai","Nagapattinam","Namakkal","Nilgiris","Perambalur","Pudukkottai","Ramanathapuram","Ranipet","Salem","Sivaganga","Tenkasi","Thanjavur","Theni","Thoothukudi","Tiruchirappalli","Tirunelveli","Tirupathur","Tiruppur","Tiruvallur","Tiruvannamalai","Tiruvarur","Vellore","Viluppuram","Virudhunagar"],
    "Telangana": ["Adilabad","Bhadradri Kothagudem","Hyderabad","Jagtial","Jangaon","Jayashankar Bhupalpally","Jogulamba Gadwal","Kamareddy","Karimnagar","Khammam","Kumuram Bheem","Mahabubabad","Mahabubnagar","Mancherial","Medak","Medchal-Malkajgiri","Mulugu","Nagarkurnool","Nalgonda","Narayanpet","Nirmal","Nizamabad","Peddapalli","Rajanna Sircilla","Rangareddy","Sangareddy","Siddipet","Suryapet","Vikarabad","Wanaparthy","Warangal Rural","Warangal Urban","Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai","Gomati","Khowai","North Tripura","Sepahijala","South Tripura","Unakoti","West Tripura"],
    "Uttar Pradesh": ["Agra","Aligarh","Allahabad","Ambedkar Nagar","Amethi","Amroha","Auraiya","Ayodhya","Azamgarh","Baghpat","Bahraich","Ballia","Balrampur","Banda","Barabanki","Bareilly","Basti","Bijnor","Budaun","Bulandshahr","Chandauli","Chitrakoot","Deoria","Etah","Etawah","Farrukhabad","Fatehpur","Firozabad","Gautam Buddha Nagar","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hapur","Hardoi","Hathras","Jalaun","Jaunpur","Jhansi","Kannauj","Kanpur Dehat","Kanpur Nagar","Kasganj","Kaushambi","Kushinagar","Lakhimpur Kheri","Lalitpur","Lucknow","Maharajganj","Mahoba","Mainpuri","Mathura","Mau","Meerut","Mirzapur","Moradabad","Muzaffarnagar","Pilibhit","Pratapgarh","Prayagraj","Rae Bareli","Rampur","Saharanpur","Sambhal","Sant Kabir Nagar","Shahjahanpur","Shamli","Shravasti","Siddharthnagar","Sitapur","Sonbhadra","Sultanpur","Unnao","Varanasi"],
    "Uttarakhand": ["Almora","Bageshwar","Chamoli","Champawat","Dehradun","Haridwar","Nainital","Pauri Garhwal","Pithoragarh","Rudraprayag","Tehri Garhwal","Udham Singh Nagar","Uttarkashi"],
    "West Bengal": ["Alipurduar","Bankura","Birbhum","Cooch Behar","Dakshin Dinajpur","Darjeeling","Hooghly","Howrah","Jalpaiguri","Jhargram","Kalimpong","Kolkata","Malda","Murshidabad","Nadia","North 24 Parganas","Paschim Bardhaman","Paschim Medinipur","Purba Bardhaman","Purba Medinipur","Purulia","South 24 Parganas","Uttar Dinajpur"],
    "Delhi": ["Central Delhi","East Delhi","New Delhi","North Delhi","North East Delhi","North West Delhi","Shahdara","South Delhi","South East Delhi","South West Delhi","West Delhi"],
    "Jammu & Kashmir": ["Anantnag","Bandipora","Baramulla","Budgam","Doda","Ganderbal","Jammu","Kathua","Kishtwar","Kulgam","Kupwara","Poonch","Pulwama","Rajouri","Ramban","Reasi","Samba","Shopian","Srinagar","Udhampur"],
    "Ladakh": ["Kargil","Leh"],
    "Puducherry": ["Karaikal","Mahe","Puducherry","Yanam"],
}

# Fallback dummy markets (used only when model can't find results)
DUMMY_MARKETS = [
    ("Azadpur",    "Delhi",       "North West Delhi"),
    ("Lasalgaon",  "Maharashtra", "Nashik"),
    ("Vashi",      "Maharashtra", "Navi Mumbai"),
    ("Kothi",      "Punjab",      "Amritsar"),
    ("Bowenpally", "Telangana",   "Hyderabad"),
]

# =============================================================================
# DISTRICT NORMALISATION + STATE CROPS  — identical to sms_handler.py
# =============================================================================
DISTRICT_ALIASES = {
    "ananthapur": "Anantapur", "karim nagar": "Karimnagar",
    "k.v.rangareddy": "Rangareddi", "visakhapatnam": "Vishakhapatnam",
    "dhubri": "Dhuburi", "mammit": "Mamit",
    "east champaran": "Purba Champaran", "west champaran": "Pashchim Champaran",
    "kaimur (bhabua)": "Bhabua", "palamau": "Palamu", "arwal": "Jehanabad",
    "bijapur(cgh)": "Bijapur",
    "central delhi": "Delhi", "east delhi": "Delhi", "new delhi": "Delhi",
    "north delhi": "Delhi", "north west delhi": "Delhi", "south delhi": "Delhi",
    "south west delhi": "Delhi", "west delhi": "Delhi",
    "ahmedabad": "Ahmadabad", "ahmed nagar": "Ahmednagar",
    "banaskantha": "Banas Kantha", "gandhi nagar": "Gandhinagar",
    "sabarkantha": "Sabar Kantha", "surendra nagar": "Surendranagar",
    "bilaspur (hp)": "Bilaspur", "hamirpur(hp)": "Hamirpur",
    "lahul & spiti": "Lahul And Spiti",
    "ananthnag": "Anantnag (Kashmir South)", "baramulla": "Baramula (Kashmir North)",
    "poonch": "Punch", "reasi": "Rajauri",
    "giridh": "Giridih", "khunti": "Ranchi", "ramgarh": "Ranchi",
    "seraikela-kharsawan": "Saraikela Kharsawan",
    "east singhbhum": "Purba Singhbhum", "west singhbhum": "Pashchim Singhbhum",
    "bangalore": "Bangalore Urban", "chickmagalur": "Chikmagalur",
    "chikkaballapur": "Chikmagalur", "dakshina kannada": "Dakshin Kannad",
    "davangere": "Davanagere", "ramanagar": "Bangalore Rural",
    "krishnagiri": "Dharmapuri", "uttara kannada": "Uttar Kannand",
    "yadgir": "Gulbarga", "bijapur(kar)": "Bijapur",
    "kasargod": "Kasaragod", "pathanamthitta": "Pattanamtitta",
    "alirajpur": "Jhabua", "ashok nagar": "Ashoknagar", "budaun": "Badaun",
    "khargone": "East Nimar", "rajnandgaon": "Raj Nandgaon", "singrauli": "Sidhi",
    "aurangabad(bh)": "Aurangabad", "beed": "Bid", "buldhana": "Buldana",
    "gadchiroli": "Garhchiroli", "gondia": "Gondiya",
    "mumbai": "Greater Bombay", "raigarh(mh)": "Raigarh",
    "imphal east": "East Imphal", "imphal west": "West Imphal",
    "ri bhoi": "Ri-Bhoi",
    "kiphire": "Tuensang", "longleng": "Mokokchung", "peren": "Kohima",
    "balangir": "Bolangir", "baleswar": "Baleshwar", "bargarh": "Baragarh",
    "debagarh": "Deogarh", "jagatsinghapur": "Jagatsinghpur",
    "jajapur": "Jajpur", "kendujhar": "Keonjhar", "khorda": "Khordha",
    "nabarangapur": "Nabarangpur", "sonapur": "Sonepur", "sundergarh": "Sundargarh",
    "pondicherry": "Puducherry",
    "nawanshahr": "Nawan Shehar", "ropar": "Rupnagar",
    "chittorgarh": "Chittaurgarh", "dholpur": "Dhaulpur", "jhujhunu": "Jhunjhunun",
    "tiruchirappalli": "Tiruchchirappalli", "tiruchirapalli": "Tiruchchirappalli",
    "tiruchi": "Tiruchchirappalli", "trichy": "Tiruchchirappalli",
    "tirunelveli": "Tirunelveli Kattabo", "tiruvallur": "Thiruvallur",
    "tiruvarur": "Thiruvarur", "kancheepuram": "Kancheepuram",
    "kanchipuram": "Kancheepuram", "the nilgiris": "Nilgiris",
    "tuticorin": "Thoothukudi", "kanyakumari": "Kanniyakumari",
    "chengalpattu": "Kancheepuram", "ranipet": "Vellore", "tiruppur": "Tirupur",
    "barabanki": "Bara Banki", "bagpat": "Baghpat", "raebareli": "Rae Bareli",
    "sant ravidas nagar": "Sant Ravi Das Nagar", "siddharthnagar": "Siddharth Nagar",
    "shrawasti": "Shravasti", "kanpur nagar": "Kanpur", "kheri": "Lakhimpur Kheri",
    "dehradun": "Dehra Dun", "nainital": "Naini Tal", "rudraprayag": "Rudra Prayag",
    "bardhaman": "Barddhaman", "howrah": "Haora", "malda": "Maldah",
    "north dinajpur": "Uttar Dinajpur", "south dinajpur": "Dakshin Dinajpur",
    "sonipat": "Sonepat",
    "dadra & nagar haveli": "Dadra And Nagar Haveli",
    "lakshadweep": "Kavaratti", "east sikkim": "East",
    "dibang valley": "Upper Dibang Valley", "bilaspur(cgh)": "Bilaspur",
}


def normalize_district(raw: str) -> str:
    """
    Corrects known spelling mismatches for centroid lookup.
    Returns the corrected district name, or raw.title() if no alias.
    Never returns None — all districts are accepted.
    Identical logic to sms_handler.py.
    """
    key = raw.strip().lower()
    if key in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[key]
    return raw.strip().title()


# Per-state crop availability (same as sms_handler.py)
STATE_CROPS = {
    "Andhra Pradesh":    ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Assam":             ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Bihar":             ["Onion", "Potato", "Tomato", "Wheat"],
    "Chandigarh":        ["Onion", "Potato", "Tomato"],
    "Chhattisgarh":      ["Onion", "Potato", "Tomato", "Wheat"],
    "Delhi":             ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Goa":               ["Potato"],
    "Gujarat":           ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Haryana":           ["Onion", "Potato", "Tomato", "Wheat"],
    "Himachal Pradesh":  ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Jammu And Kashmir": ["Onion", "Potato", "Tomato"],
    "Karnataka":         ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Kerala":            ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Madhya Pradesh":    ["Onion", "Potato", "Tomato", "Wheat"],
    "Maharashtra":       ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Manipur":           ["Onion", "Potato", "Rice"],
    "Meghalaya":         ["Onion", "Potato", "Tomato"],
    "Nagaland":          ["Onion", "Potato", "Tomato"],
    "Odisha":            ["Onion", "Potato", "Rice", "Tomato"],
    "Punjab":            ["Onion", "Potato", "Tomato", "Wheat"],
    "Rajasthan":         ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Tamil Nadu":        ["Onion", "Potato"],
    "Tripura":           ["Onion"],
    "Uttar Pradesh":     ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
    "Uttarakhand":       ["Onion", "Potato", "Rice", "Wheat"],
    "West Bengal":       ["Onion", "Potato", "Rice", "Tomato", "Wheat"],
}


def get_crops_for_state(state: str) -> list:
    """Returns available crops for a state. Falls back to all CROPS."""
    return STATE_CROPS.get(state.strip().title(), CROPS)

# =============================================================================
# CSS
# =============================================================================
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Nunito+Sans:wght@300;400;500;600;700&display=swap');

    html, body, .stApp {{
        background-color: {BG_OFFWHITE};
        font-family: 'Nunito Sans', sans-serif;
        color: {TEXT_DARK};
    }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* ── Widget labels & inputs — always dark ─────────────────── */
    .stTextInput > label, .stNumberInput > label,
    .stSelectbox > label, .stMultiSelect > label, .stSlider > label {{
        color: {TEXT_DARK} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }}
    .stTextInput input, .stNumberInput input {{
        color: {TEXT_DARK} !important;
        background: #FFFFFF !important;
        border: 1px solid {BORDER} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.9rem !important;
        border-radius: 4px !important;
    }}
    .stTextInput input::placeholder, .stNumberInput input::placeholder {{
        color: #AAAAAA !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        background: #FFFFFF !important;
        border: 1px solid {BORDER} !important;
        border-radius: 4px !important;
    }}
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[class] {{
        color: {TEXT_DARK} !important;
        background: transparent !important;
    }}
    [data-baseweb="popover"] li, [data-baseweb="menu"] li {{
        color: {TEXT_DARK} !important; background: white !important;
    }}
    [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {{
        background: {BG_OFFWHITE} !important;
    }}
    .stNumberInput button {{
        color: {TEXT_DARK} !important; background: {BG_OFFWHITE} !important;
        border-color: {BORDER} !important;
    }}
    .stMarkdown, .stMarkdown p, .stMarkdown span {{ color: {TEXT_DARK}; }}

    /* ── Nav ───────────────────────────────────────────────────── */
    .nav-bar {{
        background: {GREEN}; display: flex; align-items: center;
        justify-content: space-between; padding: 0 48px; height: 64px;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }}
    .nav-logo {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.5rem; font-weight: 700; color: white;
    }}
    .nav-logo span {{ color: {AMBER}; }}
    .nav-links {{ display: flex; gap: 32px; align-items: center; }}
    .nav-links a {{
        color: rgba(255,255,255,0.85); font-size: 0.88rem; font-weight: 600;
        letter-spacing: 0.04em; text-decoration: none; text-transform: uppercase;
    }}
    .nav-cta {{
        background: {AMBER}; color: {GREEN} !important;
        padding: 8px 20px; border-radius: 3px; font-weight: 700 !important;
    }}

    /* ── Hero ──────────────────────────────────────────────────── */
    .hero-section {{
        position: relative; width: 100%; height: 480px;
        overflow: hidden; background: {GREEN};
    }}
    .hero-bg {{
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=1600&q=80&fit=crop');
        background-size: cover; background-position: center 40%; opacity: 0.5;
    }}
    .hero-content {{
        position: relative; z-index: 2; padding: 72px 80px; max-width: 620px;
    }}
    .hero-eyebrow {{
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: {AMBER}; margin-bottom: 14px;
    }}
    .hero-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 3.4rem; font-weight: 900; color: white;
        line-height: 1.12; margin-bottom: 18px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    }}
    .hero-title em {{ color: {AMBER}; font-style: normal; }}
    .hero-desc {{
        font-size: 1.0rem; color: rgba(255,255,255,0.88);
        line-height: 1.7; margin-bottom: 24px; max-width: 460px;
    }}
    .hero-cta-btn {{
        display: inline-block; background: {AMBER}; color: {GREEN} !important;
        font-family: 'Nunito Sans', sans-serif; font-weight: 700;
        font-size: 0.95rem; letter-spacing: 0.06em; text-transform: uppercase;
        text-decoration: none; padding: 14px 32px; border-radius: 4px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25); transition: background 0.2s;
    }}
    .hero-cta-btn:hover {{ background: {AMBER_DARK} !important; color: white !important; }}

    /* ── Section headings ──────────────────────────────────────── */
    .section-eyebrow {{
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: {GREEN_LIGHT};
        margin-bottom: 10px; text-align: center;
    }}
    .section-eyebrow.dark {{ color: {AMBER}; }}
    .section-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.2rem; font-weight: 700; color: {GREEN};
        line-height: 1.2; margin-bottom: 12px; text-align: center;
    }}
    .section-title.white {{ color: white; }}
    .section-sub {{
        font-size: 1.0rem; color: {TEXT_MUTED}; text-align: center;
        max-width: 560px; margin: 0 auto 32px; line-height: 1.7;
    }}
    .section-sub.white {{ color: rgba(255,255,255,0.75); }}

    /* ── Feature cards ─────────────────────────────────────────── */
    .feat-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 24px; }}
    .feat-card {{
        background: white; border-radius: 6px; overflow: hidden;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08); position: relative;
    }}
    .feat-card img {{ width: 100%; height: 150px; object-fit: cover; }}
    .feat-icon-circle {{
        position: absolute; top: 127px; left: 50%; transform: translateX(-50%);
        width: 44px; height: 44px; border-radius: 50%; background: {GREEN};
        border: 3px solid white; display: flex; align-items: center;
        justify-content: center; font-size: 17px; z-index: 2;
    }}
    .feat-card-body {{ padding: 32px 18px 20px; text-align: center; }}
    .feat-card-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.0rem; font-weight: 700; color: {GREEN}; margin-bottom: 7px;
    }}
    .feat-card-desc {{ font-size: 0.84rem; color: {TEXT_MUTED}; line-height: 1.6; }}

    /* ── Form section (green bg) ───────────────────────────────── */
    div.stButton > button {{
        background: {AMBER} !important; color: {GREEN} !important;
        font-family: 'Nunito Sans', sans-serif !important; font-weight: 700 !important;
        letter-spacing: 0.06em !important; text-transform: uppercase !important;
        border: none !important; border-radius: 4px !important;
        padding: 0.65rem 2rem !important; font-size: 0.88rem !important; width: 100% !important;
    }}
    div.stButton > button:hover {{
        background: {AMBER_DARK} !important; color: white !important;
    }}

    /* ── Results ───────────────────────────────────────────────── */
    .results-header {{ background: {BG_OFFWHITE}; padding: 40px 80px 12px; }}
    .results-body   {{ background: {BG_OFFWHITE}; padding: 0 80px 60px; }}

    /* ── Metric card ───────────────────────────────────────────── */
    .mc {{
        background: white; border-top: 4px solid {GREEN}; border-radius: 4px;
        padding: 20px 18px 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    .mc.amber {{ border-top-color: {AMBER_DARK}; }}
    .mc.red   {{ border-top-color: #E53E3E; }}
    .mc-lbl {{
        font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 8px;
    }}
    .mc-val {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.9rem; font-weight: 600; color: {GREEN}; line-height: 1;
    }}
    .mc.amber .mc-val {{ color: {AMBER_DARK}; }}
    .mc.red   .mc-val {{ color: #E53E3E; }}
    .mc-unit {{ font-size: 0.7rem; color: {TEXT_MUTED}; margin-top: 5px; }}

    /* ── Section divider label ─────────────────────────────────── */
    .sec-lbl {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: {TEXT_MUTED};
        border-bottom: 1px solid {BORDER}; padding-bottom: 6px; margin: 32px 0 14px;
    }}

    /* ── Recommendation box ────────────────────────────────────── */
    .reco-box {{
        background: {GREEN}; color: white; border-radius: 4px;
        padding: 22px 28px; margin-top: 14px; font-size: 1.0rem; line-height: 1.7;
    }}
    .reco-box strong {{ font-weight: 700; color: {AMBER}; }}
    .reco-lbl {{
        font-size: 0.66rem; letter-spacing: 0.12em; text-transform: uppercase;
        opacity: 0.6; margin-bottom: 8px;
    }}

    /* ── Spinner / info ────────────────────────────────────────── */
    .loading-box {{
        background: white; border-radius: 6px; padding: 32px;
        text-align: center; font-size: 1.1rem; color: {TEXT_MUTED};
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}

    /* ── Footer ────────────────────────────────────────────────── */
    .site-footer {{
        background: {GREEN}; color: rgba(255,255,255,0.6);
        text-align: center; padding: 22px 48px; font-size: 0.8rem;
    }}
    .site-footer strong {{ color: white; }}

    /* ── Table ─────────────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER} !important; border-radius: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# DUMMY DATA (fallback only)
# =============================================================================
def make_dummy_df(commodity="Onion", quantity_kg=500):
    random.seed(42)
    rows = []
    for market, state, district in DUMMY_MARKETS:
        dist_km       = random.randint(20, 150)
        price_per_q   = random.randint(1200, 3500)
        qty_q         = quantity_kg / 100
        gross_revenue = round(price_per_q * qty_q, 2)
        transport     = round(dist_km * 15 + 300, 2)
        mandi_fee     = round(gross_revenue * 0.02, 2)
        misc_costs    = round(qty_q * 10, 2)
        total_costs   = round(transport + mandi_fee + misc_costs, 2)
        net_profit    = round(gross_revenue - total_costs, 2)
        profit_per_kg = round(net_profit / quantity_kg, 2)
        rows.append({
            "market": market, "state": state, "district": district,
            "distance_km": dist_km, "predicted_price": price_per_q,
            "gross_revenue": gross_revenue, "transport_cost": transport,
            "mandi_fee": mandi_fee, "misc_costs": misc_costs,
            "total_costs": total_costs, "net_profit": net_profit,
            "profit_per_kg": profit_per_kg,
        })
    return sorted(rows, key=lambda x: x["net_profit"], reverse=True)


# =============================================================================
# MODEL CALL
# =============================================================================
def get_recommendations(commodity, quantity_kg, district, state, month_num, year):
    """Call real model; fall back to dummy on any error."""
    try:
        from recommender import recommend
        results = recommend(
            commodity        = commodity,
            quantity_kg      = quantity_kg,
            farmer_district  = district,
            farmer_state     = state,
            target_month     = month_num,
            target_year      = year,
            max_distance_km  = 200,         # hardcoded 200, same as SMS
            top_n            = 3,            # same as SMS
        )
        if results and len(results) > 0:
            return results, False   # (data, is_dummy)
        # Model ran but found 0 markets — not a crash, just no results
        return [], False
    except Exception as e:
        st.session_state["model_error"] = str(e)
        return make_dummy_df(commodity, quantity_kg), True


# =============================================================================
# CHARTS
# =============================================================================
def _fig_to_img(fig):
    """Convert a matplotlib Figure to a PNG bytes buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130)
    buf.seek(0)
    plt.close(fig)
    return buf


def profit_bar_chart(records):
    """Horizontal bar — Net Profit per market, best highlighted (Matplotlib)."""
    pairs = sorted(zip(
        [r["net_profit"] for r in records],
        [r["market"]    for r in records],
    ))
    profits_s = [p for p, _ in pairs]
    markets_s = [m for _, m in pairs]
    colors_s  = [AMBER_DARK if m == records[0]["market"] else GREEN_LIGHT
                 for m in markets_s]

    fig, ax = plt.subplots(figsize=(7, max(2.5, len(markets_s) * 0.45)))
    bars = ax.barh(markets_s, profits_s, color=colors_s, edgecolor="none", height=0.55)
    for bar, val in zip(bars, profits_s):
        ax.text(bar.get_width() + max(profits_s) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"Rs. {val:,.0f}", va="center", ha="left", fontsize=8, color=TEXT_DARK)
    ax.set_xlabel("Net Profit (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="both", labelsize=8, colors=TEXT_DARK)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def cost_waterfall_chart(best):
    """Waterfall: Gross Revenue → costs → Net Profit (Matplotlib)."""
    labels  = ["Gross\nRevenue", "Transport", "Mandi Fee", "Misc", "Net Profit"]
    amounts = [
        best["gross_revenue"],
        -best["transport_cost"],
        -best["mandi_fee"],
        -best["misc_costs"],
        best["net_profit"],
    ]
    bottoms, running = [], 0
    for i, a in enumerate(amounts):
        if i == 0 or i == len(amounts) - 1:
            bottoms.append(0)
        else:
            bottoms.append(running)
        if i < len(amounts) - 1:
            running += a

    bar_colors = []
    for i, a in enumerate(amounts):
        if i == 0:
            bar_colors.append(GREEN_LIGHT)
        elif i == len(amounts) - 1:
            bar_colors.append(GREEN)
        else:
            bar_colors.append(AMBER_DARK if a < 0 else GREEN_LIGHT)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(labels, [abs(a) for a in amounts], bottom=bottoms,
                  color=bar_colors, edgecolor="none", width=0.5)
    for bar, val in zip(bars, amounts):
        sign = "-" if val < 0 else ""
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_y() + bar.get_height() + max(abs(a) for a in amounts) * 0.01,
                f"{sign}Rs.{abs(val):,.0f}", ha="center", va="bottom", fontsize=7, color=TEXT_DARK)
    ax.set_ylabel("Amount (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="both", labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def cost_pie_chart(best):
    """Donut: how the gross revenue is split (Matplotlib)."""
    labels = ["Net Profit", "Transport", "Mandi Fee", "Misc"]
    values = [max(best["net_profit"], 0),
              best["transport_cost"], best["mandi_fee"], best["misc_costs"]]
    colors = [GREEN, AMBER_DARK, GREEN_LIGHT, "#C5BFB0"]
    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    def autopct_fn(pct):
        return f"{pct:.0f}%" if pct >= 5 else ""

    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors, autopct=autopct_fn,
        pctdistance=0.75, startangle=90,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.legend(labels, loc="center right", bbox_to_anchor=(1.3, 0.5),
              fontsize=8, frameon=False)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def price_comparison_chart(records):
    """Bar — Predicted price per quintal across markets (Matplotlib)."""
    markets = [r["market"] for r in records]
    prices  = [r["predicted_price"] for r in records]
    colors  = [AMBER if i == 0 else GREEN_MID for i in range(len(records))]

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.bar(markets, prices, color=colors, edgecolor="none", width=0.55)
    for bar, val in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(prices) * 0.01,
                f"Rs.{val:,.0f}", ha="center", va="bottom", fontsize=7, color=TEXT_DARK)
    ax.set_ylabel("Price (Rs./quintal)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="x", labelsize=7, rotation=20, colors=TEXT_DARK)
    ax.tick_params(axis="y", labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def distance_vs_profit_scatter(records):
    """Scatter: distance vs net profit — bubble sized by price (Matplotlib)."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for i, r in enumerate(records):
        is_best = (i == 0)
        size = max(r["predicted_price"] / 30, 80)
        color = AMBER_DARK if is_best else GREEN_LIGHT
        ax.scatter(r["distance_km"], r["net_profit"], s=size, color=color,
                   edgecolors="white", linewidths=1.5, zorder=3, alpha=0.9)
        ax.annotate(r["market"],
                    xy=(r["distance_km"], r["net_profit"]),
                    xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=7, color=TEXT_DARK)
    ax.set_xlabel("Distance from your district (km)", fontsize=8, color=TEXT_MUTED)
    ax.set_ylabel("Net Profit (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("#FAFAF8")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


# =============================================================================
# STYLED TABLE
# =============================================================================
def style_table(records):
    rows = []
    for r in records:
        rows.append({
            "Market":           r["market"],
            "State":            r["state"],
            "Dist. (km)":       r["distance_km"],
            "Price (Rs./q)":    r["predicted_price"],
            "Transport (Rs.)":  r["transport_cost"],
            "Net Profit (Rs.)": r["net_profit"],
            "Profit/kg (Rs.)":  r["profit_per_kg"],
        })
    df = pd.DataFrame(rows)
    # Format numeric columns as strings for display (no jinja2 needed)
    df["Price (Rs./q)"]    = df["Price (Rs./q)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Transport (Rs.)"] = df["Transport (Rs.)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Net Profit (Rs.)"] = df["Net Profit (Rs.)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Profit/kg (Rs.)"] = df["Profit/kg (Rs.)"].apply(lambda x: f"Rs. {x:.2f}")
    df["Dist. (km)"]       = df["Dist. (km)"].apply(lambda x: f"{x:.0f} km")
    return df


# =============================================================================
# STATIC SECTIONS
# =============================================================================
def render_navbar():
    st.markdown(f"""
    <div class="nav-bar">
        <div class="nav-logo">Fasal<span>-to-</span>Faida</div>
        <div class="nav-links">
            <a href="#">About</a>
            <a href="#">How It Works</a>
            <a href="#">Mandis</a>
            <a href="#" class="nav-cta">Check My Mandi</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-bg"></div>
        <div class="hero-content">
            <div class="hero-eyebrow">AI-Powered Market Intelligence</div>
            <div class="hero-title">Smarter Selling<br>for Every<br><em>Indian Farmer</em></div>
            <div class="hero-desc">
                Our XGBoost model predicts crop prices at every mandi near you,
                then calculates real transport costs and net profit — so you always
                know where to sell before you load the truck.
            </div>
            <a href="#check-your-best-mandi" class="hero-cta-btn">🌾 Check My Mandi</a>
        </div>
    </div>
    <div style="background:{AMBER};height:5px;width:100%;"></div>
    """, unsafe_allow_html=True)


def render_features_section():
    st.markdown(f"""
    <div style="background:{BG_WHITE};padding:56px 72px;">
        <div class="section-eyebrow">What We Offer</div>
        <div class="section-title">Four Numbers That Change Everything</div>
        <div class="section-sub">
            One query. Real XGBoost predictions. Ranked by actual net profit after all costs.
        </div>
        <div class="feat-grid">
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1607457561901-e6ec3a6d16cf?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">📈</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Price Prediction</div>
                    <div class="feat-card-desc">XGBoost model trained on 2 years of Agmarknet data predicts the expected modal price for your crop.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">🏆</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Best Mandi Rank</div>
                    <div class="feat-card-desc">We evaluate every reachable mandi and rank them by net profit — not just advertised price.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">🚚</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Transport Cost</div>
                    <div class="feat-card-desc">Haversine distance × 1.3 road correction, then tiered truck rates based on your load size.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">💰</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Net Profit Estimate</div>
                    <div class="feat-card-desc">Gross revenue minus transport, 2% mandi commission, and misc costs — your real take-home.</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# FORM SECTION
# =============================================================================
def render_form_section():
    # Anchor target so the hero CTA can link here
    st.markdown("""
    <div id="check-your-best-mandi" style="scroll-margin-top:70px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{GREEN};padding:60px 100px 0 100px;">
        <div class="section-eyebrow dark">Find Your Market</div>
        <div class="section-title white" style="font-size:2.8rem;">Check Your Best Mandi</div>
        <div class="section-sub white" style="font-size:1.05rem;max-width:680px;">
            Enter your 6-digit pincode and crop details — our XGBoost model instantly
            evaluates every reachable mandi and ranks them by real net profit after all costs.
        </div>
    </div>
    <div style="background:{GREEN};padding:16px 100px 56px 100px;">
    """, unsafe_allow_html=True)

    # Row 1: name + pincode + crop
    c1, c2, c3 = st.columns([2.5, 2.5, 2])
    with c1:
        farmer_name = st.text_input("Farmer Name (optional)", placeholder="e.g. Ramesh Patil", key="fname")
    with c2:
        pincode = st.text_input(
            "Your Pincode *",
            placeholder="e.g. 641001",
            max_chars=6,
            key="pincode"
        )
    with c3:
        commodity = st.selectbox("Crop *", CROPS, index=1, key="crop")

    # Row 2 — same inputs as SMS: qty bucket + month + submit
    #   QTY_MAP {1:250, 2:750, 3:2500, 4:6000}  (identical to sms_handler.py)
    QTY_OPTIONS = {
        "1 — Below 500 kg  (250 kg)": 250,
        "2 — 500-1000 kg   (750 kg)": 750,
        "3 — 1000-5000 kg (2500 kg)": 2500,
        "4 — Above 5000 kg (6000 kg)": 6000,
    }
    c4, c5, c6 = st.columns([2.5, 2.5, 1.8])
    with c4:
        qty_label  = st.selectbox("Quantity *", list(QTY_OPTIONS.keys()), index=1, key="qty")
        quantity_kg = QTY_OPTIONS[qty_label]
    with c5:
        month_name = st.selectbox("Month to Sell *", MONTHS,
                                  index=pd.Timestamp.now().month - 1, key="mon")
    with c6:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submitted = st.button("🔍 Find Best Mandi", key="submit")

    st.markdown("</div>", unsafe_allow_html=True)

    return {
        "farmer_name": farmer_name.strip() if farmer_name else "",
        "commodity":   commodity,
        "quantity_kg": quantity_kg,          # 250 / 750 / 2500 / 6000
        "pincode":     pincode.strip() if pincode else "",
        "month_num":   MONTHS.index(month_name) + 1,
        "month_name":  month_name,
        "year":        pd.Timestamp.now().year,   # always current year, same as SMS
        "submitted":   submitted,
    }


# =============================================================================
# METRIC CARD HTML
# =============================================================================
def mc(label, value, unit="", variant=""):
    cls = f"mc {variant}".strip()
    return f"""<div class="{cls}">
        <div class="mc-lbl">{label}</div>
        <div class="mc-val">{value}</div>
        <div class="mc-unit">{unit}</div>
    </div>"""


# =============================================================================
# RESULTS SECTION
# =============================================================================
def render_results(inputs):
    pincode = inputs["pincode"]

    # ── Validate pincode ───────────────────────────────────────────
    import re as _re
    if not pincode:
        st.warning("⚠️ Please enter your 6-digit pincode.")
        return
    if not _re.fullmatch(r"\d{6}", pincode):
        st.warning("⚠️ Pincode must be exactly 6 digits. Example: 641001")
        return

    # ── Resolve pincode → raw district + state ───────────────────
    from recommender import lookup_pincode
    loc = lookup_pincode(pincode)
    if not loc["valid"]:
        st.warning(
            f"⚠️ Pincode **{pincode}** was not found in our database. "
            "Please double-check and try again."
        )
        return

    raw_district = loc["district"]   # e.g. 'COIMBATORE' / 'Nashik'
    state        = loc["state"]      # e.g. 'Tamil Nadu'

    # ── Normalise district name (same as sms_handler.py) ──────────
    #   Fixes CSV spelling mismatches before passing to recommend()
    district = normalize_district(raw_district)

    # Show resolved location
    st.info(f"📍 **{district}, {state}** (pincode {pincode})")

    # ── Loading spinner ────────────────────────────────────────────
    with st.spinner(f"🔍 Evaluating mandis for {inputs['commodity']} near {district}…"):
        records, is_dummy = get_recommendations(
            inputs["commodity"], inputs["quantity_kg"],
            district, state,
            inputs["month_num"], inputs["year"],
        )

    if not records:
        st.markdown(f"""
        <div style="background:{BG_OFFWHITE};padding:40px 80px;">
            <div style="background:white;border-radius:4px;padding:32px;text-align:center;color:{TEXT_MUTED};">
                <b>No markets found</b> within 200 km of <b>{district}, {state}</b>.<br><br>
                Try a different crop or month that is traded near your region.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    best = records[0]
    name_str = f"Namaste {inputs['farmer_name']} — " if inputs["farmer_name"] else ""

    # ── Dummy data notice ──────────────────────────────────────────
    if is_dummy:
        err_detail = st.session_state.get("model_error", "unknown error")
        st.error(
            f"⚠️ Model failed — showing illustrative data only.\n\n"
            f"**Error:** `{err_detail}`\n\n"
            f"District passed to model: `{district}` · State: `{state}`"
        )

    # ── Results header ─────────────────────────────────────────────
    st.markdown(f"""
    <div class="results-header">
        <div class="section-eyebrow">Market Intelligence Report</div>
        <div class="section-title" style="text-align:left;font-size:1.9rem;">
            {name_str}Best Mandis for <em style="color:{AMBER_DARK}">{inputs['commodity']}</em>
        </div>
        <div style="font-size:0.85rem;color:{TEXT_MUTED};margin-top:4px;">
            {inputs['quantity_kg']} kg &nbsp;·&nbsp; {district}, {state}
            &nbsp;·&nbsp; {inputs['month_name']} {inputs['year']}
            &nbsp;·&nbsp; Within 200 km
            &nbsp;·&nbsp; {len(records)} markets found
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='results-body'>", unsafe_allow_html=True)

    # ── KPI cards ──────────────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Top Market — At a Glance</div>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(mc("Best Mandi", best["market"], best["state"]), unsafe_allow_html=True)
    with k2:
        st.markdown(mc("Predicted Price",
                       f"Rs. {best['predicted_price']:,.0f}", "per quintal"), unsafe_allow_html=True)
    with k3:
        st.markdown(mc("Gross Revenue",
                       f"Rs. {best['gross_revenue']:,.0f}",
                       f"for {inputs['quantity_kg']} kg"), unsafe_allow_html=True)
    with k4:
        st.markdown(mc("Total Costs",
                       f"Rs. {best['total_costs']:,.0f}",
                       "transport + fees", "red"), unsafe_allow_html=True)
    with k5:
        st.markdown(mc("Net Profit",
                       f"Rs. {best['net_profit']:,.0f}",
                       f"Rs. {best['profit_per_kg']:.2f}/kg", "amber"), unsafe_allow_html=True)

    # ── Cost breakdown row ─────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Cost Breakdown — Best Market</div>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown(mc("Transport Cost",
                       f"Rs. {best['transport_cost']:,.0f}",
                       f"{best['distance_km']} km road distance"), unsafe_allow_html=True)
    with b2:
        st.markdown(mc("Mandi Commission",
                       f"Rs. {best['mandi_fee']:,.0f}", "2% of gross"), unsafe_allow_html=True)
    with b3:
        st.markdown(mc("Misc. Costs",
                       f"Rs. {best['misc_costs']:,.0f}", "handling + misc"), unsafe_allow_html=True)
    with b4:
        st.markdown(mc("Profit/kg",
                       f"Rs. {best['profit_per_kg']:.2f}", "net per kg"), unsafe_allow_html=True)

    # ── Charts row 1: Waterfall + Pie ─────────────────────────────
    st.markdown("<div class='sec-lbl'>Profit Waterfall & Cost Split — Best Market</div>",
                unsafe_allow_html=True)
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Revenue → Costs → Net Profit</p>", unsafe_allow_html=True)
        st.image(cost_waterfall_chart(best), width="content")
    with ch2:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Where Does Your Money Go?</p>", unsafe_allow_html=True)
        st.image(cost_pie_chart(best), width="content")

    # ── Charts row 2: Bar (profit) + Bar (price) ──────────────────
    st.markdown("<div class='sec-lbl'>All Markets Compared</div>", unsafe_allow_html=True)
    ch3, ch4 = st.columns(2)
    with ch3:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Net Profit by Market (Rs.)</p>", unsafe_allow_html=True)
        st.image(profit_bar_chart(records), width="content")
    with ch4:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Predicted Price per Quintal (Rs.)</p>", unsafe_allow_html=True)
        st.image(price_comparison_chart(records), width="content")

    # ── Scatter: distance vs profit ────────────────────────────────
    st.markdown("<div class='sec-lbl'>Distance vs Profit Trade-off</div>",
                unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                f"Bubble size = predicted price. Orange = best choice.</p>",
                unsafe_allow_html=True)
    st.image(distance_vs_profit_scatter(records), width="content")

    # ── Ranked table ───────────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Full Market Rankings</div>", unsafe_allow_html=True)
    st.dataframe(style_table(records), use_container_width=True, hide_index=True)

    # ── Recommendation summary (SMS-style ranked list) ─────────────
    qty_kg = inputs["quantity_kg"]
    # Build SMS-style market lines for top markets (same format as sms_handler.py)
    top_markets = records[:3]
    market_lines = ""
    for i, r in enumerate(top_markets, 1):
        market_lines += (
            f'<div style="margin-bottom:14px;">'
            f'<div style="font-size:1.05rem;font-weight:700;color:{AMBER};">{i}. {r["market"]}</div>'
            f'<div style="font-size:0.92rem;margin-top:3px;">'
            f'Rs.{r["predicted_price"]:,.0f}/qtl'
            f' &nbsp;·&nbsp; Transport: Rs.{r["transport_cost"]:,.0f}'
            f' &nbsp;·&nbsp; Net: <strong>Rs.{r["net_profit"]:,.0f}</strong>'
            f' &nbsp;(Rs.{r["profit_per_kg"]:.1f}/kg)'
            f'</div></div>'
        )

    st.markdown(f"""
    <div class="reco-box">
        <div class="reco-lbl">Fasal-to-Faida Results</div>
        <div style="font-size:1.0rem;font-weight:600;margin-bottom:4px;">
            {inputs['commodity']} &nbsp;|&nbsp; {qty_kg} kg
        </div>
        <div style="font-size:0.85rem;opacity:0.75;margin-bottom:18px;">
            Sell: {inputs['month_name']} {inputs['year']} &nbsp;|&nbsp; {district}, {state}
        </div>
        {market_lines}
        <div style="font-size:0.78rem;opacity:0.6;margin-top:6px;">
            Send #PINCODE via SMS to query from your phone
        </div>
    </div>
    <p style='font-size:0.72rem;color:{TEXT_MUTED};margin-top:10px;'>
    Prices predicted by XGBoost model trained on Agmarknet data (2023–2024).
    Transport costs use haversine × 1.3 road factor with tiered truck rates.
    Results are indicative and actual prices may vary.
    </p>
    """, unsafe_allow_html=True)

    # ── AI Summary (featherless.ai) ────────────────────────────────
    # Read the key directly from secrets every run — no sidebar dependency
    api_key = ""
    try:
        api_key = st.secrets["featherless"]["api_key"]
    except Exception:
        pass
    # Also allow sidebar override (set by user if they want to swap keys)
    api_key = st.session_state.get("featherless_key", api_key) or api_key

    if api_key:
        with st.spinner("🤖 Generating AI summary…"):
            from llm_summary import generate_summary
            summary, err = generate_summary(records, inputs, district, state, api_key)
        if summary:
            st.markdown(f"""
            <div style="background:#EDF7EE;border-left:5px solid {GREEN_MID};
                        border-radius:6px;padding:20px 26px;margin-top:16px;
                        box-shadow:0 2px 10px rgba(27,67,50,0.12);">
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.13em;
                            text-transform:uppercase;color:{GREEN_MID};margin-bottom:10px;">
                    🤖 AI Market Advisory
                </div>
                <div style="font-size:0.95rem;line-height:1.75;color:{TEXT_DARK};">{summary}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ AI summary unavailable: {err}")
    else:
        st.info("💬 AI Market Advisory unavailable — no API key found in secrets.toml.")

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================
def render_footer():
    st.markdown(f"""
    <div class="site-footer">
        <strong>Fasal-to-Faida</strong> &nbsp;|&nbsp; Bech Sahi, Kamaao Zyada &nbsp;|&nbsp;
        Powered by XGBoost · Agmarknet Data 
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================
def main():
    inject_css()

    # ── Featherless.ai sidebar status + optional key override ──────────
    secrets_key = ""
    try:
        secrets_key = st.secrets["featherless"]["api_key"]
    except Exception:
        pass
    with st.sidebar:
        st.markdown("### 🤖 AI Summary")
        if secrets_key:
            st.success("API key loaded from secrets ✓")
        override = st.text_input(
            "Override API Key (optional)",
            type="password",
            help="Leave blank to use the key from .streamlit/secrets.toml",
            key="_fl_key_input",
        )
        st.session_state["featherless_key"] = override.strip() if override.strip() else ""

    render_navbar()
    render_hero()
    render_features_section()
    inputs = render_form_section()
    if inputs["submitted"]:
        render_results(inputs)
    render_footer()


if __name__ == "__main__":
    main()