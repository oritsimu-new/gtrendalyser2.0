import time
import random
import threading
from collections import deque
import hashlib
from typing import Dict, Any, Tuple, List

import streamlit as st
import pandas as pd

try:
    from pytrends.request import TrendReq
    from pytrends import exceptions as pyex
except Exception as _e:
    st.error("Failed to import pytrends. Make sure 'pytrends' is installed in your environment.")
    st.stop()

# -------------------------
# Config
# -------------------------
APP_TITLE = "G-Trendalyser 2.0 - Stable"
MAX_KEYWORDS = 5
CACHE_TTL_SECONDS = 60 * 60  # 1 hour
MAX_TRIES = 6
BASE_SLEEP = 2.0  # seconds for exponential backoff
MIN_GAP_SECONDS = 3.0  # throttle gap between network calls
DEFAULT_TIMEOUT = (10, 30)  # connect, read

# -------------------------
# Helpers: throttle and stores
# -------------------------
@st.cache_resource
def _lock() -> threading.Lock:
    return threading.Lock()

@st.cache_resource
def call_timestamps() -> deque:
    # Tracks last N call times to keep a small gap
    return deque(maxlen=16)

def throttle(min_gap: float = MIN_GAP_SECONDS):
    # Simple per-process throttle
    with _lock():
        tsq = call_timestamps()
        now = time.time()
        if tsq and now - tsq[-1] < min_gap:
            sleep_s = min_gap - (now - tsq[-1])
            time.sleep(max(0.0, sleep_s))
        tsq.append(time.time())

def _norm_inputs(kw_list: List[str], timeframe: str, geo_code: str) -> Tuple[Tuple[str, ...], str, str]:
    kw_norm = tuple([kw.strip().lower() for kw in kw_list if kw and kw.strip()])
    return kw_norm, timeframe.strip(), geo_code.strip()

def _key_for_cache(kw_list: List[str], timeframe: str, geo_code: str) -> str:
    kw_norm, tf, geo = _norm_inputs(kw_list, timeframe, geo_code)
    payload = "|".join(kw_norm) + "||" + tf + "||" + geo
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

@st.cache_resource
def stale_store() -> Dict[str, Dict[str, Any]]:
    # key -> result dict
    return {}

# -------------------------
# Data fetch with caching and retries
# -------------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_trends_data(kw_list: List[str], timeframe: str, geo_code: str) -> Dict[str, Any]:
    """Fetch data from Google Trends via pytrends.
    Returns a dict with keys: related_queries, interest_over_time, interest_by_region
    """
    # network throttle
    throttle()

    pytrends = TrendReq(
        hl="en-US",
        tz=0,                  # UTC
        timeout=DEFAULT_TIMEOUT,
        retries=5,             # internal retries in requests
        backoff_factor=0.5     # internal backoff
    )

    tries = 0
    last_err = None
    while tries < MAX_TRIES:
        try:
            pytrends.build_payload(kw_list, timeframe=timeframe, geo=geo_code)
            # Collect a few popular endpoints
            rq = pytrends.related_queries()
            iot = pytrends.interest_over_time()
            try:
                ibr = pytrends.interest_by_region(resolution="COUNTRY", inc_low_vol=True)
            except Exception:
                ibr = pd.DataFrame()

            return {
                "related_queries": rq,
                "interest_over_time": iot,
                "interest_by_region": ibr
            }
        except pyex.TooManyRequestsError as e:
            last_err = e
            sleep_s = BASE_SLEEP * (2 ** tries) + random.uniform(0, 1.5)
            st.info(f"Google is throttling requests. Auto-retry in ~{sleep_s:.0f}s...")
            time.sleep(sleep_s)
            tries += 1
        except Exception as e:
            # Non rate-limit errors should surface to the caller
            raise e

    # If all retries failed, re-raise a clean TooManyRequestsError
    raise pyex.TooManyRequestsError("Google Trends is rate-limiting right now. Please try again later.")

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
ston = st.title(APP_TITLE)
st.caption("Stable build with retries, caching, throttle, and graceful fallbacks.")

# Country options
country_options = [
    ("Worldwide", ""),
    ("United Kingdom", "GB"),
    ("United States", "US"),
    ("Canada", "CA"),
    ("Australia", "AU"),
    ("Germany", "DE"),
    ("France", "FR"),
    ("Spain", "ES"),
    ("Italy", "IT"),
    ("Netherlands", "NL"),
    ("Brazil", "BR"),
    ("India", "IN"),
    ("Japan", "JP"),
]

timeframe_labels = {
    "Past 7 days": "now 7-d",
    "Past 30 days": "today 1-m",
    "Past 90 days": "today 3-m",
    "Past 12 months": "today 12-m",
    "Past 5 years": "today 5-y",
    "2004 - present": "all",
}

# Ensure busy flag
if "busy" not in st.session_state:
    st.session_state.busy = False

# Controls in a form to debounce
with st.form("controls"):
    st.subheader("Query")
    default_text = "nike\nadidas"  # example placeholders
    keywords_input = st.text_area("Up to 5 keywords - 1 per line", value=default_text, height=120, help="Paste up to 5 keywords. Lines that are empty will be ignored.")
    country_label = st.selectbox("Country", options=[label for label, _ in country_options], index=1)
    timeframe_label = st.selectbox("Timeframe", options=list(timeframe_labels.keys()), index=0)
    submitted = st.form_submit_button("Get Trends", disabled=st.session_state.busy)

# Resolve selected values
geo_code = dict(country_options)[country_label]
timeframe = timeframe_labels[timeframe_label]

# Normalize keywords
kw_list = [kw.strip() for kw in keywords_input.splitlines() if kw.strip()]
kw_list = kw_list[:MAX_KEYWORDS]

# Main execution
if submitted:
    st.session_state.busy = True
    left, right = st.columns([0.6, 0.4])
    with left:
        if not kw_list:
            st.warning("Please input at least 1 keyword.")
            st.session_state.busy = False
            st.stop()

        if len(kw_list) > MAX_KEYWORDS:
            st.error(f"This app allows up to {MAX_KEYWORDS} keywords. Please reduce your input.")
            st.session_state.busy = False
            st.stop()

        cache_key = _key_for_cache(kw_list, timeframe, geo_code)
        with st.spinner("Fetching data from Google Trends..."):
            try:
                data = fetch_trends_data(kw_list, timeframe, geo_code)
                # Update stale store on success
                stale_store()[cache_key] = data
                st.success("Success")
            except pyex.TooManyRequestsError:
                # Try to serve stale
                stale = stale_store().get(cache_key)
                if stale:
                    st.info("Showing cached results from a recent successful run because Google is rate-limiting right now.")
                    data = stale
                else:
                    st.warning("Google Trends is rate-limiting right now. Please wait a bit and try again or reduce keywords.")
                    st.session_state.busy = False
                    st.stop()
            except Exception as e:
                st.error("Unexpected error while fetching data. Please try again later.")
                st.session_state.busy = False
                st.stop()

        # Render results
        rq = data.get("related_queries", {})
        iot = data.get("interest_over_time", pd.DataFrame())
        ibr = data.get("interest_by_region", pd.DataFrame())

        st.subheader("Related queries")
        if isinstance(rq, dict) and rq:
            # rq structure: {kw: {"top": df, "rising": df}, ...}
            for kw, parts in rq.items():
                st.markdown(f"**{kw}**")
                top_df = parts.get("top") if parts else None
                rising_df = parts.get("rising") if parts else None
                if isinstance(top_df, pd.DataFrame) and not top_df.empty:
                    st.write("Top")
                    st.dataframe(top_df.reset_index(drop=True), use_container_width=True)
                else:
                    st.write("No top queries")
                if isinstance(rising_df, pd.DataFrame) and not rising_df.empty:
                    st.write("Rising")
                    st.dataframe(rising_df.reset_index(drop=True), use_container_width=True)
                else:
                    st.write("No rising queries")
                st.divider()
        else:
            st.write("No related queries returned.")

        st.subheader("Interest over time")
        if isinstance(iot, pd.DataFrame) and not iot.empty:
            st.line_chart(iot.drop(columns=[c for c in ["isPartial"] if c in iot.columns], errors="ignore"))
        else:
            st.write("No time series returned.")

        st.subheader("Interest by region")
        if isinstance(ibr, pd.DataFrame) and not ibr.empty:
            st.dataframe(ibr.sort_index().reset_index(), use_container_width=True)
        else:
            st.write("No regional data returned.")

    with right:
        st.subheader("Run details")
        st.write(f"Keywords: {', '.join(kw_list)}")
        st.write(f"Geo: {country_label} ({geo_code or 'Worldwide'})")
        st.write(f"Timeframe: {timeframe_label} ({timeframe})")
        st.caption("Tips: reduce keywords, shorten timeframe, and avoid repeated runs in quick succession to reduce rate-limits.")

    st.session_state.busy = False

# Footer note
st.caption("If you see repeated rate-limit notices, try again in a few minutes. The app will serve stale results when possible.")
