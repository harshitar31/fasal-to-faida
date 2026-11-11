"""
geo.py
======
Single source of truth for locations: pincode -> farmer location, mandi
locations, and distances. Reads the tables built by scripts/build_geo.py;
nothing here does name matching at request time.

    from geo import lookup_pincode, markets_near, available_crops

    loc = lookup_pincode("641001")
    # {'valid': True, 'pincode': '641001', 'state': 'Tamil Nadu',
    #  'district': 'Coimbatore', 'lat': 11.0, 'lon': 76.9}

Debug a pincode from the command line:

    python geo.py 641001
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

import numpy as np
import pandas as pd

GEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "geo")
ROAD_FACTOR = 1.3   # straight-line km x 1.3 ~ road km


@lru_cache(maxsize=1)
def _pincodes() -> dict[str, dict]:
    df = pd.read_csv(os.path.join(GEO_DIR, "pincodes.csv"), dtype={"pincode": str})
    df = df.dropna(subset=["lat", "lon"])
    return {r.pincode: {"state": r.state, "district": r.district,
                        "lat": float(r.lat), "lon": float(r.lon)}
            for r in df.itertuples()}


@lru_cache(maxsize=1)
def markets() -> pd.DataFrame:
    """All mandis with coordinates. src_district/src_state are the price-data
    spellings that predict.py expects; state/district are canonical."""
    df = pd.read_csv(os.path.join(GEO_DIR, "markets.csv"))
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    df["commodities"] = df["commodities"].str.split("|")
    df["fresh_commodities"] = df["fresh_commodities"].fillna("").map(
        lambda s: s.split("|") if s else [])
    return df


def lookup_pincode(pincode) -> dict:
    """Pincode -> canonical state/district + coordinates. valid=False if unknown."""
    pin = str(pincode).strip()
    hit = _pincodes().get(pin) if re.fullmatch(r"\d{6}", pin) else None
    if hit is None:
        return {"valid": False, "pincode": pin, "state": None, "district": None,
                "lat": None, "lon": None}
    return {"valid": True, "pincode": pin, **hit}


def road_distance_km(lat, lon, lats, lons) -> np.ndarray:
    """Vectorised haversine from one point to many, times ROAD_FACTOR."""
    lat1, lon1 = np.radians(lat), np.radians(lon)
    lat2, lon2 = np.radians(np.asarray(lats, float)), np.radians(np.asarray(lons, float))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return np.round(6371 * 2 * np.arcsin(np.sqrt(a)) * ROAD_FACTOR, 1)


def markets_near(lat: float, lon: float, max_km: float,
                 commodity: str | None = None) -> pd.DataFrame:
    """Mandis within max_km road distance, optionally only those trading commodity.
    Adds a distance_km column, sorted nearest first."""
    m = markets()
    if commodity is not None:
        m = m[m["commodities"].apply(lambda cs: commodity in cs)]
    m = m.assign(distance_km=road_distance_km(lat, lon, m["lat"], m["lon"]))
    return m[m["distance_km"] <= max_km].sort_values("distance_km")


def available_crops(lat: float, lon: float, max_km: float,
                    order: list[str] | None = None) -> list[str]:
    """Crops with recent prices at at least one mandi within max_km. Replaces the
    old hard-coded STATE_CROPS, which ignored mandis across state borders."""
    near = markets_near(lat, lon, max_km)
    crops = sorted({c for cs in near["fresh_commodities"] for c in cs})
    if order:
        crops = [c for c in order if c in crops] + [c for c in crops if c not in order]
    return crops


if __name__ == "__main__":
    import sys
    pin = sys.argv[1] if len(sys.argv) > 1 else "641001"
    loc = lookup_pincode(pin)
    print(loc)
    if loc["valid"]:
        near = markets_near(loc["lat"], loc["lon"], 200)
        print(f"{len(near)} mandis within 200 km; crops: "
              f"{available_crops(loc['lat'], loc['lon'], 200)}")
        print(near[["market", "district", "state", "distance_km"]].head(10).to_string(index=False))
