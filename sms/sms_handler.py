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

# ── Add parent directory to path so we can import recommender ────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recommender import recommend
# ────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# ── File paths ───────────────────────────────────────────────────────────────
USERS_FILE    = "registered_users.json"
SESSIONS_FILE = "sessions.json"

# ── Constants ────────────────────────────────────────────────────────────────
CROPS = {
    "1": "Tomato",
    "2": "Onion",
    "3": "Potato",
    "4": "Wheat",
    "5": "Rice"
}
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


# ── Supported districts & name normalisation ─────────────────────────────────
SUPPORTED_DISTRICTS = {
    "Coimbatore", "Salem", "Erode", "Madurai", "Trichy",
    "Tirupur", "Dindigul", "Namakkal", "Pollachi", "Thanjavur", "Chennai"
}

# Maps API-returned district names → internal names used in the distance matrix.
# Keys are lowercase-stripped for case-insensitive matching.
DISTRICT_NORMALIZE = {
    "coimbatore":             "Coimbatore",
    "coimbatore district":    "Coimbatore",
    "salem":                  "Salem",
    "erode":                  "Erode",
    "madurai":                "Madurai",
    "tiruchirappalli":        "Trichy",
    "trichy":                 "Trichy",
    "tiruppur":               "Tirupur",
    "tirupur":                "Tirupur",
    "dindigul":               "Dindigul",
    "namakkal":               "Namakkal",
    "pollachi":               "Pollachi",
    "thanjavur":              "Thanjavur",
    "chennai":                "Chennai",
    "kancheepuram":           "Chennai",   # nearest supported
    "chengalpattu":           "Chennai",
    "tiruvallur":             "Chennai",
    "the nilgiris":           "Coimbatore",  # nearest supported
    "nilgiris":               "Coimbatore",
    "ooty":                   "Coimbatore",
    "krishnagiri":            "Salem",
    "dharmapuri":             "Salem",
    "karur":                  "Trichy",
    "perambalur":             "Trichy",
    "ariyalur":               "Trichy",
}

SUPPORTED_LIST_STR = ", ".join(sorted(SUPPORTED_DISTRICTS))


def normalize_district(raw: str):
    """
    Maps a raw API district name to an internal supported name.
    Returns the internal name string, or None if not mappable.
    """
    key = raw.strip().lower()
    # Direct lookup
    if key in DISTRICT_NORMALIZE:
        return DISTRICT_NORMALIZE[key]
    # Check if already a valid supported name (case-insensitive)
    for supported in SUPPORTED_DISTRICTS:
        if key == supported.lower():
            return supported
    return None


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
        with open(path, "r") as f:
            return json.load(f)
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

        # District recognised by API but not in our supported list
        if district is None:
            return send(
                f"Your district ({raw_district}) is not yet supported.\n"
                f"Supported: {SUPPORTED_LIST_STR}.\n"
                f"Send a nearby district's pincode."
            )

        is_update = phone in users
        users[phone] = {
            "pincode":  pincode,
            "district": district,   # normalized internal name
            "state":    state
        }
        save_json(USERS_FILE, users)

        # Clear any active session on re-register
        sessions.pop(phone, None)
        save_json(SESSIONS_FILE, sessions)

        action = "Updated" if is_update else "Registered"
        return send(
            f"Fasal-to-Faida\n"
            f"{action}!\n"
            f"District: {district}, {state}\n\n"
            f"Select crop:\n"
            f"1. Tomato\n2. Onion\n3. Potato\n"
            f"4. Wheat\n5. Rice\n\n"
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
        return send(
            f"Fasal-to-Faida\n"
            f"District: {district}\n\n"
            f"Select crop:\n"
            f"1. Tomato\n2. Onion\n3. Potato\n"
            f"4. Wheat\n5. Rice\n\n"
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
        sessions[phone] = {"step": "crop"}
        save_json(SESSIONS_FILE, sessions)
        return send(
            f"Fasal-to-Faida | {district}\n\n"
            f"Select crop:\n"
            f"1. Tomato\n2. Onion\n3. Potato\n"
            f"4. Wheat\n5. Rice"
        )

    # ── 6. ACTIVE SESSION — menu steps ───────────────────────────────────────
    session = sessions[phone]
    step    = session.get("step", "crop")

    # Step: crop
    if step == "crop":
        if body not in CROPS:
            return send(
                "Reply 1-5 for crop:\n"
                "1.Tomato 2.Onion 3.Potato\n"
                "4.Wheat  5.Rice"
            )
        session["crop"] = CROPS[body]
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