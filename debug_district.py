"""
Run: python debug_district.py <pincode>
Shows what district/state we resolve from pincode, what normalize_district returns,
and whether that name exists in the centroid CSV.

Example: python debug_district.py 641001
"""
import sys, os, csv, pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── Load pincode CSV ──
pin = sys.argv[1] if len(sys.argv) > 1 else "641001"
pincode_csv = "datasets/india pincode final.csv"
centroid_csv = "datasets/district wise centroids.csv"

# Read pincode → district
db = {}
with open(pincode_csv, newline="", encoding="latin-1") as f:
    for row in csv.DictReader(f):
        p = str(row.get("pincode", "")).strip().zfill(6)
        d = row.get("Districtname", "").strip()
        s = row.get("statename", "").strip().title()
        if p and d:
            db[p] = (d, s)

raw_district, state = db.get(pin, (None, None))
print(f"\nPincode       : {pin}")
print(f"Raw district  : {raw_district!r}")
print(f"State         : {state!r}")

if raw_district is None:
    print("❌ Pincode not found in CSV")
    sys.exit(1)

# DISTRICT_ALIASES from sms_handler
DISTRICT_ALIASES = {
    "east champaran": "Purba Champaran", "west champaran": "Pashchim Champaran",
    "central delhi": "Delhi", "east delhi": "Delhi", "new delhi": "Delhi",
    "north delhi": "Delhi", "north west delhi": "Delhi", "south delhi": "Delhi",
    "south west delhi": "Delhi", "west delhi": "Delhi",
    "ahmedabad": "Ahmadabad", "banaskantha": "Banas Kantha",
    "tiruchirappalli": "Tiruchchirappalli", "tiruchirapalli": "Tiruchchirappalli",
    "tirunelveli": "Tirunelveli Kattabo", "tiruvallur": "Thiruvallur",
    "tiruvarur": "Thiruvarur", "kancheepuram": "Kancheepuram",
    "the nilgiris": "Nilgiris", "tuticorin": "Thoothukudi",
    "kanyakumari": "Kanniyakumari", "chengalpattu": "Kancheepuram",
    "tiruppur": "Tirupur", "beed": "Bid", "gondia": "Gondiya",
    "mumbai": "Greater Bombay", "dehradun": "Dehra Dun",
    "nainital": "Naini Tal", "howrah": "Haora", "malda": "Maldah",
}

key = raw_district.strip().lower()
normalized = DISTRICT_ALIASES.get(key, raw_district.strip().title())
print(f"Normalized    : {normalized!r}")

# Check centroid CSV
centroids = pd.read_csv(centroid_csv)
centroids.columns = centroids.columns.str.strip()
centroids['District'] = centroids['District'].str.strip().str.title()

match_exact = centroids[centroids['District'].str.lower() == normalized.lower()]
print(f"\nCentroid match: {len(match_exact)} rows found for '{normalized}'")
if not match_exact.empty:
    print(f"  → {match_exact[['District','State','Latitude','Longitude']].to_string(index=False)}")
else:
    print("  ❌ NOT FOUND — all distances will be 999 → 0 results!")
    # Show closest matches
    close = centroids[centroids['District'].str.lower().str.startswith(normalized.lower()[:4])]
    if not close.empty:
        print(f"\nDid you mean one of these?")
        print(close[['District','State']].drop_duplicates().to_string(index=False))
