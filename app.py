import streamlit as st
import pandas as pd
import time
from pytrends.request import TrendReq
from pytrends import exceptions as pytrends_exceptions # Import pytrends exceptions
from io import BytesIO

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
- Hit Get Trends🤘
- Wait for a few moments⏳  (the longer the timeframe, the longer it takes)
- Scroll through the results tables (optional)📈
- Export your results in xlsx or csv format📊 or scroll down to the bottom to copy everything to clipboard

Each keyword can return up to 25 Top and up to 25 Rising related queries.
Value is not search volume. It is a score from Google that signals how trending a query is.

**⚠️ Note on Stability & Timeouts:** This app includes automatic retry logic to better handle temporary network issues and Google's rate limits (Too Many Requests/429 errors). If the fetch fails after multiple retries, please wait **5-10 minutes** before attempting again.
"""
)

# --- Inputs
keywords_input = st.text_area(
    "Paste up to 5 keywords (1 per line)",
    placeholder="e.g.\nshoes\nsummer dresses\ntrainers\n..."
)

# Country selector
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

# Timeframe selector
timeframe_labels = {
    "Last hour": "now 1-H",
    "Last 4 hours": "now 4-H",
    "Last day": "now 1-d",
    "Last 7 days": "now 7-d",
    "Last 30 days": "today 1-m",
    "Last 90 days": "today 3-m",
    "Last 12 months": "today 12-m",
    "Last 5 years": "today+5-y",
}
timeframe_label = st.selectbox("Choose Period", list(timeframe_labels.keys()))
timeframe = timeframe_labels[timeframe_label]

# --- Helpers
def format_top_value(v):
    """Formats the 'value' column for Top queries (score)."""
    try:
        return str(int(v))
    except Exception:
        return str(v)

def format_rising_change(v):
    """Formats the 'change' column for Rising queries."""
    if isinstance(v, str):
        if v.strip().lower() == "breakout":
            return "Breakout"
        try:
            return f"{int(float(v))}%"
        except Exception:
            return v
    try:
        # Pytrends uses a high value (like 5000) for 'Breakout' when the change is > 5000%
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

# --- Fetch button row
col_get, col_csv, col_xlsx = st.columns([1, 1, 1])
get_trends = col_get.button("Get Trends🤘")
slot_top_csv = col_csv.empty()
slot_top_xlsx = col_xlsx.empty()

if get_trends:
    if not keywords_input.strip():
        st.warning("Please input at least 1 keyword.")
    else:
        kw_list = [kw.strip().lower() for kw in keywords_input.strip().split("\n") if kw.strip()]
        if len(kw_list) > 5:
            st.error("This app is restricted to 5 keywords only. Please reduce your input.")
        else:
            pytrends = TrendReq(hl="en-US", tz=360)
            
            # --- Robustness Implementation ---
            MAX_RETRIES = 5
            INITIAL_DELAY = 5 # seconds
            related_queries = None
            
            with st.spinner("Fetching data from Google Trends..."):
                for attempt in range(MAX_RETRIES):
                    try:
                        current_delay = INITIAL_DELAY * (2 ** attempt) # Exponential backoff
                        
                        # 1. Build Payload
                        pytrends.build_payload(kw_list, timeframe=timeframe, geo=geo_code)
                        
                        # 2. Get Related Queries
                        related_queries = pytrends.related_queries()

                        # Success!
                        break 
                        
                    except pytrends_exceptions.TooManyRequestsError:
                        if attempt < MAX_RETRIES - 1:
                            st.warning(f"Rate limit hit (429). Retrying in {current_delay} seconds... (Attempt {attempt + 2} of {MAX_RETRIES})")
                            time.sleep(current_delay)
                        else:
                            st.error("Failed to fetch data after multiple retries due to rate limiting (429). Please wait 5-10 minutes and try again.")
                            st.stop() # Use st.stop() instead of return

                    except Exception as e:
                        # Catch other general exceptions (e.g., connection reset, DNS issues, general timeouts)
                        if attempt < MAX_RETRIES - 1:
                            st.warning(f"Connection error or timeout: {type(e).__name__}. Retrying in {current_delay} seconds... (Attempt {attempt + 2} of {MAX_RETRIES})")
                            time.sleep(current_delay)
                        else:
                            st.error(f"Failed to fetch data after multiple retries due to an unexpected error: {type(e).__name__} - {e}. Please try again.")
                            st.stop() # Use st.stop() instead of return
            
            if related_queries:
                st.success(f"Showing results for: {', '.join(kw_list)}")

                top_blocks = []
                rising_blocks = []
                combined_blocks = []

                for kw in kw_list:
                    st.subheader(f"Keyword: {kw}")
                    rq = related_queries.get(kw, {})
                    rising = rq.get("rising")
                    top = rq.get("top")

                    # On-screen Top table (no change column)
                    if top is not None and not top.empty:
                        top_disp = pd.DataFrame({
                            "query": top["query"],
                            "value": top["value"].apply(format_top_value),
                            "keyword": kw,
                            "type": "Top",
                        })[["query","value","keyword","type"]]
                        st.markdown("**Top Queries (up to 25)**")
                        st.dataframe(top_disp, use_container_width=True)
                        top_blocks.append(top_disp)

                        # For unified exports
                        top_export = top_disp.copy()
                        top_export["change"] = ""
                        combined_blocks.append(top_export[["query","value","keyword","type","change"]])
                    else:
                        st.info("No top queries found.")

                    # On-screen Rising table (no value column)
                    if rising is not None and not rising.empty:
                        rising_disp = pd.DataFrame({
                            "query": rising["query"],
                            "keyword": kw,
                            "type": "Rising",
                            "change": rising["value"].apply(format_rising_change),
                        })[["query","keyword","type","change"]]
                        st.markdown("**Rising Queries (up to 25)**")
                        st.dataframe(rising_disp, use_container_width=True)
                        rising_blocks.append(rising_disp)

                        # For unified exports
                        rise_export = rising_disp.copy()
                        rise_export["value"] = ""
                        rise_export = rise_export[["query","value","keyword","type","change"]]
                        combined_blocks.append(rise_export)
                    else:
                        st.info("No rising queries found.")

                st.session_state["results_top_df"] = pd.concat(top_blocks, ignore_index=True) if top_blocks else None
                st.session_state["results_rising_df"] = pd.concat(rising_blocks, ignore_index=True) if rising_blocks else None
                st.session_state["results_combined_df"] = pd.concat(combined_blocks, ignore_index=True) if combined_blocks else None


# If results exist, compute unified exports and show copy-all
combined_df = st.session_state.get("results_combined_df")
export_df = None
if combined_df is not None and not combined_df.empty:
    export_df = combined_df[["query","value","keyword","type","change"]]

    st.session_state["export_csv_bytes"] = export_df.to_csv(index=False).encode("utf-8")
    from io import BytesIO as _BIO
    with _BIO() as _buf:
        # Ensure xlsxwriter is available for Excel export
        try:
            with pd.ExcelWriter(_buf, engine="xlsxwriter") as _writer:
                export_df.to_excel(_writer, index=False, sheet_name="Trends")
            st.session_state["export_xlsx_bytes"] = _buf.getvalue()
        except ImportError:
            st.warning("Install 'xlsxwriter' to enable Excel downloads.")
            st.session_state["export_xlsx_bytes"] = None


    st.markdown("---")
    st.subheader("Copy all to clipboard")
    st.markdown("Hover to find the copy icon in the top right corner")
    st.code(export_df.to_csv(index=False), language="text")
# --- Render download buttons in fixed locations (top and bottom)
csv_bytes = st.session_state.get("export_csv_bytes")
xlsx_bytes = st.session_state.get("export_xlsx_bytes")
disabled_state = csv_bytes is None or (xlsx_bytes is None and csv_bytes is None) # Allow CSV download if XLSX failed

with slot_top_csv:
    st.download_button("Download Trends (CSV)", data=csv_bytes or b"", file_name="google_trends.csv", mime="text/csv", key="btn_csv_top", disabled=csv_bytes is None) # Only disable if no CSV data
with slot_top_xlsx:
    st.download_button("Download Trends (Excel)", data=xlsx_bytes or b"", file_name="google_trends.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="btn_xlsx_top", disabled=xlsx_bytes is None) # Only disable if no XLSX data

st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    st.download_button("Download Trends (CSV)", data=csv_bytes or b"", file_name="google_trends.csv", mime="text/csv", key="btn_csv_bottom", disabled=csv_bytes is None)
with b2:
    st.download_button("Download Trends (Excel)", data=xlsx_bytes or b"", file_name="google_trends.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="btn_xlsx_bottom", disabled=xlsx_bytes is None)
