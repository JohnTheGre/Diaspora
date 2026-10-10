import pandas as pd
import pycountry
from database import SessionLocal, engine, Base
from models import Country, LanguageSpeakers

# The table schema changed, so drop and recreate just this table
LanguageSpeakers.__table__.drop(engine, checkfirst=True)
Base.metadata.create_all(bind=engine)

MANUAL_ISO = {
    "Congo, Democratic Republic of the": "COD",
    "Congo, Republic of": "COG",
    "Korea, North": "PRK",
    "Korea, South": "KOR",
    "Kosovo": "KOS",  # no official ISO code; check what your geojson uses
    "Cape Verde": "CPV",
    "East Timor": "TLS",
    "Macedonia": "MKD",
    "Swaziland": "SWZ",
    "Micronesia": "FSM",
    "Palestinian State (proposed)": "PSE",
    "Vatican City (Holy See)": "VAT",
    "Western Sahara (proposed state)": "ESH",
    "St. Kitts and Nevis": "KNA",
    "St. Lucia": "LCA",
    "St. Vincent and the Grenadines": "VCT",
    "São Tomé and Príncipe": "STP",
    "Côte d'Ivoire": "CIV",
    "Russia": "RUS", "Syria": "SYR", "Iran": "IRN", "Laos": "LAO",
    "Brunei": "BRN", "Bolivia": "BOL", "Venezuela": "VEN",
    "Tanzania": "TZA", "Vietnam": "VNM", "Moldova": "MDA",
    "Taiwan": "TWN", "Czech Republic": "CZE",
}

def to_iso(name):
    if name in MANUAL_ISO:
        return MANUAL_ISO[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        try:
            return pycountry.countries.search_fuzzy(name)[0].alpha_3
        except LookupError:
            return None

def parse_pct(v):
    if pd.isna(v):
        return None
    try:
        return float(str(v).replace("%", "").strip())
    except ValueError:
        return None

df = pd.read_csv("data/country_languages.csv")

db = SessionLocal()
unmatched, added = [], 0

for _, row in df.iterrows():
    iso = to_iso(row["Country"])
    if not iso:
        unmatched.append(row["Country"])
        continue

    country = db.query(Country).filter(Country.iso_code == iso).first()
    if not country:
        country = Country(iso_code=iso, name=row["Country"])
        db.add(country)
        db.flush()  # get country.id

    for rank in range(1, 5):
        lang = row.get(f"L{rank}")
        pct = parse_pct(row.get(f"L{rank} %"))
        if pd.isna(lang) or pct is None:
            continue
        db.add(LanguageSpeakers(
            country_id=country.id,
            language=str(lang).strip(),
            rank=rank,
            percentage=pct,
        ))
        added += 1

db.commit()
db.close()
print(f" Added {added} language rows.")
if unmatched:
    print("⚠️ No ISO match for:", unmatched)