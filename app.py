import streamlit as st
from indicators.waci import show_waci_dashboard
from indicators.financed_emissions import show_financed_emissions_dashboard

st.set_page_config(page_title="Climate Risk Dashboard", layout="wide")
st.title("Climate Risk Dashboard")

indicator = st.sidebar.selectbox(
    "Select indicator",
    ["WACI", "Financed Emissions"]
)

if indicator == "WACI":
    show_waci_dashboard()

if indicator == "Financed Emissions":
    show_financed_emissions_dashboard()
