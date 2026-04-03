# -- coding: utf-8 --
import pandas as pd
import numpy as np
from pathlib import Path

def parse_fr_number(x):
    if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x):
        return float(x)
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    s = s.replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    s = s.replace(",", ".")
    return np.nan if s == "" else float(s)

def read_csv_robust(path: Path) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep)
            if df.shape[1] >= 5:
                print(f">>> CSV loaded with sep='{sep}', shape={df.shape}")
                return df
        except Exception:
            pass
    raise ValueError("Unable to read CSV (unknown separator).")

def main():
    print(">>> financed emissions generator started")

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data" / "financed_emissions"
    data_dir.mkdir(parents=True, exist_ok=True)

    input_path = data_dir / "financed_emission.csv"
    print(">>> input:", input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    df = read_csv_robust(input_path)

    COL_CP = "Entreprise"
    COL_YE = "Année émissions"
    COL_E  = "Emissions totales (S1,2,3,tCO2e)"
    COL_YD = "Année valeur entreprise"
    COL_D  = "Valeur totale"
    COL_V  = "Exposition (banque)"

    required = [COL_CP, COL_YE, COL_E, COL_YD, COL_D, COL_V]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    has_sector = "sector" in df.columns
    has_country = "country" in df.columns
    print(">>> has_sector:", has_sector, "| has_country:", has_country)

    df["E_total"] = df[COL_E].apply(parse_fr_number)
    df["D_value"] = df[COL_D].apply(parse_fr_number)
    df["V_expo"]  = df[COL_V].apply(parse_fr_number)

    df["excluded_reason"] = ""
    df.loc[df[COL_CP].isna() | (df[COL_CP].astype(str).str.strip() == ""), "excluded_reason"] = "missing_counterparty"
    df.loc[df["V_expo"].isna() | (df["V_expo"] < 0), "excluded_reason"] = df["excluded_reason"].where(df["excluded_reason"] != "", "missing_or_invalid_exposure")
    df.loc[df["D_value"].isna() | (df["D_value"] <= 0), "excluded_reason"] = df["excluded_reason"].where(df["excluded_reason"] != "", "missing_or_invalid_denominator")
    df.loc[df["E_total"].isna() | (df["E_total"] < 0), "excluded_reason"] = df["excluded_reason"].where(df["excluded_reason"] != "", "missing_or_invalid_emissions")

    df["is_in_scope"] = df["excluded_reason"].eq("")
    df["time_mismatch_flag"] = df[COL_YE].astype("Int64") != df[COL_YD].astype("Int64")

    df["AF"] = np.where(df["is_in_scope"], df["V_expo"] / df["D_value"], np.nan)
    df["financed_emissions"] = np.where(df["is_in_scope"], df["AF"] * df["E_total"], np.nan)

    total_exposure = df["V_expo"].sum()
    in_scope_exposure = df.loc[df["is_in_scope"], "V_expo"].sum()
    coverage = in_scope_exposure / total_exposure if total_exposure else np.nan
    fe_total = df.loc[df["is_in_scope"], "financed_emissions"].sum()
    avg_af = df.loc[df["is_in_scope"], "AF"].mean() if df["is_in_scope"].any() else np.nan
    mismatch_share = df.loc[df["is_in_scope"], "time_mismatch_flag"].mean() if df["is_in_scope"].any() else np.nan

    summary = pd.DataFrame({
        "metric": ["reporting_year","total_exposure_eur","in_scope_exposure_eur","coverage_pct","financed_emissions_total_tco2e","avg_attribution_factor","time_mismatch_share"],
        "value": [int(df[COL_YE].dropna().iloc[0]) if len(df[COL_YE].dropna()) else "", total_exposure, in_scope_exposure, coverage, fe_total, avg_af, mismatch_share]
    })
    summary.to_csv(data_dir / "dashboard_summary.csv", sep=";", index=False)
    print(">>> wrote dashboard_summary.csv")

    counterparty = pd.DataFrame({
        "counterparty": df[COL_CP],
        "country": df["country"] if has_country else "N/A",
        "sector": df["sector"] if has_sector else "N/A",
        "exposure_eur": df["V_expo"],
        "denominator_eur": df["D_value"],
        "af": df["AF"],
        "emissions_total_tco2e": df["E_total"],
        "financed_emissions_tco2e": df["financed_emissions"],
        "emissions_year": df[COL_YE],
        "denominator_year": df[COL_YD],
        "time_mismatch_flag": df["time_mismatch_flag"],
        "excluded_reason": df["excluded_reason"],
    })
    counterparty.to_csv(data_dir / "dashboard_counterparty_indicator.csv", sep=";", index=False)
    print(">>> wrote dashboard_counterparty_indicator.csv")

    if has_country:
        country = (df[df["is_in_scope"]].groupby("country")["financed_emissions"].sum().reset_index().rename(columns={"financed_emissions":"indicator"}))
    else:
        country = pd.DataFrame([{"country":"N/A","indicator":fe_total}])
    country.to_csv(data_dir / "dashboard_country_indicator.csv", sep=";", index=False)
    print(">>> wrote dashboard_country_indicator.csv")

    if has_sector:
        sector = (df[df["is_in_scope"]].groupby("sector")["financed_emissions"].sum().reset_index().rename(columns={"financed_emissions":"indicator"}))
    else:
        sector = pd.DataFrame([{"sector":"N/A","indicator":fe_total}])
    sector.to_csv(data_dir / "dashboard_sector_indicator.csv", sep=";", index=False)
    print(">>> wrote dashboard_sector_indicator.csv")

    assets = counterparty[["counterparty","country","sector","exposure_eur","financed_emissions_tco2e"]].copy()
    assets.rename(columns={"counterparty":"name"}, inplace=True)
    assets.to_csv(data_dir / "dashboard_assets.csv", sep=";", index=False)
    print(">>> wrote dashboard_assets.csv")

    exclusions = (df[~df["is_in_scope"]].groupby("excluded_reason", dropna=False)["V_expo"].agg(exposure_eur="sum", rows="size").reset_index().sort_values("exposure_eur", ascending=False))
    exclusions.to_csv(data_dir / "dashboard_exclusions.csv", sep=";", index=False)
    print(">>> wrote dashboard_exclusions.csv")

    print("✅ DONE")

if __name__ == "__main__":
    main()
