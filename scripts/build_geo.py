"""
build_geo.py
============
Builds ONE canonical location table so pincodes, mandis and district centroids
all agree on names. Run from the project root after the source data changes:

    python scripts/build_geo.py

Inputs
    datasets/district wise centroids.csv   canonical districts + coordinates
    datasets/india pincode final.csv       pincode -> district/state (old spellings)
    model/clean_df.parquet                 mandis (market, district, state) + crops
    datasets/geo/overrides.csv             hand-curated district matches (edit this file)
    datasets/geo/market_overrides.csv      mandis the price data files under the wrong state

Outputs (datasets/geo/)
    districts.csv   state, district, lat, lon
    pincodes.csv    pincode, state, district, lat, lon, method
    markets.csv     market, src_district, src_state, state, district, lat, lon,
                    commodities, fresh_commodities, method
    match_report.csv  every non-exact or failed match, for human review

Matching never crosses state lines: a district is only matched to a centroid in
the same (canonical) state. That is what prevents e.g. a farmer in Bilaspur,
Chhattisgarh being placed in Bilaspur, Himachal Pradesh.
"""
from __future__ import annotations

import difflib
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_CENTROIDS = os.path.join(ROOT, "datasets", "district wise centroids.csv")
SRC_PINCODES = os.path.join(ROOT, "datasets", "india pincode final.csv")
SRC_PRICES = os.path.join(ROOT, "model", "clean_df.parquet")
OUT_DIR = os.path.join(ROOT, "datasets", "geo")
OVERRIDES = os.path.join(OUT_DIR, "overrides.csv")
MARKET_OVERRIDES = os.path.join(OUT_DIR, "market_overrides.csv")

FRESH_DAYS = 180     # keep in sync with the staleness guard in predict.py
FUZZY_CUTOFF = 0.8  # difflib ratio on folded names; matches below this are reported, not used

# ── State names ──────────────────────────────────────────────────────────────
# Canonical = centroid-file spelling, except where that file uses pre-2011 names.
CENTROID_STATE_RENAMES = {"Orissa": "Odisha", "Uttaranchal": "Uttarakhand"}

# Any other spelling seen in the sources -> canonical. Keys are folded (see _state_key).
STATE_ALIASES = {
    "chattisgarh": "Chhattisgarh",
    "pondicherry": "Puducherry",
    "andamanandnicobarislands": "Andaman and Nicobar",
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    "telangana": "Andhra Pradesh",   # centroid file predates the 2014 split
    "ladakh": "Jammu and Kashmir",   # centroid file predates the 2019 split
    "eastsinghbhum": "Jharkhand",    # bad row in the pincode CSV: district in the state column
}


def _state_key(name: str) -> str:
    return re.sub(r"[^a-z]", "", str(name).lower().replace("&", "and"))


# ── District name folding ────────────────────────────────────────────────────
_TRANSLIT = [("ph", "f"), ("c", "k"), ("q", "k"), ("w", "v"), ("z", "j"), ("y", "i"),
             ("aa", "a"), ("ee", "i"), ("oo", "u"), ("ou", "u")]


def fold(name: str) -> str:
    """Spelling-insensitive key: 'Hooghly' and 'Hugli' both fold to 'hugli'."""
    s = str(name).lower().replace("&", " and ")
    s = re.sub(r"\b(district|dist|dt)\b", " ", s)
    s = re.sub(r"[^a-z]", "", s)
    for a, b in _TRANSLIT:
        s = s.replace(a, b)
    s = re.sub(r"([bdfgjklmnprstvk])h", r"\1", s)   # drop aspirate h: 'bh'->'b', 'kh'->'k'
    s = re.sub(r"(.)\1+", r"\1", s)                 # collapse doubled letters
    return s


def name_variants(name: str) -> set[str]:
    """Folded keys for a name and its parenthetical parts: 'Ladakh (Leh)' -> ladak, le, ..."""
    out = {fold(name)}
    outside = re.sub(r"\(.*?\)", " ", name)
    out.add(fold(outside))
    for inner in re.findall(r"\((.*?)\)", name):
        out.add(fold(inner))
    return {v for v in out if v}


# ── Loaders ──────────────────────────────────────────────────────────────────
def load_centroids() -> pd.DataFrame:
    c = pd.read_csv(SRC_CENTROIDS)
    c.columns = c.columns.str.strip()
    c["State"] = c["State"].str.strip().replace(CENTROID_STATE_RENAMES)
    c["District"] = c["District"].str.strip()
    c = c.rename(columns={"State": "state", "District": "district",
                          "Latitude": "lat", "Longitude": "lon"})
    return c[["state", "district", "lat", "lon"]]


def canonical_state(raw: str, states: list[str]) -> str | None:
    key = _state_key(raw)
    if key in STATE_ALIASES:
        return STATE_ALIASES[key]
    by_key = {_state_key(s): s for s in states}
    return by_key.get(key)


def load_overrides() -> dict[tuple[str, str], str]:
    """(canonical state, folded source district) -> centroid district."""
    if not os.path.exists(OVERRIDES):
        return {}
    o = pd.read_csv(OVERRIDES, comment="#").fillna("")
    return {(r.state.strip(), fold(r.source_district)): r.centroid_district.strip()
            for r in o.itertuples()}


def legacy_aliases() -> dict[str, str]:
    """The team's hand-made pincode->centroid aliases from sms_handler.py (pre-geo)."""
    path = os.path.join(ROOT, "scripts", "legacy_district_aliases.py")
    ns: dict = {}
    exec(open(path, encoding="utf-8").read(), ns)
    return {fold(k): v for k, v in ns["DISTRICT_ALIASES"].items()}


# ── Matcher ──────────────────────────────────────────────────────────────────
class Matcher:
    def __init__(self, centroids: pd.DataFrame):
        self.c = centroids
        self.states = sorted(centroids["state"].unique())
        self.by_state: dict[str, dict[str, str]] = {}
        for st, grp in centroids.groupby("state"):
            keys: dict[str, str] = {}
            for d in grp["district"]:
                for v in name_variants(d):
                    keys.setdefault(v, d)
            self.by_state[st] = keys
        self.overrides = load_overrides()
        self.legacy = legacy_aliases()

    def match(self, raw_state: str, raw_district: str):
        """Returns (canonical_state, centroid_district, method, score)."""
        st = canonical_state(raw_state, self.states)
        if st is None:
            return None, None, "unknown_state", 0.0
        keys = self.by_state.get(st, {})
        centroid_names = set(keys.values())
        f = fold(raw_district)

        ov = self.overrides.get((st, f))
        if ov:
            if ov not in centroid_names:
                raise ValueError(f"overrides.csv: '{ov}' is not a centroid district in {st}")
            return st, ov, "override", 1.0

        for v in name_variants(raw_district):
            if v in keys:
                return st, keys[v], "exact", 1.0

        legacy = self.legacy.get(f)
        if legacy and legacy in centroid_names:
            return st, legacy, "legacy_alias", 1.0

        best = difflib.get_close_matches(f, list(keys), n=2, cutoff=FUZZY_CUTOFF)
        if best:
            score = difflib.SequenceMatcher(None, f, best[0]).ratio()
            return st, keys[best[0]], "fuzzy", round(score, 3)
        return st, None, "unmatched", 0.0


def apply_market_overrides(mk: pd.DataFrame, coords: pd.DataFrame, report: list) -> pd.DataFrame:
    """Relocate mandis the price data files under the wrong state (market_overrides.csv)."""
    if not os.path.exists(MARKET_OVERRIDES):
        return mk
    ov = pd.read_csv(MARKET_OVERRIDES, comment="#").fillna("")
    mk = mk.copy()
    for r in ov.itertuples():
        hit = (mk["market"] == r.market) & (mk["src_state"] == r.src_state)
        if not hit.any():
            raise ValueError(f"market_overrides.csv: no market '{r.market}' in {r.src_state}")
        if (r.state, r.district) not in coords.index:
            raise ValueError(f"market_overrides.csv: '{r.district}' is not a centroid district in {r.state}")
        lat, lon = coords.loc[(r.state, r.district)]
        mk.loc[hit, ["state", "district", "lat", "lon", "method"]] = \
            [r.state, r.district, lat, lon, "market_override"]
        report.append({"kind": "market", "source_state": r.src_state, "source_district": r.market,
                       "state": r.state, "district": r.district, "method": "market_override",
                       "score": 1.0})
    return mk


def build(out_dir: str = OUT_DIR, verbose: bool = True):
    os.makedirs(out_dir, exist_ok=True)
    centroids = load_centroids()
    m = Matcher(centroids)
    coords = centroids.set_index(["state", "district"])[["lat", "lon"]]
    report = []

    def resolve(df, state_col, dist_col, kind):
        uniq = df[[state_col, dist_col]].drop_duplicates()
        rows = []
        for raw_s, raw_d in uniq.itertuples(index=False):
            st, d, method, score = m.match(raw_s, raw_d)
            rows.append((raw_s, raw_d, st, d, method, score))
            if method not in ("exact", "override"):
                report.append({"kind": kind, "source_state": raw_s, "source_district": raw_d,
                               "state": st, "district": d, "method": method, "score": score})
        res = pd.DataFrame(rows, columns=[state_col, dist_col, "state", "district", "method", "score"])
        out = df.merge(res, on=[state_col, dist_col], how="left")
        out = out.join(coords, on=["state", "district"])
        return out

    # Pincodes
    pins = pd.read_csv(SRC_PINCODES, dtype=str)
    pins["pincode"] = pins["pincode"].str.strip().str.zfill(6)
    pins = pins.dropna(subset=["Districtname", "statename"])
    pins["Districtname"] = pins["Districtname"].str.strip()
    pins["statename"] = pins["statename"].str.strip()
    pins = resolve(pins, "statename", "Districtname", "pincode")
    pins = pins.drop_duplicates("pincode")
    pins_out = pins[["pincode", "state", "district", "lat", "lon", "method"]]

    # Markets (one row per market+source district+source state; that is the key predict.py uses)
    prices = pd.read_parquet(SRC_PRICES, columns=["market", "district", "state", "commodity",
                                                  "price_date"])
    crops = (prices.groupby(["market", "district", "state"])["commodity"]
             .apply(lambda s: "|".join(sorted(s.unique()))).reset_index(name="commodities"))
    # Crops this mandi still reported recently: same 180-day rule as predict.py's
    # staleness guard. Used to build crop menus that won't lead to "no markets found".
    cutoff = prices["price_date"].max() - pd.Timedelta(days=FRESH_DAYS)
    last = prices.groupby(["market", "district", "state", "commodity"])["price_date"].max()
    fresh = (last[last >= cutoff].reset_index().groupby(["market", "district", "state"])["commodity"]
             .apply(lambda s: "|".join(sorted(s.unique()))).reset_index(name="fresh_commodities"))
    crops = crops.merge(fresh, on=["market", "district", "state"], how="left").fillna(
        {"fresh_commodities": ""})
    crops = crops.rename(columns={"district": "src_district", "state": "src_state"})
    mk = resolve(crops, "src_state", "src_district", "market")
    mk = apply_market_overrides(mk, coords, report)
    mk_out = mk[["market", "src_district", "src_state", "state", "district", "lat", "lon",
                 "commodities", "fresh_commodities", "method"]]

    centroids.to_csv(os.path.join(out_dir, "districts.csv"), index=False)
    pins_out.to_csv(os.path.join(out_dir, "pincodes.csv"), index=False)
    mk_out.to_csv(os.path.join(out_dir, "markets.csv"), index=False)
    rep = pd.DataFrame(report).sort_values(["method", "kind", "state", "source_district"])
    rep.to_csv(os.path.join(out_dir, "match_report.csv"), index=False)

    def summary(df, label):
        n = len(df)
        ok = df["lat"].notna().sum()
        meth = df["method"].value_counts().to_dict()
        print(f"{label:9s} {ok}/{n} located ({ok / n:.1%})  {meth}")

    if not verbose:
        return pins_out, mk_out, rep
    summary(pins_out, "pincodes")
    summary(mk_out, "markets")
    unmatched = rep[rep.method.isin(["unmatched", "unknown_state"])]
    if len(unmatched):
        print(f"\n{len(unmatched)} names could not be located (add them to overrides.csv):")
        print(unmatched[["kind", "source_state", "source_district", "state"]].to_string(index=False))
    return pins_out, mk_out, rep


if __name__ == "__main__":
    build()
    sys.exit(0)
