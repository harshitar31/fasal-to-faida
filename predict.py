"""
predict.py
==========
Price prediction function.
Used by recommender.py, app.py, and sms.py.

Usage:
    from predict import predict_price
    price = predict_price('Salem', 'Tomato', 'Tamil Nadu', 6, 2025)
    print(f"Predicted: ₹{price}/quintal")
"""

import pandas as pd
import numpy as np
import joblib

# ── Load artifacts at module import — guaranteed ready before first request ───
print("📦 Loading model artifacts...")
_model    = joblib.load('model/price_model.joblib')
_encoders = joblib.load('model/encoders.joblib')
_features = joblib.load('model/features.joblib')
_df       = pd.read_parquet('model/clean_df.parquet')
print("   ✅ Model loaded.")


# ── Helpers ───────────────────────────────────────────────
SEASON_MAP = {
    12: 'Winter', 1: 'Winter',  2: 'Winter',
    3:  'Summer', 4: 'Summer',  5: 'Summer',
    6:  'Monsoon',7: 'Monsoon', 8: 'Monsoon',
    9:  'Post',  10: 'Post',   11: 'Post'
}

HARVEST_MONTHS = {
    'Tomato': [11, 12, 1, 2],
    'Onion':  [2, 3, 4, 5],
    'Potato': [1, 2, 3],
    'Wheat':  [3, 4, 5],
    'Rice':   [10, 11, 12]
}

def _safe_encode(col, value):
    """Encode a value — returns 0 if unseen."""
    try:
        return int(_encoders[col].transform(
            [str(value)])[0])
    except ValueError:
        # Unknown value — use most common class
        return 0


def _get_recent_prices(commodity, market, district, state):
    """
    Get last 90 days of prices for this 
    commodity + market combo.
    Falls back to state-level if market not found.
    """
    # Try exact market match first
    hist = _df[
        (_df['commodity'] == commodity) &
        (_df['market']    == market)
    ].sort_values('price_date').tail(90)

    if len(hist) >= 7:
        return hist

    # Fallback: same district + commodity
    hist = _df[
        (_df['commodity'] == commodity) &
        (_df['district']  == district)
    ].sort_values('price_date').tail(90)

    if len(hist) >= 7:
        return hist

    # Fallback: same state + commodity
    hist = _df[
        (_df['commodity'] == commodity) &
        (_df['state']     == state)
    ].sort_values('price_date').tail(90)

    return hist


# ── Main prediction function ──────────────────────────────
def predict_price(district, commodity, state,
                  target_month, target_year,
                  market=None):
    """
    Predict modal price for a crop at a given
    market/district in a given month.

    Parameters
    ----------
    district      : str  e.g. 'Salem'
    commodity     : str  e.g. 'Tomato'
    state         : str  e.g. 'Tamil Nadu'
    target_month  : int  1-12
    target_year   : int  e.g. 2025
    market        : str  optional, e.g. 'Salem'

    Returns
    -------
    float : predicted price in ₹/quintal
    None  : if prediction not possible
    """
    # Use district name as market if not given
    if market is None:
        market = district

    # Get recent price history for lag features
    hist = _get_recent_prices(
        commodity, market, district, state)

    if len(hist) == 0:
        return None

    prices = hist['modal_price']

    # Build feature row
    season = SEASON_MAP[target_month]
    row = {
        # Time features
        'month':        target_month,
        'year':         target_year,
        'quarter':      (target_month - 1) // 3 + 1,
        'week':         target_month * 4,
        'day_of_year':  target_month * 30,
        'season_enc':   _safe_encode('season', season),
        'is_harvest':   1 if target_month in
                        HARVEST_MONTHS.get(commodity, [])
                        else 0,
        # Location & commodity
        'state_enc':     _safe_encode('state',     state),
        'district_enc':  _safe_encode('district',  district),
        'market_enc':    _safe_encode('market',    market),
        'commodity_enc': _safe_encode('commodity', commodity),
        # Lag features from recent history
        'lag_7d':   prices.iloc[-7]  if len(prices) >= 7
                    else prices.mean(),
        'lag_14d':  prices.iloc[-14] if len(prices) >= 14
                    else prices.mean(),
        'lag_30d':  prices.iloc[-30] if len(prices) >= 30
                    else prices.mean(),
        'lag_60d':  prices.iloc[-60] if len(prices) >= 60
                    else prices.mean(),
        # Rolling averages
        'roll_7d':   prices.tail(7).mean(),
        'roll_30d':  prices.tail(30).mean(),
        'roll_90d':  prices.mean(),
        # Other signals
        'momentum':   prices.iloc[-1] - (
                        prices.iloc[-30]
                        if len(prices) >= 30
                        else prices.mean()),
        'volatility': float(prices.std()) \
                        if len(prices) > 1 else 0.0,
        'price_range': float(
            hist['max_price'].iloc[-1] -
            hist['min_price'].iloc[-1]),
        'min_price':  float(hist['min_price'].iloc[-1]),
        'max_price':  float(hist['max_price'].iloc[-1]),
    }

    X = pd.DataFrame([row])[_features]
    prediction = float(_model.predict(X)[0])
    return round(max(prediction, 0), 2)


# ── Quick test ────────────────────────────────────────────
if __name__ == '__main__':
    test_cases = [
        ('Salem',       'Onion',  'Tamil Nadu',   6, 2025),
        ('Nashik',      'Onion',  'Maharashtra',  6, 2025),
        ('Coimbatore',  'Tomato', 'Tamil Nadu',   3, 2025),
        ('Agra',        'Potato', 'Uttar Pradesh',2, 2025),
        ('Ludhiana',    'Wheat',  'Punjab',       4, 2025),
    ]

    print("🧪 Testing predict_price()\n")
    print(f"{'District':<15} {'Crop':<8} {'State':<15}"
          f"{'Month':<8} {'Predicted Price'}")
    print("-" * 60)

    for district, crop, state, month, year in test_cases:
        price = predict_price(
            district, crop, state, month, year)
        if price:
            print(f"{district:<15} {crop:<8} {state:<15}"
                  f"{'Month '+str(month):<8} "
                  f"₹{price:,.2f}/quintal")
        else:
            print(f"{district:<15} {crop:<8} "
                  f"No data available")
