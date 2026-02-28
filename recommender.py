"""
recommender.py
==============
Market Recommendation System + Profit Calculator.

Used by app.py and sms.py.

Usage:
    from recommender import recommend

    results = recommend(
        commodity       = 'Tomato',
        quantity_kg     = 500,
        farmer_district = 'Coimbatore',
        farmer_state    = 'Tamil Nadu',
        target_month    = 6,
        target_year     = 2025,
        max_distance_km = 150,
        top_n           = 5
    )

    for r in results:
        print(r)
"""

import pandas as pd
import numpy as np
import joblib
from predict import predict_price

# ── Load supporting datasets once ────────────────────────
_centroids  = None
_final_data = None
_price_df   = None

def _load_data():
    global _centroids, _final_data, _price_df
    if _centroids is None:
        _centroids = pd.read_csv(
    'datasets/district wise centroids.csv')
        _centroids.columns = \
            _centroids.columns.str.strip()
        _centroids['District'] = \
            _centroids['District'].str.strip().str.title()
        _centroids['State'] = \
            _centroids['State'].str.strip()

        _final_data = pd.read_csv(
            'datasets/final_data.csv')
        _final_data['District'] = \
            _final_data['District'].str.strip().str.title()
        _final_data['State'] = \
            _final_data['State'].str.strip()
        _final_data['Market'] = \
            _final_data['Market'].str.strip()

        _price_df = pd.read_parquet(
            'model/clean_df.parquet')


# ─────────────────────────────────────────────────────────
# DISTANCE
# ─────────────────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    """Straight-line distance × 1.3 ≈ road distance."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(
        np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (np.sin(dlat/2)**2 +
         np.cos(lat1) * np.cos(lat2) *
         np.sin(dlon/2)**2)
    straight = R * 2 * np.arctan2(
        np.sqrt(a), np.sqrt(1-a))
    return round(straight * 1.3, 1)


def get_distance(origin_district, dest_district,
                 origin_state=None, dest_state=None):
    """
    Get approximate road distance (km) between
    two districts using centroid coordinates.
    Returns 999 if district not found.
    """
    _load_data()

    def get_coords(district, state=None):
        mask = (_centroids['District'].str.lower()
                == district.lower())
        if state:
            mask_s = (_centroids['State'].str.lower()
                      == state.lower())
            row = _centroids[mask & mask_s]
            if row.empty:
                row = _centroids[mask]
        else:
            row = _centroids[mask]
        return row

    orig = get_coords(origin_district, origin_state)
    dest = get_coords(dest_district,   dest_state)

    if orig.empty or dest.empty:
        return 999  # unknown — will be filtered out

    return _haversine(
        orig['Latitude'].values[0],
        orig['Longitude'].values[0],
        dest['Latitude'].values[0],
        dest['Longitude'].values[0]
    )


# ─────────────────────────────────────────────────────────
# TRANSPORT COST
# ─────────────────────────────────────────────────────────
def calc_transport(distance_km, quantity_kg):
    """
    Tiered transport cost based on truck size.

    Rates (realistic Indian road freight):
    - Mini  (≤1000 kg):  ₹12/km + ₹200 loading
    - Medium (≤5000 kg): ₹18/km + ₹400 loading
    - Large  (>5000 kg): ₹25/km + ₹600 loading
    """
    if quantity_kg <= 1000:
        rate, loading, minimum = 12, 200, 500
    elif quantity_kg <= 5000:
        rate, loading, minimum = 18, 400, 800
    else:
        rate, loading, minimum = 25, 600, 1200

    cost = distance_km * rate + loading
    return round(max(cost, minimum), 2)


# ─────────────────────────────────────────────────────────
# PROFIT CALCULATOR
# ─────────────────────────────────────────────────────────
def calc_profit(quantity_kg, price_per_quintal,
                distance_km):
    """
    Full profit breakdown.

    Parameters
    ----------
    quantity_kg       : int/float  weight in kg
    price_per_quintal : float      predicted price ₹/quintal
    distance_km       : float      road distance in km

    Returns
    -------
    dict with full profit breakdown
    """
    qty_quintals = quantity_kg / 100

    gross_revenue  = round(price_per_quintal
                           * qty_quintals, 2)
    transport_cost = calc_transport(
                        distance_km, quantity_kg)
    mandi_fee      = round(gross_revenue * 0.02, 2)
    misc_costs     = round(qty_quintals * 10, 2)
    total_costs    = round(
                        transport_cost +
                        mandi_fee + misc_costs, 2)
    net_profit     = round(
                        gross_revenue - total_costs, 2)
    profit_per_kg  = round(
                        net_profit / quantity_kg, 2) \
                     if quantity_kg > 0 else 0

    return {
        'gross_revenue':    gross_revenue,
        'transport_cost':   transport_cost,
        'mandi_fee':        mandi_fee,
        'misc_costs':       misc_costs,
        'total_costs':      total_costs,
        'net_profit':       net_profit,
        'profit_per_kg':    profit_per_kg,
    }


# ─────────────────────────────────────────────────────────
# MARKET RECOMMENDER
# ─────────────────────────────────────────────────────────
def recommend(commodity, quantity_kg,
              farmer_district, farmer_state,
              target_month, target_year,
              max_distance_km=150, top_n=5):
    """
    Recommend best markets for selling a crop.

    Parameters
    ----------
    commodity        : str   e.g. 'Tomato'
    quantity_kg      : int   e.g. 500
    farmer_district  : str   e.g. 'Coimbatore'
    farmer_state     : str   e.g. 'Tamil Nadu'
    target_month     : int   1-12
    target_year      : int   e.g. 2025
    max_distance_km  : int   filter out far markets
    top_n            : int   number of results

    Returns
    -------
    list of dicts, sorted by net_profit descending
    """
    _load_data()

    # Get all markets that trade this commodity
    # from the price dataset (real trading history)
    price_df = _price_df
    markets = price_df[
        price_df['commodity'] == commodity
    ][['market', 'district', 'state']]\
     .drop_duplicates()\
     .reset_index(drop=True)

    print(f"\n[INFO] Evaluating {len(markets)} markets "
          f"for {commodity}...")

    results = []
    skipped = 0

    for _, row in markets.iterrows():
        mkt_market   = row['market']
        mkt_district = row['district']
        mkt_state    = row['state']

        # Calculate distance
        dist = get_distance(
            farmer_district, mkt_district,
            farmer_state,    mkt_state
        )

        # Skip if too far or coordinates unknown
        if dist > max_distance_km:
            skipped += 1
            continue

        # Predict price at this market
        price = predict_price(
            district      = mkt_district,
            commodity     = commodity,
            state         = mkt_state,
            target_month  = target_month,
            target_year   = target_year,
            market        = mkt_market
        )

        if price is None or price <= 0:
            skipped += 1
            continue

        # Calculate profit
        profit = calc_profit(quantity_kg, price, dist)

        results.append({
            # Market info
            'market':           mkt_market,
            'district':         mkt_district,
            'state':            mkt_state,
            'distance_km':      dist,
            'is_same_district': (
                mkt_district.lower() ==
                farmer_district.lower()),
            # Price
            'predicted_price':  price,
            # Profit breakdown
            **profit
        })

    print(f"   Found {len(results)} reachable markets "
          f"(skipped {skipped})")

    # Sort by net profit
    results.sort(key=lambda x: x['net_profit'],
                 reverse=True)

    return results[:top_n]


# ─────────────────────────────────────────────────────────
# PINCODE LOOKUP (for SMS teammate)
# ─────────────────────────────────────────────────────────
_pincode_df = None

def lookup_pincode(pincode):
    """
    Convert pincode → district + state.
    Uses local india_pincode_final.csv (no internet needed).

    Returns dict with district, state, valid flag.
    """
    global _pincode_df
    if _pincode_df is None:
        _pincode_df = pd.read_csv(
    'datasets/india pincode final.csv')
        _pincode_df['pincode'] = \
            _pincode_df['pincode'].astype(str).str.strip()

    pin_str = str(pincode).strip()
    match   = _pincode_df[
        _pincode_df['pincode'] == pin_str]

    if match.empty:
        return {'valid': False,
                'district': None,
                'state': None}

    row = match.iloc[0]
    return {
        'valid':    True,
        'district': row['Districtname'].title(),
        'state':    row['statename'].title(),
    }


# ─────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("TEST 1: Distance calculation")
    print("=" * 60)
    pairs = [
        ('Coimbatore', 'Salem',    'Tamil Nadu', 'Tamil Nadu'),
        ('Coimbatore', 'Madurai',  'Tamil Nadu', 'Tamil Nadu'),
        ('Nashik',     'Pune',     'Maharashtra','Maharashtra'),
    ]
    for o, d, os, ds in pairs:
        dist = get_distance(o, d, os, ds)
        print(f"  {o} → {d}: {dist} km")

    print("\n" + "=" * 60)
    print("TEST 2: Profit calculator")
    print("=" * 60)
    p = calc_profit(
        quantity_kg       = 500,
        price_per_quintal = 1200,
        distance_km       = 80
    )
    for k, v in p.items():
        print(f"  {k:<20}: ₹{v:,.2f}")

    print("\n" + "=" * 60)
    print("TEST 3: Market recommendation")
    print("=" * 60)
    results = recommend(
        commodity       = 'Tomato',
        quantity_kg     = 500,
        farmer_district = 'Coimbatore',
        farmer_state    = 'Tamil Nadu',
        target_month    = 6,
        target_year     = 2025,
        max_distance_km = 200,
        top_n           = 5
    )

    if results:
        print(f"\n🏆 Top {len(results)} markets:\n")
        print(f"{'#':<3} {'Market':<30} {'District':<15}"
              f"{'Dist':>6} {'Price':>8} {'Profit':>10}")
        print("-" * 75)
        for i, r in enumerate(results, 1):
            print(
                f"{i:<3} {r['market']:<30} "
                f"{r['district']:<15} "
                f"{r['distance_km']:>5}km "
                f"₹{r['predicted_price']:>7,.0f} "
                f"₹{r['net_profit']:>9,.0f}"
            )
    else:
        print("  No markets found — check distance filter")

    print("\n" + "=" * 60)
    print("TEST 4: Pincode lookup")
    print("=" * 60)
    for pin in ['641001', '600001', '110001', '999999']:
        result = lookup_pincode(pin)
        if result['valid']:
            print(f"  {pin} → {result['district']}, "
                  f"{result['state']}")
        else:
            print(f"  {pin} → ❌ Not found")
