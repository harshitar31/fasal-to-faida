"""Tests for the canonical location table (scripts/build_geo.py + geo.py)."""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_geo  # noqa: E402
import geo  # noqa: E402

GEO = os.path.join(ROOT, "datasets", "geo")


# ── Name folding ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("a,b", [
    ("Hooghly", "Hugli"),
    ("JAMMU & KASHMIR", "Jammu and Kashmir"),
    ("Bijapur(CGH)", "Bijapur (CGH)"),
])
def test_fold_treats_spelling_variants_as_equal(a, b):
    assert build_geo.fold(a) == build_geo.fold(b)


@pytest.mark.parametrize("state,raw,expected,method", [
    ("ANDHRA PRADESH", "Mahabub Nagar", "Mahbubnagar", "fuzzy"),
    ("Uttar Pradesh", "Bulandshahar", "Bulandshahr", "fuzzy"),
    ("WEST BENGAL", "Hooghly", "Hugli", "exact"),
    ("PUNJAB", "Mohali", "Rupnagar", "override"),
    ("Odisha", "Bargarh", "Baragarh", "legacy_alias"),
])
def test_matcher(state, raw, expected, method):
    m = build_geo.Matcher(build_geo.load_centroids())
    _, district, got_method, _ = m.match(state, raw)
    assert (district, got_method) == (expected, method)


def test_matcher_never_crosses_states():
    m = build_geo.Matcher(build_geo.load_centroids())
    st, district, method, _ = m.match("Kerala", "Coimbatore")   # Coimbatore is in Tamil Nadu
    assert st == "Kerala" and district != "Coimbatore"


def test_fold_keeps_different_districts_apart_within_each_state():
    c = build_geo.load_centroids()
    for state, grp in c.groupby("state"):
        keys = {}
        for d in grp["district"]:
            for v in build_geo.name_variants(d):
                assert keys.setdefault(v, d) == d, f"{state}: {d} collides with {keys[v]}"


# ── Built tables ─────────────────────────────────────────────────────────────
def test_every_pincode_and_market_is_located():
    pins = pd.read_csv(os.path.join(GEO, "pincodes.csv"), dtype={"pincode": str})
    mk = pd.read_csv(os.path.join(GEO, "markets.csv"))
    assert pins[["lat", "lon"]].notna().all().all()
    assert mk[["lat", "lon"]].notna().all().all()


def test_markets_never_cross_state_except_documented_relocations():
    mk = pd.read_csv(os.path.join(GEO, "markets.csv"))
    states = sorted(build_geo.load_centroids()["state"].unique())
    canon_src = mk["src_state"].map(lambda s: build_geo.canonical_state(s, states))
    moved = mk[canon_src != mk["state"]]
    assert set(moved["method"]) <= {"market_override"}, moved[["market", "src_state", "state"]]


def test_committed_tables_are_up_to_date(tmp_path):
    """Fails if someone edits overrides.csv / source data without re-running
    `python scripts/build_geo.py` and committing the result."""
    build_geo.build(out_dir=str(tmp_path), verbose=False)
    for f in ("districts.csv", "pincodes.csv", "markets.csv", "match_report.csv"):
        fresh = (tmp_path / f).read_bytes()
        committed = open(os.path.join(GEO, f), "rb").read()
        assert fresh == committed, f"datasets/geo/{f} is stale: run scripts/build_geo.py"


# ── Pincode lookup ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("pin,state,district", [
    ("641001", "Tamil Nadu", "Coimbatore"),
    ("712101", "West Bengal", "Hugli"),            # was 'not found' before geo table
    ("736101", "West Bengal", "Kochbihar"),        # Cooch Behar
    ("509001", "Andhra Pradesh", "Mahbubnagar"),
    ("160062", "Punjab", "Rupnagar"),              # Mohali -> parent district
    ("495003", "Chhattisgarh", "Bilaspur"),        # NOT Bilaspur, Himachal Pradesh
    ("174001", "Himachal Pradesh", "Bilaspur"),
    ("561206", "Karnataka", "Kolar"),              # Chikkaballapur; legacy alias said Chikmagalur
])
def test_lookup_pincode(pin, state, district):
    loc = geo.lookup_pincode(pin)
    assert loc["valid"] and loc["state"] == state and loc["district"] == district


@pytest.mark.parametrize("pin", ["", "12345", "abcdef", "1234567", "999999"])
def test_lookup_pincode_rejects_bad_input(pin):
    assert geo.lookup_pincode(pin)["valid"] is False


def test_bilaspur_chhattisgarh_is_far_from_bilaspur_himachal():
    cg, hp = geo.lookup_pincode("495003"), geo.lookup_pincode("174001")
    assert geo.road_distance_km(cg["lat"], cg["lon"], [hp["lat"]], [hp["lon"]])[0] > 1000


# ── Distances and crops ──────────────────────────────────────────────────────
def test_road_distance():
    assert geo.road_distance_km(20.0, 73.8, [20.0], [73.8])[0] == 0
    # Nashik -> Pune: ~165 km straight line, x1.3 road factor
    assert 180 < geo.road_distance_km(19.99, 73.79, [18.52], [73.86])[0] < 240


def test_markets_near_is_sorted_and_filtered():
    loc = geo.lookup_pincode("422001")
    near = geo.markets_near(loc["lat"], loc["lon"], 100, "Onion")
    assert len(near) > 0
    assert near["distance_km"].is_monotonic_increasing
    assert (near["distance_km"] <= 100).all()
    assert near["commodities"].apply(lambda cs: "Onion" in cs).all()


def test_relocated_mandi_is_no_longer_near_punjab():
    """Maudaha is in Hamirpur, UP; the raw data files it under Hamirpur, HP."""
    loc = geo.lookup_pincode("160062")
    near = geo.markets_near(loc["lat"], loc["lon"], 200)
    assert "Maudaha" not in set(near["market"])


def test_available_crops_crosses_state_borders():
    """The old hard-coded STATE_CROPS offered only Onion and Potato in Tamil Nadu,
    but Coimbatore farmers can reach Kerala mandis with recent rice prices."""
    loc = geo.lookup_pincode("641001")
    assert "Rice" in geo.available_crops(loc["lat"], loc["lon"], 200)
    near = geo.markets_near(loc["lat"], loc["lon"], 200)
    rice = near[near["fresh_commodities"].apply(lambda cs: "Rice" in cs)]
    assert (rice["state"] != "Tamil Nadu").any()


@pytest.mark.parametrize("pin", ["641001", "712101", "160062", "495003"])
def test_every_offered_crop_returns_results(pin):
    """Crop menus must never offer a crop that ends in 'No markets found'."""
    import logging
    import recommender
    logging.getLogger("fasal.recommender").disabled = True
    loc = geo.lookup_pincode(pin)
    for crop in geo.available_crops(loc["lat"], loc["lon"], 200):
        res = recommender.recommend(crop, 750, loc["lat"], loc["lon"], 1, 2027, 200, 3,
                                    farmer_district=loc["district"])
        assert res, f"{pin}: {crop} offered but no results"
