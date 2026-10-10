import pandas as pd
from database import SessionLocal, engine, Base
from models import Country

Base.metadata.create_all(bind=engine)

# --- Load height data ---
height_df = pd.read_csv("data/NCD_RisC_Lancet_2020_height_child_adolescent_country.csv")
height_df = height_df[height_df["Age group"] == 19]
latest_year = height_df["Year"].max()
height_df = height_df[height_df["Year"] == latest_year]

height_avg = (
    height_df.groupby("Country")["Mean height"]
    .mean()  # averages Boys + Girls
    .reset_index()
    .rename(columns={"Mean height": "avg_height_cm"})
)

# --- Load BMI data (male + female) ---
bmi_female = pd.read_csv("data/NCD_RisC_Nature_2026_BMI_female_age_specific_country.csv")
bmi_male = pd.read_csv("data/NCD_RisC_Nature_2026_BMI_male_age_specific_country.csv")

bucket_cols = {
    "Prevalence of BMI<18.5 kg/m² (underweight)": 17.0,
    "Prevalence of BMI 18.5 kg/m² to <20 kg/m²": 19.25,
    "Prevalence of BMI 20 kg/m² to <25 kg/m²": 22.5,
    "Prevalence of BMI 25 kg/m² to <30 kg/m²": 27.5,
    "Prevalence of BMI 30 kg/m² to <35 kg/m²": 32.5,
    "Prevalence of BMI 35 kg/m² to <40 kg/m²": 37.5,
    "Prevalence of BMI >=40 kg/m² (morbid obesity)": 42.0,
}

def estimate_mean_bmi(df):
    df = df[df["Age group"] == "18-19"]
    latest = df["Year"].max()
    df = df[df["Year"] == latest].copy()

    df["mean_bmi"] = 0
    for col, midpoint in bucket_cols.items():
        df["mean_bmi"] += df[col] * midpoint

    return df[["Country/Region/World", "ISO", "mean_bmi"]].rename(
        columns={"Country/Region/World": "Country"}
    )

bmi_f = estimate_mean_bmi(bmi_female)
bmi_m = estimate_mean_bmi(bmi_male)

bmi_combined = pd.merge(bmi_f, bmi_m, on=["Country", "ISO"], suffixes=("_f", "_m"))
bmi_combined["avg_bmi"] = bmi_combined[["mean_bmi_f", "mean_bmi_m"]].mean(axis=1)
bmi_combined = bmi_combined[["Country", "ISO", "avg_bmi"]]

# --- Normalize mismatched country names (BMI file -> height file naming) ---
name_fixes = {
    "Czechia": "Czech Republic",
    "Eswatini": "Swaziland",
    "Federated States of Micronesia": "Micronesia (Federated States of)",
    "North Macedonia": "Macedonia (TFYR)",
    "Palestine": "Occupied Palestinian Territory",
    "Turkiye": "Turkey",
    # South Sudan has no match in the height dataset — leave it, will be dropped
}
bmi_combined["Country"] = bmi_combined["Country"].replace(name_fixes)

# --- Merge height + BMI by country name ---
merged = pd.merge(height_avg, bmi_combined, on="Country", how="inner")

unmatched_height = set(height_avg["Country"]) - set(merged["Country"])
unmatched_bmi = set(bmi_combined["Country"]) - set(merged["Country"])
if unmatched_height or unmatched_bmi:
    print(f"⚠️  {len(unmatched_height)} countries in height data had no BMI match:")
    print(sorted(unmatched_height))
    print(f"\n⚠️  {len(unmatched_bmi)} countries in BMI data had no height match:")
    print(sorted(unmatched_bmi))

# --- Estimate weight from BMI + height ---
merged["avg_weight_kg"] = merged["avg_bmi"] * (merged["avg_height_cm"] / 100) ** 2

# --- Insert into database ---
db = SessionLocal()
inserted = 0
for _, row in merged.iterrows():
    existing = db.query(Country).filter(Country.iso_code == row["ISO"]).first()
    if existing:
        existing.avg_height_cm = round(row["avg_height_cm"], 1)
        existing.avg_weight_kg = round(row["avg_weight_kg"], 1)
    else:
        db.add(Country(
            iso_code=row["ISO"],
            name=row["Country"],
            avg_height_cm=round(row["avg_height_cm"], 1),
            avg_weight_kg=round(row["avg_weight_kg"], 1),
        ))
    inserted += 1

db.commit()
db.close()
print(f"\n✅ Inserted/updated {inserted} countries.")


