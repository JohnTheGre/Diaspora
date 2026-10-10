
import pandas as pd

from database import SessionLocal, Base, engine
from models import Country, DiasporaPopulation

CSV_PATH = "data/globe_diaspora_seed.csv"

# Creates missing tables, but does not update existing table schemas.
DiasporaPopulation.__table__.drop(engine, checkfirst=True)
Base.metadata.create_all(bind=engine)

df = pd.read_csv(CSV_PATH)

required_columns = {
    "origin_country",
    "origin_iso3",
    "destination_country",
    "destination_iso3",
    "diaspora_population_estimate",
    "estimate_year",
    "record_status",
    "confidence",
    "source_url",
}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(f"CSV is missing columns: {sorted(missing)}")

db = SessionLocal()

added = 0
skipped = 0

try:
    # Replace the current imported dataset.
    db.query(DiasporaPopulation).delete()

    for row in df.to_dict("records"):
        origin_iso3 = str(row["origin_iso3"]).strip().upper()
        destination_iso3 = str(row["destination_iso3"]).strip().upper()

        if not origin_iso3 or origin_iso3 == "NAN":
            skipped += 1
            continue

        if not destination_iso3 or destination_iso3 == "NAN":
            skipped += 1
            continue

        # Find the destination country already in the database.
        destination = (
            db.query(Country)
            .filter(Country.iso_code == destination_iso3)
            .first()
        )

        # Add a country record if height/weight imports did not create it.
        if destination is None:
            destination_name = str(
                row["destination_country"]
            ).strip()

            # Avoid creating a duplicate country name under another code.
            same_name = (
                db.query(Country)
                .filter(Country.name == destination_name)
                .first()
            )

            if same_name is not None:
                print(
                    f"Skipping {destination_name}: name exists with "
                    f"ISO code {same_name.iso_code}, but CSV uses "
                    f"{destination_iso3}"
                )
                skipped += 1
                continue

            destination = Country(
                iso_code=destination_iso3,
                name=destination_name
            )
            db.add(destination)
            db.flush()

        estimate = row["diaspora_population_estimate"]
        year = row["estimate_year"]

        population_count = (
            None if pd.isna(estimate) else int(estimate)
        )
        estimate_year = None if pd.isna(year) else int(year)

        record = DiasporaPopulation(
            country_id=destination.id,
            origin_country=str(row["origin_country"]),
            origin_iso3=origin_iso3,
            destination_country=str(row["destination_country"]),
            destination_iso3=destination_iso3,
            population_count=population_count,
            estimate_year=estimate_year,
            record_status=str(row["record_status"]),
            confidence=(
                None if pd.isna(row["confidence"])
                else str(row["confidence"])
            ),
            source_url=(
                None if pd.isna(row["source_url"])
                else str(row["source_url"])
            ),
        )

        db.add(record)
        added += 1

    db.commit()

except Exception:
    db.rollback()
    raise

finally:
    db.close()

print(f"Imported {added} diaspora records.")
print(f"Skipped {skipped} records.")