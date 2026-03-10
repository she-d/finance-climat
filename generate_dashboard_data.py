import pandas as pd

# -------------------------
# Charger tes données WACI
# -------------------------

data = pd.read_csv("your_waci_dataset.csv")

# Exemple colonnes attendues :
# counterparty
# country
# sector
# latitude
# longitude
# exposure_value
# emissions
# revenue

# -------------------------
# Calcul intensité carbone
# -------------------------

data["intensity"] = data["emissions"] / (data["revenue"] / 1_000_000)

total_value = data["exposure_value"].sum()

data["weight"] = data["exposure_value"] / total_value

data["waci_contribution"] = data["weight"] * data["intensity"]

portfolio_waci = data["waci_contribution"].sum()

# -------------------------
# SUMMARY
# -------------------------

summary = pd.DataFrame({
    "metric": ["total_value", "total_emissions", "portfolio_indicator"],
    "value": [
        total_value,
        data["emissions"].sum(),
        portfolio_waci
    ]
})

summary.to_csv("dashboard_summary.csv", sep=";", index=False)

# -------------------------
# COUNTRY INDICATOR
# -------------------------

country = (
    data.groupby("country")["waci_contribution"]
    .sum()
    .reset_index()
)

country.rename(columns={"waci_contribution": "indicator"}, inplace=True)

country.to_csv("dashboard_country_indicator.csv", sep=";", index=False)

# -------------------------
# SECTOR INDICATOR
# -------------------------

sector = (
    data.groupby("sector")["waci_contribution"]
    .sum()
    .reset_index()
)

sector.rename(columns={"waci_contribution": "indicator"}, inplace=True)

sector.to_csv("dashboard_sector_indicator.csv", sep=";", index=False)

# -------------------------
# ASSETS DATA
# -------------------------

assets = data[[
    "counterparty",
    "latitude",
    "longitude",
    "exposure_value",
    "sector",
    "country"
]]

assets.rename(columns={"counterparty": "name"}, inplace=True)

assets.to_csv("dashboard_assets.csv", sep=";", index=False)

print("Dashboard data generated successfully")