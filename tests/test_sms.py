"""Tests for the Twilio SMS webhook: signature validation, error handling, flow."""
import importlib
import json
import logging
import os
import sys

import pytest
from twilio.request_validator import RequestValidator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

URL = "https://example.up.railway.app/sms"
TOKEN = "test-token-123"
FORM = {"From": "+919999999999", "Body": "HELP"}
SIG = RequestValidator(TOKEN).compute_signature(URL, FORM)


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    def _make(**env):
        for k in ("TWILIO_AUTH_TOKEN", "TWILIO_WEBHOOK_URL", "ALLOW_UNSIGNED_SMS"):
            monkeypatch.delenv(k, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        cwd = os.getcwd()
        import sms.sms_handler as h
        h = importlib.reload(h)
        os.chdir(cwd)   # the handler chdirs to the project root on import
        h.USERS_FILE = str(tmp_path / "users.json")
        h.SESSIONS_FILE = str(tmp_path / "sessions.json")
        logging.getLogger("fasal.sms").disabled = True
        return h, h.app.test_client()
    return _make


# ── Signature validation ─────────────────────────────────────────────────────
def test_valid_signature_accepted(make_client):
    _, c = make_client(TWILIO_AUTH_TOKEN=TOKEN, TWILIO_WEBHOOK_URL=URL)
    r = c.post("/sms", data=FORM, headers={"X-Twilio-Signature": SIG})
    assert r.status_code == 200 and b"<Response>" in r.data


@pytest.mark.parametrize("headers,form", [
    ({"X-Twilio-Signature": "forged"}, FORM),
    ({}, FORM),
    ({"X-Twilio-Signature": SIG}, {**FORM, "From": "+911111111111"}),   # tampered sender
])
def test_bad_signature_rejected(make_client, headers, form):
    _, c = make_client(TWILIO_AUTH_TOKEN=TOKEN, TWILIO_WEBHOOK_URL=URL)
    assert c.post("/sms", data=form, headers=headers).status_code == 403


def test_proxy_header_url_reconstruction(make_client):
    _, c = make_client(TWILIO_AUTH_TOKEN=TOKEN)
    r = c.post("/sms", data=FORM, headers={"X-Twilio-Signature": SIG,
               "X-Forwarded-Proto": "https", "X-Forwarded-Host": "example.up.railway.app"})
    assert r.status_code == 200


def test_fails_closed_without_token(make_client):
    _, c = make_client()
    assert c.post("/sms", data=FORM).status_code == 403


def test_unsigned_allowed_only_with_explicit_dev_flag(make_client):
    _, c = make_client(ALLOW_UNSIGNED_SMS="1")
    assert c.post("/sms", data=FORM).status_code == 200


# ── Error handling ───────────────────────────────────────────────────────────
def _boom(*a, **k):
    raise RuntimeError("SECRET_INTERNAL_DETAIL")


def test_crash_returns_generic_message(make_client):
    h, c = make_client(ALLOW_UNSIGNED_SMS="1")
    h.load_json = _boom
    r = c.post("/sms", data=FORM)
    assert r.status_code == 200
    assert b"something went wrong" in r.data and b"SECRET_INTERNAL_DETAIL" not in r.data


def test_prediction_failure_is_translated_and_hides_internals(make_client):
    h, c = make_client(ALLOW_UNSIGNED_SMS="1")
    h.recommend = _boom
    json.dump({"+91222": {"pincode": "422001", "district": "Nashik",
                          "state": "Maharashtra", "lang": "HI"}}, open(h.USERS_FILE, "w"))
    json.dump({"+91222": {"step": "qty", "crop": "Onion", "month": 6}}, open(h.SESSIONS_FILE, "w"))
    body = c.post("/sms", data={"From": "+91222", "Body": "2"}).data.decode()
    assert "कुछ गड़बड़" in body and "SECRET_INTERNAL_DETAIL" not in body


# ── Conversation flow with the geo table ─────────────────────────────────────
def _say(c, phone, text):
    return c.post("/sms", data={"From": phone, "Body": text}).data.decode()


def test_full_flow_for_previously_unresolvable_pincode(make_client):
    """Hooghly (712101) returned 0 results before the geo table."""
    h, c = make_client(ALLOW_UNSIGNED_SMS="1")
    phone = "+91333"
    assert "English" in _say(c, phone, "hi")
    _say(c, phone, "1")                                  # English
    reg = _say(c, phone, "#712101")
    assert "Hugli, West Bengal" in reg
    users = json.load(open(h.USERS_FILE))
    assert users[phone]["district"] == "Hugli" and users[phone]["pincode"] == "712101"
    crop_map = json.load(open(h.SESSIONS_FILE))[phone]["crop_map"]
    potato = next(k for k, v in crop_map.items() if v == "Potato")
    _say(c, phone, potato)
    _say(c, phone, "1")                                  # January
    result = _say(c, phone, "2")                         # 500-1000 kg
    assert "km)" in result and "Net profit" in result, result


def test_crop_menu_follows_location_not_state(make_client):
    """Coimbatore can reach Kerala rice mandis; old STATE_CROPS hid Rice for TN."""
    h, c = make_client(ALLOW_UNSIGNED_SMS="1")
    phone = "+91444"
    _say(c, phone, "hi")
    _say(c, phone, "1")
    _say(c, phone, "#641001")
    crop_map = json.load(open(h.SESSIONS_FILE))[phone]["crop_map"]
    assert "Rice" in crop_map.values()
