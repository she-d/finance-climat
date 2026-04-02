import streamlit as st

st.set_page_config(page_title="Climate Risk Dashboard", layout="wide")

st.title("Climate Risk Dashboard")

st.markdown("""
Welcome to the climate dashboard.

This application presents climate indicators through separate pages.

### Available pages
- Physical Risk
- WACI

### Goal
Help users understand:
- what each indicator measures,
- how to read it,
- which countries, sectors or assets are less risky,
- where a beginner investor could prioritize investment.

### General reading rule
For climate risk indicators:
- lower values = lower risk
- higher values = more caution needed
""")

st.info("Use the sidebar to open an indicator page.")
