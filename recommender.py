"""
recommender.py
==============
Market Recommendation System + Profit Calculator.

Used by app.py and sms/sms_handler.py. Locations come from geo.py.

Usage:
    from geo import lookup_pincode
    from recommender import recommend

    loc = lookup_pincode("641001")
    results = recommend(
        commodity       = 'Onion',
        quantity_kg     = 500,
        farmer_lat      = loc['lat'],
        farmer_lon      = loc['lon'],
        target_month    = 6,
        target_year     = 2026,
        max_distance_km = 200,
        top_n           = 5,
        farmer_district = loc['district'],
    )
"""

import logging

from geo import lookup_pincode, markets_near  # noqa: F401  (lookup_pincode re-exported)
from predict import predict_price

log = logging.getLogger("fasal.recommender")


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
              farmer_lat, farmer_lon,
              target_month, target_year,
              max_distance_km=150, top_n=5,
              farmer_district=None):
    """
    Recommend best markets for selling a crop.

    Parameters
    ----------
    commodity        : str    e.g. 'Tomato'
    quantity_kg      : int    e.g. 500
    farmer_lat/lon   : float  farmer location (from geo.lookup_pincode)
    target_month     : int    1-12
    target_year      : int    e.g. 2026
    max_distance_km  : int    filter out far markets
    top_n            : int    number of results
    farmer_district  : str    canonical district, only used for is_same_district

    Returns
    -------
    list of dicts, sorted by net_profit descending
    """
    near = markets_near(farmer_lat, farmer_lon, max_distance_km, commodity)

    results = []
    no_price = 0
    for row in near.itertuples(index=False):
        # predict.py is keyed on the price-data spellings (src_*), not canonical names
        price = predict_price(
            district     = row.src_district,
            commodity    = commodity,
            state        = row.src_state,
            target_month = target_month,
            target_year  = target_year,
            market       = row.market,
        )
        if price is None or price <= 0:
            no_price += 1
            continue

        results.append({
            'market':           row.market,
            'district':         row.district,
            'state':            row.state,
            'distance_km':      float(row.distance_km),
            'is_same_district': (farmer_district is not None
                                 and row.district == farmer_district),
            'predicted_price':  price,
            **calc_profit(quantity_kg, price, float(row.distance_km)),
        })

    log.info("%s: %d mandis within %s km, %d priced, %d without recent prices",
             commodity, len(near), max_distance_km, len(results), no_price)

    results.sort(key=lambda x: x['net_profit'], reverse=True)
    return results[:top_n]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    for pin, crop in [('641001', 'Onion'), ('422001', 'Onion'), ('712101', 'Potato')]:
        loc = lookup_pincode(pin)
        print(f"\n{pin} -> {loc['district']}, {loc['state']}  ({crop})")
        for i, r in enumerate(recommend(crop, 500, loc['lat'], loc['lon'], 6, 2026, 200, 5,
                                        farmer_district=loc['district']), 1):
            print(f"  {i}. {r['market']:<30} {r['state']:<15} {r['distance_km']:>6} km"
                  f"  Rs.{r['predicted_price']:>8,.0f}/q  net Rs.{r['net_profit']:>9,.0f}")
