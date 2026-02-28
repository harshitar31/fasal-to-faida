# sms_handler.py
# Fasal-to-Faida — SMS via Twilio
# Registration: #PINCODE | Prediction: crop → month → qty → results

from flask import Flask, request, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
import json
import os
import re
import sys
import datetime
import csv

# ── Set working directory to project root so recommender's relative paths work ─
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)
from recommender import recommend
from sms.strings import LANGS, LANG_MENU, STRINGS, t, crop_name

app = Flask(__name__)

# ── Twilio request validation (skipped in local dev if token not set) ─────────
_TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
_twilio_validator  = RequestValidator(_TWILIO_AUTH_TOKEN) if _TWILIO_AUTH_TOKEN else None

@app.before_request
def validate_twilio_signature():
    if request.path != "/sms":
        return
    if _twilio_validator is None:
        return  # local dev — skip validation
    sig    = request.headers.get("X-Twilio-Signature", "")
    valid  = _twilio_validator.validate(request.url, request.form.to_dict(), sig)
    if not valid:
        abort(403)

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

def get_lang(phone: str, users: dict) -> str:
    """Return stored language code for this user, defaulting to EN."""
    return users.get(phone, {}).get("lang", "EN")

def get_crops_for_state(state: str) -> list:
    """Returns available crop list for a state. Falls back to ALL_CROPS."""
    key = state.strip().title()
    return STATE_CROPS.get(key, ALL_CROPS)

def build_crop_menu(crops: list, lang: str = "EN") -> tuple:
    """
    Returns (menu_str, crop_map) where crop_map maps reply digit → crop name (English).
    Menu lines use translated crop names for the given language.
    """
    crop_map = {str(i+1): c for i, c in enumerate(crops)}  # always English keys
    lines = "\n".join(f"{i+1}. {crop_name(c, lang)}" for i, c in enumerate(crops))
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
def send(msg: str):
    from flask import Response
    r = MessagingResponse()
    r.message(msg)
    return Response(str(r), mimetype="text/xml")



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
        lang = get_lang(phone, users)

        if err in ("bad_pincode", "not_found"):
            return send(t("bad_pincode", lang))

        is_update = phone in users
        existing_lang = users.get(phone, {}).get("lang", lang)
        users[phone] = {
            "pincode":  pincode,
            "district": district,
            "state":    state,
            "lang":     existing_lang,
        }
        save_json(USERS_FILE, users)
        lang = existing_lang

        crops = get_crops_for_state(state)
        crop_menu, crop_map = build_crop_menu(crops, lang)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)

        action = t("registered_action", lang).get(
            "update" if is_update else "new", "Registered"
        )
        return send(t("registered", lang,
                      action=action, district=district,
                      state=state, crop_menu=crop_menu))

    # ── LANG N  or  ** — switch language anytime ─────────────────────────────
    if body == "**":
        # Show language menu so user can pick by number
        sessions[phone] = {**sessions.get(phone, {}), "pending_lang": True, "step": "lang"}
        save_json(SESSIONS_FILE, sessions)
        return send(LANG_MENU)

    if body_upper.startswith("LANG "):
        code     = body_upper.split(None, 1)[1].strip()
        new_lang = LANGS.get(code)
        if new_lang:
            users.setdefault(phone, {})["lang"] = new_lang
            save_json(USERS_FILE, users)
            return send(t("lang_switched", new_lang))
        return send("Send LANG 1 (English), LANG 2 (Hindi), or LANG 3 (Tamil).")

    # ── 2. HELP ───────────────────────────────────────────────────────────────
    if body_upper in ["HELP", "?"]:
        return send(t("help", get_lang(phone, users)))

    # ── 3. RESET / MENU ───────────────────────────────────────────────────────
    if body_upper in ["MENU", "HI", "HELLO", "START", "RESET"]:
        lang = get_lang(phone, users)
        sessions.pop(phone, None)
        save_json(SESSIONS_FILE, sessions)
        if phone not in users or not users[phone].get("district"):
            sessions[phone] = {"step": "lang"}
            save_json(SESSIONS_FILE, sessions)
            return send(LANG_MENU)
        district = users[phone]["district"]
        state_u  = users[phone].get("state", "")
        crops    = get_crops_for_state(state_u)
        crop_menu, crop_map = build_crop_menu(crops, lang)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)
        return send(t("main_menu", lang, district=district, crop_menu=crop_menu))

    # ── 4. NEW USER — no registration, no session ─────────────────────────────
    if phone not in users and phone not in sessions:
        sessions[phone] = {"step": "lang"}
        save_json(SESSIONS_FILE, sessions)
        return send(LANG_MENU)

    # ── 5. REGISTERED USER — no active session → start crop menu ─────────────
    if phone not in sessions:
        lang     = get_lang(phone, users)
        district = users[phone]["district"]
        state_u  = users[phone].get("state", "")
        crops    = get_crops_for_state(state_u)
        crop_menu, crop_map = build_crop_menu(crops, lang)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)
        return send(t("main_menu", lang, district=district, crop_menu=crop_menu))

    session = sessions[phone]
    step    = session.get("step", "crop")
    lang    = get_lang(phone, users)

    # ── LANGUAGE SELECTION — first interaction ────────────────────────────────
    if step == "lang":
        chosen = LANGS.get(body)
        if not chosen:
            return send(LANG_MENU)
        lang = chosen
        users.setdefault(phone, {})["lang"] = lang
        save_json(USERS_FILE, users)
        sessions[phone] = {"step": "await_pincode"}
        save_json(SESSIONS_FILE, sessions)
        return send(t("lang_set", lang, next=t("register_prompt", lang)))

    # Not yet registered — nudge toward pincode
    if step == "await_pincode" or not users.get(phone, {}).get("district"):
        return send(t("register_prompt", lang))

    # ── BACK navigation: '*' goes one step back ───────────────────────────────
    if body == "*":
        if step == "qty":
            session["step"] = "month"
            sessions[phone] = session
            save_json(SESSIONS_FILE, sessions)
            return send(t("crop_ok_ask_month", lang,
                          crop=crop_name(session.get("crop", ""), lang)))
        elif step == "month":
            state_u  = users.get(phone, {}).get("state", "")
            crops    = get_crops_for_state(state_u)
            crop_menu, crop_map = build_crop_menu(crops, lang)
            session["step"]     = "crop"
            session["crop_map"] = crop_map
            session.pop("crop", None)
            sessions[phone] = session
            save_json(SESSIONS_FILE, sessions)
            district = users[phone]["district"]
            return send(t("main_menu", lang, district=district, crop_menu=crop_menu))
        else:
            state_u  = users.get(phone, {}).get("state", "")
            crops    = get_crops_for_state(state_u)
            crop_menu, crop_map = build_crop_menu(crops, lang)
            sessions[phone] = {"step": "crop", "crop_map": crop_map}
            save_json(SESSIONS_FILE, sessions)
            district = users[phone]["district"]
            return send(t("main_menu", lang, district=district, crop_menu=crop_menu))

    if step == "crop":
        crop_map = session.get("crop_map") or {}
        if not crop_map:
            state_u  = users.get(phone, {}).get("state", "")
            crops    = get_crops_for_state(state_u)
            _, crop_map = build_crop_menu(crops, lang)
        if body not in crop_map:
            valid    = "/".join(crop_map.keys())
            menu_str = "\n".join(f"{k}. {crop_name(v, lang)}" for k, v in crop_map.items())
            return send(t("invalid_crop", lang, valid=valid, menu=menu_str))
        session["crop"] = crop_map[body]   # stored in English
        session["step"] = "month"
        sessions[phone] = session
        save_json(SESSIONS_FILE, sessions)
        return send(t("crop_ok_ask_month", lang,
                      crop=crop_name(session["crop"], lang)))

    # Step: month
    elif step == "month":
        if not body.isdigit() or not (1 <= int(body) <= 12):
            return send(t("invalid_month", lang))
        session["month"] = int(body)
        session["step"]  = "qty"
        sessions[phone]  = session
        save_json(SESSIONS_FILE, sessions)
        month_name = datetime.date(2000, session["month"], 1).strftime("%B")
        return send(t("month_ok_ask_qty", lang, month=month_name))

    # Step: qty → run prediction
    elif step == "qty":
        if body not in QTY_MAP:
            return send(t("invalid_qty", lang))

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
                msg = t("no_results", lang,
                        crop=crop_name(crop, lang),
                        district=district, month=month_name)
            else:
                top = results[:2]
                msg = t("result_header", lang,
                        crop=crop_name(crop, lang),
                        month=month_name, qty=qty,
                        district=district)
                for i, r in enumerate(top, 1):
                    msg += t("result_item", lang,
                             rank=i,
                             market=r["market"],
                             dist=round(r.get("distance_km", 0)),
                             price=f"{r['predicted_price']:,.0f}",
                             profit=f"{r['net_profit']:,.0f}")
            msg += "\nMENU"

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
