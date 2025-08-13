
import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
from io import BytesIO

st.set_page_config(page_title="The G-Trendalyser", layout="centered")

# --- Title & intro
st.title("The G-Trendalyser 2.0🐍🔥")
st.subheader("Discover your Top & Rising Google Trends⚡")
st.markdown(
    """by Orit Mutznik, @oritsimu-new, @oritsimu"""
)
st.markdown(
    """
Get your Top & Rising trends for 5 keywords, directly from Google Trends, no coding needed 😎.

To get started:
- Paste **1 keyword per line** (up to 5 keywords)📝
- Pick your country (geo)🌎
- Pick timeframe⏱️
- Hit **Get Trends! 🤘**
- Wait for a few moments⏳ (the longer the timeframe, the longer it takes)
- Scroll through the restuls tables (optional)📈
- Export your results in xlsx or csv format📊

Each keyword can return up to **25 Top** and **25 Rising** related queries.
_Value is not search volume. It is a score from Google that signals how trending a query is._
"""
)

# --- Inputs
keywords_input = st.text_area(
    "Paste up to 5 keywords (1 per line)",
    placeholder="e.g.\nshoes\nsummer dresses\ntrainers\n..."
)

# Country selector
country_options = [('United States', 'US'), ('United Kingdom', 'GB'), ('India', 'IN'), ('Brazil', 'BR'), ('Germany', 'DE'), ('France', 'FR'), ('Japan', 'JP'), ('Canada', 'CA'), ('Australia', 'AU'), ('South Korea', 'KR'), ('Mexico', 'MX'), ('Italy', 'IT'), ('Spain', 'ES'), ('---', '---'), ('Argentina', 'AR'), ('Australia', 'AU'), ('Austria', 'AT'), ('Belgium', 'BE'), ('Brazil', 'BR'), ('Canada', 'CA'), ('Chile', 'CL'), ('Colombia', 'CO'), ('Czech Republic', 'CZ'), ('Denmark', 'DK'), ('Egypt', 'EG'), ('Finland', 'FI'), ('France', 'FR'), ('Germany', 'DE'), ('Greece', 'GR'), ('Hungary', 'HU'), ('India', 'IN'), ('Indonesia', 'ID'), ('Ireland', 'IE'), ('Israel', 'IL'), ('Italy', 'IT'), ('Japan', 'JP'), ('Malaysia', 'MY'), ('Mexico', 'MX'), ('Netherlands', 'NL'), ('New Zealand', 'NZ'), ('Norway', 'NO'), ('Pakistan', 'PK'), ('Peru', 'PE'), ('Philippines', 'PH'), ('Poland', 'PL'), ('Portugal', 'PT'), ('Romania', 'RO'), ('Russia', 'RU'), ('Saudi Arabia', 'SA'), ('Singapore', 'SG'), ('South Africa', 'ZA'), ('South Korea', 'KR'), ('Spain', 'ES'), ('Sweden', 'SE'), ('Switzerland', 'CH'), ('Thailand', 'TH'), ('Turkey', 'TR'), ('Ukraine', 'UA'), ('United Arab Emirates', 'AE'), ('United Kingdom', 'GB'), ('United States', 'US'), ('Vietnam', 'VN')]
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

# --- Fetch button row (Get + placeholder for Export once ready)
col1, col2 = st.columns([1, 1])
get_trends = col1.button("Get Trends! 🤘")
export_slot_top = col2.empty()  # we will populate after results are ready

combined_results = []  # collect data for export

# --- Action
if get_trends:
    if not keywords_input.strip():
        st.warning("Please input at least 1 keyword.")
    else:
        kw_list = [kw.strip() for kw in keywords_input.strip().split("\n") if kw.strip()]
        if len(kw_list) > 5:
            st.error("🚫 This app is restricted to 5 keywords only. Please reduce your input.")
        else:
            pytrends = TrendReq(hl="en-US", tz=360)
            with st.spinner("Fetching data from Google Trends..."):
                pytrends.build_payload(kw_list, timeframe=timeframe, geo=geo_code)
                related_queries = pytrends.related_queries()

            st.success(f"Showing results for: {', '.join(kw_list)}")

            # show results and collect for export
            for kw in kw_list:
                st.subheader(f"🔍 Keyword: {kw}")
                rq = related_queries.get(kw, {})
                rising = rq.get("rising")
                top = rq.get("top")

                if top is not None and not top.empty:
                    st.markdown("**🏆 Top Queries (up to 25)**")
                    st.dataframe(top)
                    top2 = top.copy()
                    top2["keyword"] = kw
                    top2["type"] = "Top"
                    combined_results.append(top2)
                else:
                    st.info("No top queries found.")

                if rising is not None and not rising.empty:
                    st.markdown("**📈 Rising Queries (up to 25)**")
                    st.dataframe(rising)
                    rising2 = rising.copy()
                    rising2["keyword"] = kw
                    rising2["type"] = "Rising"
                    combined_results.append(rising2)
                else:
                    st.info("No rising queries found.")

            # --- Export buttons (top row and bottom)
            if combined_results:
                all_df = pd.concat(combined_results, ignore_index=True)

                # CSV
                csv_bytes = all_df.to_csv(index=False).encode("utf-8")
                export_slot_top.download_button(
                    "📥 Download Trends (CSV)",
                    data=csv_bytes,
                    file_name="google_trends_export.csv",
                    mime="text/csv",
                    key="export_csv_top",
                )

                # Also show at the end of the results
                st.markdown("---")
                st.download_button(
                    "📥 Download Trends (CSV)",
                    data=csv_bytes,
                    file_name="google_trends_export.csv",
                    mime="text/csv",
                    key="export_csv_bottom",
                )

                # Optional Excel export as well
                with BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        all_df.to_excel(writer, index=False, sheet_name="Trends")
                    xlsx_bytes = buffer.getvalue()

                st.download_button(
                    "📥 Download Trends (Excel)",
                    data=xlsx_bytes,
                    file_name="google_trends_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="export_xlsx_bottom",
                )
