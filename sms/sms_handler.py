# sms_handler.py
# Fasal-to-Faida — SMS via Twilio
# Registration: #PINCODE | Prediction: crop → month → qty → results

from flask import Flask, request, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
import json
import logging
import os
import re
import sys
import datetime

# ── Set working directory to project root so recommender's relative paths work ─
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)
import geo
from recommender import recommend
from sms.strings import LANGS, LANG_MENU, STRINGS, t, crop_name

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fasal.sms")

# ── Twilio request validation ────────────────────────────────────────────────
# Fails CLOSED: without TWILIO_AUTH_TOKEN every POST /sms is rejected, unless
# ALLOW_UNSIGNED_SMS=1 is set explicitly (local development only).
#
# TWILIO_WEBHOOK_URL must be the exact URL configured in the Twilio console,
# e.g. https://your-app.up.railway.app/sms — Twilio signs that string, and
# rebuilding it from proxy headers is what broke validation before.
_TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
_TWILIO_WEBHOOK_URL = os.environ.get("TWILIO_WEBHOOK_URL", "").strip()
_ALLOW_UNSIGNED     = os.environ.get("ALLOW_UNSIGNED_SMS") == "1"
_twilio_validator   = RequestValidator(_TWILIO_AUTH_TOKEN) if _TWILIO_AUTH_TOKEN else None

if _twilio_validator is None and not _ALLOW_UNSIGNED:
    log.warning("TWILIO_AUTH_TOKEN not set: all /sms requests will be rejected. "
                "Set ALLOW_UNSIGNED_SMS=1 for local development.")


def _signed_url() -> str:
    """The URL Twilio signed: explicit config, else rebuilt from proxy headers."""
    if _TWILIO_WEBHOOK_URL:
        url = _TWILIO_WEBHOOK_URL
        if request.query_string:
            url += "?" + request.query_string.decode()
        return url
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    host   = request.headers.get("X-Forwarded-Host", request.host)
    return f"{scheme}://{host}{request.full_path.rstrip('?')}"


@app.before_request
def validate_twilio_signature():
    if request.path != "/sms" or request.method != "POST":
        return
    if _twilio_validator is None:
        if _ALLOW_UNSIGNED:
            return
        abort(403)
    sig = request.headers.get("X-Twilio-Signature", "")
    if not _twilio_validator.validate(_signed_url(), request.form.to_dict(), sig):
        log.warning("Rejected /sms request with invalid Twilio signature")
        abort(403)


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    """Log the real error server-side; the user only gets a generic reply."""
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):
        return exc
    log.exception("Unhandled error in SMS webhook")
    return send(t("error", "EN"))

# ── File paths ───────────────────────────────────────────────────────────────
USERS_FILE    = "registered_users.json"
SESSIONS_FILE = "/tmp/sessions.json"   # ephemeral per container run — that's fine

# Seed registered users from USERS_JSON env var on cold start (survives redeploys)
_USERS_JSON_ENV = os.environ.get("USERS_JSON", "")
if _USERS_JSON_ENV and not os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as _f:
            _f.write(_USERS_JSON_ENV)
    except Exception:
        pass

# All 5 crops in display order (used as fallback)
ALL_CROPS = ["Tomato", "Onion", "Potato", "Wheat", "Rice"]

def get_lang(phone: str, users: dict) -> str:
    """Return stored language code for this user, defaulting to EN."""
    return users.get(phone, {}).get("lang", "EN")

MAX_DISTANCE_KM = 200


def get_crops_for_user(user: dict) -> list:
    """Crops traded at a mandi within MAX_DISTANCE_KM of the user's pincode.
    Falls back to ALL_CROPS if the pincode is missing or unknown."""
    loc = geo.lookup_pincode(user.get("pincode", ""))
    if not loc["valid"]:
        return ALL_CROPS
    return geo.available_crops(loc["lat"], loc["lon"], MAX_DISTANCE_KM, order=ALL_CROPS) or ALL_CROPS

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


# ── Pincode → location (geo.py owns all name matching) ───────────────────────
def pincode_to_location(pincode: str):
    """Returns (loc, error); error is 'bad_pincode' | 'not_found' | None."""
    if not re.fullmatch(r"\d{6}", pincode):
        return None, "bad_pincode"
    loc = geo.lookup_pincode(pincode)
    if not loc["valid"]:
        return None, "not_found"
    return loc, None


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
        loc, err = pincode_to_location(pincode)
        lang = get_lang(phone, users)

        if err in ("bad_pincode", "not_found"):
            return send(t("bad_pincode", lang))

        is_update = phone in users
        existing_lang = users.get(phone, {}).get("lang", lang)
        users[phone] = {
            "pincode":  pincode,
            "district": loc["district"],
            "state":    loc["state"],
            "lang":     existing_lang,
        }
        save_json(USERS_FILE, users)
        lang = existing_lang

        crops = get_crops_for_user(users[phone])
        crop_menu, crop_map = build_crop_menu(crops, lang)
        sessions[phone] = {"step": "crop", "crop_map": crop_map}
        save_json(SESSIONS_FILE, sessions)

        action = t("registered_action", lang).get(
            "update" if is_update else "new", "Registered"
        )
        return send(t("registered", lang,
                      action=action, district=loc["district"],
                      state=loc["state"], crop_menu=crop_menu))

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
        crops    = get_crops_for_user(users.get(phone, {}))
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
        crops    = get_crops_for_user(users.get(phone, {}))
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
            crops    = get_crops_for_user(users.get(phone, {}))
            crop_menu, crop_map = build_crop_menu(crops, lang)
            session["step"]     = "crop"
            session["crop_map"] = crop_map
            session.pop("crop", None)
            sessions[phone] = session
            save_json(SESSIONS_FILE, sessions)
            district = users[phone]["district"]
            return send(t("main_menu", lang, district=district, crop_menu=crop_menu))
        else:
            crops    = get_crops_for_user(users.get(phone, {}))
            crop_menu, crop_map = build_crop_menu(crops, lang)
            sessions[phone] = {"step": "crop", "crop_map": crop_map}
            save_json(SESSIONS_FILE, sessions)
            district = users[phone]["district"]
            return send(t("main_menu", lang, district=district, crop_menu=crop_menu))

    if step == "crop":
        crop_map = session.get("crop_map") or {}
        if not crop_map:
            crops    = get_crops_for_user(users.get(phone, {}))
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
        loc        = geo.lookup_pincode(users[phone].get("pincode", ""))
        district   = loc["district"] or users[phone].get("district", "")
        state      = loc["state"] or users[phone].get("state", "")
        month_name = datetime.date(2000, month, 1).strftime("%B")

        try:
            if not loc["valid"]:
                raise ValueError(f"stored pincode for {phone[-4:]} no longer resolves")
            results = recommend(
                commodity       = crop,
                quantity_kg     = qty,
                farmer_lat      = loc["lat"],
                farmer_lon      = loc["lon"],
                target_month    = month,
                target_year     = year,
                max_distance_km = MAX_DISTANCE_KM,
                top_n           = 3,
                farmer_district = district,
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

        except Exception:
            log.exception("recommend() failed (crop=%s month=%s district=%s state=%s)",
                          crop, month, district, state)
            msg = t("error", lang)

        # Clear session after result
        sessions.pop(phone, None)
        save_json(SESSIONS_FILE, sessions)
        return send(msg)

    # Fallback — unknown state, reset
    sessions.pop(phone, None)
    save_json(SESSIONS_FILE, sessions)
    return send("Send MENU to start or HELP for info.")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
