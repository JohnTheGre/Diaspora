import pandas as pd

height_df = pd.read_csv("data/NCD_RisC_Lancet_2020_height_child_adolescent_country.csv")
print("=== Height age groups ===")
print(height_df["Age group"].unique())
print("\n=== Height sample rows ===")
print(height_df.head())

bmi_df = pd.read_csv("data/NCD_RisC_Nature_2026_BMI_female_age_specific_country.csv")
print("\n=== BMI age groups ===")
print(bmi_df["Age group"].unique())
print("\n=== BMI sample rows ===")
print(bmi_df.head())

language_df = pd.read_csv("data/countries_languages.csv")
print("\n=== Languages ===")
print(language_df.head(10))
print("\n=== Non-null counts ===")
print(language_df.count())
print("\n=== Sample of filled Population L1 values ===")
print(language_df[language_df["Population L1"].notna()][["Country", "L1", "Population L1"]].head(20))

diaspra_df = pd.read_csv("data/globe_diaspora_seed.csv")
print("\n=== Diaspora population sample rows ===")
print(diaspra_df.head())
print("\n=== Diaspora population non-null counts ===")
print(diaspra_df.count())
