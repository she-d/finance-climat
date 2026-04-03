import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

def show_financed_emissions_dashboard():
    st.header("Climate Transition Risk Dashboard : Financed Emissions")

    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data" / "financed_emissions"

    assets = pd.read_csv(data_dir / "dashboard_assets.csv", sep=";")
    country = pd.read_csv(data_dir / "dashboard_country_indicator.csv", sep=";")
    sector = pd.read_csv(data_dir / "dashboard_sector_indicator.csv", sep=";")
    exclusions = pd.read_csv(data_dir / "dashboard_exclusions.csv", sep=";")
    summary_raw = pd.read_csv(data_dir / "dashboard_summary.csv", sep=";")
    counterparty = pd.read_csv(data_dir / "dashboard_counterparty_indicator.csv", sep=";")

    summary = summary_raw.set_index("metric")["value"]

    total_exposure = float(summary["total_exposure_eur"])
    coverage = float(summary["coverage_pct"])
    fe_total = float(summary["financed_emissions_total_tco2e"])
    avg_af = float(summary["avg_attribution_factor"])
    mismatch_share = float(summary["time_mismatch_share"])

    st.subheader("Portfolio Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Exposure (EUR)", f"{total_exposure:,.0f}")
    c2.metric("Coverage (%)", f"{coverage*100:.1f}")
    c3.metric("Financed Emissions (tCO2e)", f"{fe_total:,.0f}")
    c4.metric("Average AF", f"{avg_af:.4f}")
    c5.metric("Year mismatch share", f"{mismatch_share*100:.1f}%")

    st.caption("Financed emissions = Emissions × (Bank exposure / Enterprise value)")

    st.subheader("Financed Emissions by Country")
    fig_country = px.bar(country.sort_values("indicator", ascending=False).head(20), x="country", y="indicator")
    st.plotly_chart(fig_country, width="stretch")

    st.subheader("Financed Emissions by Sector")
    fig_sector = px.bar(sector.sort_values("indicator", ascending=False).head(20), x="sector", y="indicator")
    st.plotly_chart(fig_sector, width="stretch")

    st.subheader("Top Counterparties")
    top = counterparty.sort_values("financed_emissions_tco2e", ascending=False).head(20)
    fig_cp = px.bar(top, x="counterparty", y="financed_emissions_tco2e")
    st.plotly_chart(fig_cp, width="stretch")

    st.subheader("Assets Data")
    st.dataframe(assets.head(1000), width="stretch")

    st.subheader("Exclusions by reason")
    if len(exclusions) > 0:
        fig_exc = px.bar(exclusions, x="excluded_reason", y="exposure_eur")
        st.plotly_chart(fig_exc, width="stretch")
        st.dataframe(exclusions, width="stretch")
    else:
        st.write("No exclusions.")
