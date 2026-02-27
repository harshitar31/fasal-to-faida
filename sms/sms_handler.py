# sms_handler.py
# Fasal-to-Faida — SMS simulation via Twilio
# Registration: #PINCODE | Prediction: crop → month → qty → results

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
import re
import sys
import datetime
import csv

# ── Set working directory to project root so recommender's relative paths work ─
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT_ROOT)                          # datasets/, model/ now resolve
sys.path.insert(0, _PROJECT_ROOT)
from recommender import recommend
# ────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# ── File paths ───────────────────────────────────────────────────────────────
USERS_FILE    = "registered_users.json"
SESSIONS_FILE = "sessions.json"

# All 5 crops in display order (used as fallback)
ALL_CROPS = ["Tomato", "Onion", "Potato", "Wheat", "Rice"]

# Per-state crop availability — derived from clean_df.parquet
# Only crops with actual training data for that state are shown
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
    """Returns available crop list for a state. Falls back to ALL_CROPS."""
    key = state.strip().title()
    return STATE_CROPS.get(key, ALL_CROPS)

def build_crop_menu(crops: list) -> tuple:
    """
    Returns (menu_str, crop_map) where crop_map maps reply digit → crop name.
    Example: '1. Onion\n2. Potato', {'1': 'Onion', '2': 'Potato'}
    """
    crop_map = {str(i+1): c for i, c in enumerate(crops)}
    lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(crops))
    return lines, crop_map

QTY_MAP = {
    "1": 250,
    "2": 750,
    "3": 2500,
    "4": 6000
}
QTY_LABELS = {
    "1": "<500 kg",
    "2": "500-1000 kg",
    "3": "1000-5000 kg",
    "4": ">5000 kg"
}


# ── District name normalisation ───────────────────────────────────────────────
# Auto-derived by diffing 'india pincode final.csv' district names against
# 'district wise centroids.csv'. Covers all 26 states.
# Keys = lowercase pincode-CSV spelling → Value = exact centroid-CSV spelling.
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



def normalize_district(raw: str) -> str:
    """
    Corrects known spelling mismatches for centroid lookup.
    Returns the corrected district name, or raw.title() if no alias exists.
    Never returns None — all districts are accepted.
    """
    key = raw.strip().lower()
    if key in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[key]
    return raw.strip().title()



# ── Load pincode → district from local CSV (no network needed) ────────────────
_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datasets", "india pincode final.csv"
)

def _load_pincode_db(path: str) -> dict:
    """
    Reads 'india pincode final.csv' (columns: pincode, Taluk, Districtname, statename)
    and returns {pincode_str: (district, state)} for O(1) lookup.
    """
    db = {}
    try:
        with open(path, newline="", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pin  = str(row.get("pincode", "")).strip().zfill(6)
                dist = row.get("Districtname", "").strip()
                state = row.get("statename", "").strip().title()  # 'TAMIL NADU' → 'Tamil Nadu'
                if pin and dist:
                    db[pin] = (dist, state)
    except FileNotFoundError:
        print(f"[WARNING] Pincode DB not found at {path}. Pincode lookup will fail.")
    return db

PINCODE_DB = _load_pincode_db(_CSV_PATH)


# ── Pincode → District via local CSV ──────────────────────────────────────────
def pincode_to_district(pincode: str):
    """
    Returns (raw_district, state, normalized_district, error).
    - error: 'bad_pincode' | 'not_found' | None (success)
    Fully offline — uses PINCODE_DB loaded from local CSV at startup.
    """
    if not re.fullmatch(r"\d{6}", pincode):
        return None, None, None, "bad_pincode"
    result = PINCODE_DB.get(pincode)
    if result is None:
        return None, None, None, "not_found"
    raw_district, state = result
    normalized = normalize_district(raw_district)
    return raw_district, state, normalized, None


# ── JSON helpers ─────────────────────────────────────────────────────────────
def load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except json.JSONDecodeError:
            return {}  # file is empty or corrupted
    return {}

def save_json(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── SMS helper ────────────────────────────────────────────────────────────────
def send(msg: str) -> str:
    r = MessagingResponse()
    r.message(msg)
    return str(r)


# ── Main Twilio webhook ───────────────────────────────────────────────────────
@app.route("/sms", methods=["POST"])
def sms_reply():
    phone      = request.form.get("From", "").strip()
    body       = request.form.get("Body", "").strip()
    body_upper = body.upper()

    users    = load_json(USERS_FILE)
    sessions = load_json(SESSIONS_FILE)

    # ── 1. REGISTRATION / DISTRICT CHANGE via #PINCODE ───────────────────────
    if body.startswith("#"):
        pincode = body[1:].strip()
        raw_district, state, district, err = pincode_to_district(pincode)

        if err in ("bad_pincode", "not_found"):
            return send(
                "Invalid pincode.\n"
                "Send a valid 6-digit pincode.\n"
                "Example: #641001"
            )


        is_update = phone in users
        users[phone] = {
            "pincode":  pincode,
            "district": district,
            "state":    state
        }
        save_json(USERS_FILE, users)

        # Build crop menu for this state
        crops = get_crops_for_state(state)
        crop_menu, crop_map = build_crop_menu(crops)

        # Start crop session immediately so next reply goes to crop step
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)

        action = "Updated" if is_update else "Registered"
        return send(
            f"Fasal-to-Faida\n"
            f"{action}!\n"
            f"District: {district}, {state}\n\n"
            f"Select crop:\n"
            f"{crop_menu}\n\n"
            f"Reply with number."
        )

    # ── 2. HELP ───────────────────────────────────────────────────────────────
    if body_upper in ["HELP", "?"]:
        return send(
            "Fasal-to-Faida Help\n\n"
            "Register district:\n"
            "  #PINCODE (e.g. #641001)\n\n"
            "Get prediction:\n"
            "  Just text us\n\n"
            "Restart: MENU or HI"
        )

    # ── 3. RESET / MENU ───────────────────────────────────────────────────────
    if body_upper in ["MENU", "HI", "HELLO", "START", "RESET"]:
        sessions.pop(phone, None)
        save_json(SESSIONS_FILE, sessions)

        if phone not in users:
            return send(
                "Welcome to Fasal-to-Faida!\n\n"
                "Register your district:\n"
                "Send #PINCODE\n"
                "Example: #641001"
            )

        district = users[phone]["district"]
        state_u  = users[phone].get("state", "")
        crops = get_crops_for_state(state_u)
        crop_menu, crop_map = build_crop_menu(crops)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)
        return send(
            f"Fasal-to-Faida\n"
            f"District: {district}\n\n"
            f"Select crop:\n"
            f"{crop_menu}\n\n"
            f"Send #PINCODE to change district."
        )

    # ── 4. NEW USER — not registered, no session ──────────────────────────────
    if phone not in users and phone not in sessions:
        return send(
            "Welcome to Fasal-to-Faida!\n\n"
            "Register your district first.\n"
            "Send #PINCODE\n"
            "Example: #641001\n\n"
            "Send HELP for info."
        )

    # ── 5. REGISTERED USER — no active session → start crop menu ─────────────
    if phone not in sessions:
        district = users[phone]["district"]
        state_u  = users[phone].get("state", "")
        crops = get_crops_for_state(state_u)
        crop_menu, crop_map = build_crop_menu(crops)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)
        return send(
            f"Fasal-to-Faida | {district}\n\n"
            f"Select crop:\n"
            f"{crop_menu}"
        )

    # ── 6. ACTIVE SESSION — menu steps ───────────────────────────────────────
    session = sessions[phone]
    step    = session.get("step", "crop")

    # Step: crop
    if step == "crop":
        crop_map = session.get("crop_map") or {}
        # Rebuild map if missing (e.g. old session)
        if not crop_map:
            state_u  = users.get(phone, {}).get("state", "")
            crops    = get_crops_for_state(state_u)
            _, crop_map = build_crop_menu(crops)
        if body not in crop_map:
            valid = "/".join(crop_map.keys())
            menu_str = "\n".join(f"{k}. {v}" for k, v in crop_map.items())
            return send(f"Reply {valid} for crop:\n{menu_str}")
        session["crop"] = crop_map[body]
        session["step"] = "month"
        sessions[phone] = session
        save_json(SESSIONS_FILE, sessions)
        return send(
            f"Crop: {session['crop']} OK\n\n"
            f"Which month to sell?\n"
            f"Reply 1-12\n"
            f"(1=Jan  6=June  12=Dec)"
        )

    # Step: month
    elif step == "month":
        if not body.isdigit() or not (1 <= int(body) <= 12):
            return send("Reply with month 1-12.\nExample: 3 for March.")
        session["month"] = int(body)
        session["step"]  = "qty"
        sessions[phone]  = session
        save_json(SESSIONS_FILE, sessions)
        month_name = datetime.date(2000, session["month"], 1).strftime("%B")
        return send(
            f"Month: {month_name} OK\n\n"
            f"Select quantity:\n"
            f"1. Below 500 kg\n"
            f"2. 500-1000 kg\n"
            f"3. 1000-5000 kg\n"
            f"4. Above 5000 kg"
        )

    # Step: qty → run prediction
    elif step == "qty":
        if body not in QTY_MAP:
            return send(
                "Reply 1-4:\n"
                "1.<500kg   2.500-1000kg\n"
                "3.1-5 ton  4.>5000kg"
            )

        qty        = QTY_MAP[body]
        crop       = session["crop"]
        month      = session["month"]
        year       = datetime.datetime.now().year
        district   = users[phone]["district"]
        state      = users[phone].get("state", "Tamil Nadu")
        month_name = datetime.date(2000, month, 1).strftime("%B")

        try:
            results = recommend(
                commodity       = crop,
                quantity_kg     = qty,
                farmer_district = district,
                farmer_state    = state,
                target_month    = month,
                target_year     = year,
                max_distance_km = 200,
                top_n           = 3
            )

            if not results:
                msg = (
                    f"No markets found for {crop}\n"
                    f"near {district} in {month_name}.\n\n"
                    f"Try a different crop or month.\n"
                    f"MENU to start again."
                )
            else:
                top = results[:2]
                msg = (
                    f"Fasal-to-Faida Results\n"
                    f"{crop} | {QTY_LABELS[body]}\n"
                    f"Sell: {month_name} | {district}\n\n"
                )
                for i, r in enumerate(top, 1):
                    msg += (
                        f"{i}. {r['market']}\n"
                        f"   Rs.{r['predicted_price']:,.0f}/qtl\n"
                        f"   Transport: Rs.{r['transport_cost']:,.0f}\n"
                        f"   Net: Rs.{r['net_profit']:,.0f}"
                    f" (Rs.{r['profit_per_kg']:.1f}/kg)\n\n"
                )
            msg += "MENU for new query\n#PINCODE to change district"

        except Exception as e:
            msg = (
                f"Prediction failed. Try again.\n"
                f"Send MENU to restart.\n"
                f"Error: {e}"
            )

        # Clear session after result
        sessions.pop(phone, None)
        save_json(SESSIONS_FILE, sessions)
        return send(msg)

    # Fallback — unknown state, reset
    sessions.pop(phone, None)
    save_json(SESSIONS_FILE, sessions)
    return send("Send MENU to start or HELP for info.")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
