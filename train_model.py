"""
train_model.py
==============
Trains XGBoost model on Agriculture_price_dataset.csv
Run this ONCE before anything else.
Saves model artifacts to model/ folder.
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── Paths ────────────────────────────────────────────────
DATA_PATH  = 'datasets/Agriculture_price_dataset.csv'
MODEL_DIR  = 'model'
os.makedirs(MODEL_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────
# STEP 1: LOAD & CLEAN
# ─────────────────────────────────────────────────────────
print("📂 Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"   Raw shape: {df.shape}")

# Standardize column names
df = df.rename(columns={
    'STATE':          'state',
    'District Name':  'district',
    'Market Name':    'market',
    'Commodity':      'commodity',
    'Min_Price':      'min_price',
    'Max_Price':      'max_price',
    'Modal_Price':    'modal_price',
    'Price Date':     'price_date'
})

# Fix state name inconsistencies
state_fix = {
    'tamilnadu':          'Tamil Nadu',
    'tamil nadu':         'Tamil Nadu',
    'jammu & kashmir':    'Jammu and Kashmir',
    'jammu and kashmir':  'Jammu and Kashmir',
    'chattisgarh':        'Chhattisgarh',
    'chhattisgarh':       'Chhattisgarh',
    'uttrakhand':         'Uttarakhand',
    'orissa':             'Odisha',
    'gao':                'Goa',
}
df['state'] = df['state'].str.strip()
df['state'] = df['state'].str.strip().str.lower()\
    .map(lambda x: state_fix.get(x, x.title()))

# Clean strings
df['district']  = df['district'].str.strip().str.title()
df['market']    = df['market'].str.strip()
df['commodity'] = df['commodity'].str.strip()

# Parse dates and prices
df['price_date']  = pd.to_datetime(df['price_date'],
                                    dayfirst=False,
                                    errors='coerce')
df['modal_price'] = pd.to_numeric(df['modal_price'],
                                   errors='coerce')
df['min_price']   = pd.to_numeric(df['min_price'],
                                   errors='coerce')
df['max_price']   = pd.to_numeric(df['max_price'],
                                   errors='coerce')

# Drop bad rows
df = df.dropna(subset=['price_date', 'modal_price'])
df = df[df['modal_price'] > 0]

# Sort for lag features
df = df.sort_values(['commodity', 'market', 'price_date'])\
       .reset_index(drop=True)

print(f"   Clean shape: {df.shape}")
print(f"   Date range: {df['price_date'].min().date()} "
      f"→ {df['price_date'].max().date()}")
print(f"   Crops: {sorted(df['commodity'].unique())}")
print(f"   States: {df['state'].nunique()}")
print(f"   Markets: {df['market'].nunique()}")

# ─────────────────────────────────────────────────────────
# STEP 2: FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────
print("\n⚙️  Engineering features...")

# Time features
df['month']       = df['price_date'].dt.month
df['year']        = df['price_date'].dt.year
df['quarter']     = df['price_date'].dt.quarter
df['day_of_year'] = df['price_date'].dt.dayofyear
df['week']        = df['price_date'].dt.isocalendar()\
                      .week.astype(int)

# Season
season_map = {
    12: 'Winter', 1: 'Winter',  2: 'Winter',
    3:  'Summer', 4: 'Summer',  5: 'Summer',
    6:  'Monsoon',7: 'Monsoon', 8: 'Monsoon',
    9:  'Post',  10: 'Post',   11: 'Post'
}
df['season'] = df['month'].map(season_map)

# Harvest season flag per crop
harvest_months = {
    'Tomato': [11, 12, 1, 2],
    'Onion':  [2, 3, 4, 5],
    'Potato': [1, 2, 3],
    'Wheat':  [3, 4, 5],
    'Rice':   [10, 11, 12]
}
df['is_harvest'] = df.apply(
    lambda r: 1 if r['month'] in
    harvest_months.get(r['commodity'], [])
    else 0, axis=1
)

# Price spread (proxy for supply variability)
df['price_range'] = df['max_price'] - df['min_price']

# Lag features — grouped by commodity + market
# (most predictive features for price)
print("   Computing lag features (takes ~30s)...")
grp = df.groupby(['commodity', 'market'])['modal_price']

df['lag_7d']  = grp.shift(7)
df['lag_14d'] = grp.shift(14)
df['lag_30d'] = grp.shift(30)
df['lag_60d'] = grp.shift(60)

# Rolling averages
df['roll_7d']  = grp.transform(
    lambda x: x.rolling(7,  min_periods=1).mean())
df['roll_30d'] = grp.transform(
    lambda x: x.rolling(30, min_periods=1).mean())
df['roll_90d'] = grp.transform(
    lambda x: x.rolling(90, min_periods=1).mean())

# Momentum
df['momentum'] = df['modal_price'] - df['lag_30d']

# Volatility
df['volatility'] = grp.transform(
    lambda x: x.rolling(30, min_periods=1).std()
).fillna(0)

print("   Lag features done.")

# ─────────────────────────────────────────────────────────
# STEP 3: ENCODE CATEGORICAL COLUMNS
# ─────────────────────────────────────────────────────────
print("\n🔤 Encoding categoricals...")
encoders = {}
for col in ['state', 'district', 'market',
            'commodity', 'season']:
    le = LabelEncoder()
    df[f'{col}_enc'] = le.fit_transform(
        df[col].astype(str))
    encoders[col] = le
    print(f"   {col}: {len(le.classes_)} unique values")

# ─────────────────────────────────────────────────────────
# STEP 4: TRAIN MODEL
# ─────────────────────────────────────────────────────────
print("\n🧠 Training XGBoost model...")

FEATURES = [
    # Time
    'month', 'year', 'quarter', 'week', 'day_of_year',
    'season_enc', 'is_harvest',
    # Location & crop
    'state_enc', 'district_enc',
    'market_enc', 'commodity_enc',
    # Lag prices (most important)
    'lag_7d', 'lag_14d', 'lag_30d', 'lag_60d',
    # Rolling averages
    'roll_7d', 'roll_30d', 'roll_90d',
    # Other signals
    'momentum', 'volatility',
    'price_range', 'min_price', 'max_price'
]

# TIME-BASED split — never random for time series
cutoff = pd.Timestamp('2025-01-01')
train  = df[df['price_date'] <  cutoff]\
           .dropna(subset=FEATURES)
test   = df[df['price_date'] >= cutoff]\
           .dropna(subset=FEATURES)

print(f"   Train: {len(train):,} rows "
      f"(before {cutoff.date()})")
print(f"   Test:  {len(test):,}  rows "
      f"(from {cutoff.date()})")

model = XGBRegressor(
    n_estimators     = 500,
    learning_rate    = 0.05,
    max_depth        = 6,
    subsample        = 0.8,
    colsample_bytree = 0.8,
    min_child_weight = 3,
    random_state     = 42,
    n_jobs           = -1,
    verbosity        = 0
)

model.fit(
    train[FEATURES], train['modal_price'],
    eval_set=[(test[FEATURES], test['modal_price'])],
    verbose=100
)

# ─────────────────────────────────────────────────────────
# STEP 5: EVALUATE
# ─────────────────────────────────────────────────────────
preds = model.predict(test[FEATURES])
mae   = mean_absolute_error(test['modal_price'], preds)
r2    = r2_score(test['modal_price'], preds)
mape  = np.mean(
    np.abs((test['modal_price'] - preds) /
            test['modal_price'])
) * 100

print(f"\n📊 Model Performance:")
print(f"   MAE:  ₹{mae:.2f} per quintal")
print(f"   MAPE: {mape:.1f}%")
print(f"   R²:   {r2:.3f}")

# Top features
feat_imp = pd.Series(
    model.feature_importances_,
    index=FEATURES
).sort_values(ascending=False)
print(f"\n🔝 Top 5 Features:")
for feat, imp in feat_imp.head(5).items():
    print(f"   {feat}: {imp:.4f}")

# ─────────────────────────────────────────────────────────
# STEP 6: SAVE EVERYTHING
# ─────────────────────────────────────────────────────────
print(f"\n💾 Saving artifacts to {MODEL_DIR}/...")

joblib.dump(model,    f'{MODEL_DIR}/price_model.joblib')
joblib.dump(encoders, f'{MODEL_DIR}/encoders.joblib')
joblib.dump(FEATURES, f'{MODEL_DIR}/features.joblib')

# Save clean dataframe (needed for lag lookup in predict.py)
df.to_parquet(f'{MODEL_DIR}/clean_df.parquet', index=False)

print(f"   ✅ price_model.joblib")
print(f"   ✅ encoders.joblib")
print(f"   ✅ features.joblib")
print(f"   ✅ clean_df.parquet")
print(f"\n✅ Training complete! Run predict.py to test.")
