import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
from pytrends import exceptions as pyex
from io import BytesIO
import time, random
import requests

st.set_page_config(page_title="The G-Trendalyser", layout="centered")

# --- Title & intro
st.title("The G-Trendalyser 2.0🐍🔥")
st.subheader("Discover your Top & Rising Google Trends⚡")
st.markdown(
    "by Orit Mutznik, GitHub repo: @oritsimu-new Socials: @oritsimu"
)
st.markdown(
    """
Get your Top & Rising trends for 5 keywords, directly from Google Trends, no coding needed.

To get started:
- Paste 1 keyword per line (up to 5 keywords)📝
- Pick your country (geo)🌎
- Pick timeframe⏱️
- Hit Get Trevnds🤘
- Wait for a few moments⏳  (the longer the timeframe, the longer it takes)
- Scroll through the results tables (optional)📈
- Export your results in xlsx or csv format📊 or scroll down to the bottom to copy everything to clipboard
- If you get a 429 error due to too many requests, refresh the browser or connect to vpn and you're good to go!🤘

Each keyword can return up to 25 Top and up to 25 Rising related queries.
Value is not search volume. It is a score from Google that signals how trending a query is.
"""
)

# --- Inputs
keywords_input = st.text_area(
    "Paste up to 5 keywords (1 per line)",
    placeholder="e.g.\nshoes\nsummer dresses\ntrainers\n..."
)

# Country selector - keep list exactly as you had
country_options = [
    ('United States', 'US'), ('United Kingdom', 'GB'), ('India', 'IN'), ('Brazil', 'BR'), ('Germany', 'DE'),
    ('France', 'FR'), ('Japan', 'JP'), ('Canada', 'CA'), ('Australia', 'AU'), ('South Korea', 'KR'),
    ('Mexico', 'MX'), ('Italy', 'IT'), ('Spain', 'ES'), ('---', '---'), ('Argentina', 'AR'), ('Australia', 'AU'),
    ('Austria', 'AT'), ('Belgium', 'BE'), ('Brazil', 'BR'), ('Canada', 'CA'), ('Chile', 'CL'), ('Colombia', 'CO'),
    ('Czech Republic', 'CZ'), ('Denmark', 'DK'), ('Egypt', 'EG'), ('Finland', 'FI'), ('France', 'FR'), ('Germany', 'DE'),
    ('Greece', 'GR'), ('Hungary', 'HU'), ('India', 'IN'), ('Indonesia', 'ID'), ('Ireland', 'IE'), ('Israel', 'IL'),
    ('Italy', 'IT'), ('Japan', 'JP'), ('Malaysia', 'MY'), ('Mexico', 'MX'), ('Netherlands', 'NL'), ('New Zealand', 'NZ'),
    ('Norway', 'NO'), ('Pakistan', 'PK'), ('Peru', 'PE'), ('Philippines', 'PH'), ('Poland', 'PL'), ('Portugal', 'PT'),
    ('Romania', 'RO'), ('Russia', 'RU'), ('Saudi Arabia', 'SA'), ('Singapore', 'SG'), ('South Africa', 'ZA'),
    ('South Korea', 'KR'), ('Spain', 'ES'), ('Sweden', 'SE'), ('Switzerland', 'CH'), ('Thailand', 'TH'), ('Turkey', 'TR'),
    ('Ukraine', 'UA'), ('United Arab Emirates', 'AE'), ('United Kingdom', 'GB'), ('United States', 'US'), ('Vietnam', 'VN')
]
selected_country = st.selectbox("Select Country", options=[label for label, _ in country_options])
geo_code = dict(country_options).get(selected_country, "")
# Guard the placeholder item
if geo_code == '---':
    geo_code = ""

# Timeframe selector - fix the "Last 5 years" token to a valid one without changing the label
timeframe_labels = {
    "Last hour": "now 1-H",
    "Last 4 hours": "now 4-H",
    "Last day": "now 1-d",
    "Last 7 days": "now 7-d",
    "Last 30 days": "today 1-m",
    "Last 90 days": "today 3-m",
    "Last 12 months": "today 12-m",
    "Last 5 years": "today 5-y",   # was "today+5-y" which causes errors
}
timeframe_label = st.selectbox("Choose Period", list(timeframe_labels.keys()))
timeframe = timeframe_labels[timeframe_label]

# --- Helpers
def format_top_value(v):
    try:
        return str(int(v))
    except Exception:
        return str(v)

def format_rising_change(v):
    if isinstance(v, str):
        if v.strip().lower() == "breakout":
            return "Breakout"
        try:
            return f"{int(float(v))}%"
        except Exception:
            return v
    try:
        if float(v) >= 5000:
            return "Breakout"
        return f"{int(float(v))}%"
    except Exception:
        return str(v)

# Keep results stable across reruns
if "results_top_df" not in st.session_state:
    st.session_state["results_top_df"] = None
if "results_rising_df" not in st.session_state:
    st.session_state["results_rising_df"] = None
if "results_combined_df" not in st.session_state:
    st.session_state["results_combined_df"] = None
if "export_csv_bytes" not in st.session_state:
    st.session_state["export_csv_bytes"] = None
if "export_xlsx_bytes" not in st.session_state:
    st.session_state["export_xlsx_bytes"] = None

# --- Robust fetcher that keeps your exact UI
MAX_TRIES = 6
BASE_SLEEP = 2.0

@st.cache
