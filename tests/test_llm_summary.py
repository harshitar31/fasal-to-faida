"""Tests for llm_summary.py. A fake OpenAI client is used; nothing calls a real API."""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import llm_summary  # noqa: E402

CFG = {"base_url": "https://api.example.test/v1", "model": "test-model", "api_key": "k"}
RECORDS = [{"market": "Lasalgaon", "state": "Maharashtra", "predicted_price": 1500.0,
            "distance_km": 42.0, "transport_cost": 704.0, "net_profit": 10000.0,
            "profit_per_kg": 13.3}]
INPUTS = {"quantity_kg": 750, "commodity": "Onion", "month_name": "January", "year": 2027}


@pytest.fixture
def fake_openai(monkeypatch):
    """Install a fake `openai` module and record how it was called."""
    calls = {}

    class FakeClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.chat = types.SimpleNamespace(completions=self)

        def create(self, **kwargs):
            calls["create"] = kwargs
            if calls.get("raise"):
                raise RuntimeError("provider down")
            msg = types.SimpleNamespace(content=calls.get("reply", "  Sell at Lasalgaon.  "))
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeClient))
    return calls


@pytest.mark.parametrize("secrets", [
    {},
    {"llm": {}},
    {"llm": {"base_url": "x", "model": "m", "api_key": ""}},
    {"llm": {"base_url": "x", "model": "", "api_key": "k"}},
    {"featherless": {"api_key": "old"}},          # old config is no longer used
])
def test_incomplete_config_disables_advisory(secrets):
    assert llm_summary.load_llm_config(secrets) is None


def test_complete_config_is_trimmed():
    cfg = llm_summary.load_llm_config({"llm": {"base_url": " u ", "model": "m ", "api_key": " k"}})
    assert cfg == {"base_url": "u", "model": "m", "api_key": "k"}


def test_uses_configured_provider_with_timeout(fake_openai):
    text, err = llm_summary.generate_summary(RECORDS, INPUTS, "Nashik", "Maharashtra", CFG)
    assert (text, err) == ("Sell at Lasalgaon.", None)
    assert fake_openai["client"]["base_url"] == CFG["base_url"]
    assert fake_openai["client"]["api_key"] == "k"
    assert fake_openai["client"]["timeout"] <= 10
    assert fake_openai["create"]["model"] == "test-model"
    assert fake_openai["create"]["temperature"] <= 0.3


def test_prompt_contains_only_real_numbers_and_forbids_inventing(fake_openai):
    llm_summary.generate_summary(RECORDS, INPUTS, "Nashik", "Maharashtra", CFG)
    system, user = (m["content"] for m in fake_openai["create"]["messages"])
    assert "never invent" in system
    assert "Lasalgaon" in user and "10,000" in user and "Nashik, Maharashtra" in user


def test_provider_error_is_returned_not_raised(fake_openai):
    fake_openai["raise"] = True
    text, err = llm_summary.generate_summary(RECORDS, INPUTS, "Nashik", "Maharashtra", CFG)
    assert text is None and "provider down" in err


def test_empty_reply_counts_as_failure(fake_openai):
    fake_openai["reply"] = "   "
    text, err = llm_summary.generate_summary(RECORDS, INPUTS, "Nashik", "Maharashtra", CFG)
    assert text is None and err


def test_no_call_without_config_or_records(fake_openai):
    assert llm_summary.generate_summary(RECORDS, INPUTS, "N", "M", None)[0] is None
    assert llm_summary.generate_summary([], INPUTS, "N", "M", CFG)[0] is None
    assert "create" not in fake_openai
