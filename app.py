import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Climate Risk Dashboard", layout="wide")

st.title("Climate Transition Risk Dashboard : WACI")

# Chargement des données
assets = pd.read_csv("dashboard_assets.csv", sep=";")
country = pd.read_csv("dashboard_country_indicator.csv", sep=";")
sector = pd.read_csv("dashboard_sector_indicator.csv", sep=";")
summary_raw = pd.read_csv("dashboard_summary.csv", sep=";")

summary = summary_raw.set_index("metric")["value"]

total_value = summary["total_value"]
total_emissions = summary["total_emissions"]
indicator = summary["portfolio_indicator"]

# Portfolio Summary
st.header("Portfolio Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Value", f"{total_value:,.0f}")
col2.metric("Total Emissions", f"{total_emissions:,.0f}")
col3.metric("Portfolio Indicator", f"{indicator:.3f}")

st.caption("WACI = Σ(weight_i × carbon intensity_i)")

# Assets Map
st.header("Assets Map")

fig_map = px.scatter_mapbox(
    assets,
    lat="latitude",
    lon="longitude",
    size="exposure_value",
    color="sector",
    hover_name="name",
    hover_data=["country", "exposure_value"],
    zoom=2,
    height=600
)

fig_map.update_layout(mapbox_style="carto-positron")

st.plotly_chart(fig_map, use_container_width=True)

# Risk by Country
st.header("WACI by Country")

fig_country = px.bar(
    country.sort_values("indicator", ascending=False).head(20),
    x="country",
    y="indicator"
)

st.plotly_chart(fig_country, use_container_width=True)

# Risk by Sector
st.header("WACI by Sector")

fig_sector = px.bar(
    sector.sort_values("indicator", ascending=False),
    x="sector",
    y="indicator"
)

st.plotly_chart(fig_sector, use_container_width=True)

# Assets Data
st.header("Assets Data")

st.dataframe(assets.head(1000), use_container_width=True)