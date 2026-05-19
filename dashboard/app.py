"""TTC Transit Analytics — landing page.

Streamlit auto-discovers pages from the `pages/` directory adjacent to this
file, so navigation in the sidebar appears for free.
"""
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import TTC_RED, footer, format_relative, sidebar_branding

st.set_page_config(
    page_title="TTC Transit Reliability Monitor",
    page_icon="🚇",
    layout="wide",
)

sidebar_branding()

# TTC red accent on headings; subtle red glow on metric tiles.
st.markdown(
    f"""
    <style>
        h1 {{ color: {TTC_RED}; }}
        div[data-testid="stMetric"] {{
            background-color: rgba(218, 41, 28, 0.06);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border-left: 3px solid {TTC_RED};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"<h1>🚇 TTC Transit Reliability Monitor</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color: #bbb; font-size: 1.1rem;'>"
    "A live analytics dashboard tracking how recently TTC vehicles report "
    "their locations across Toronto's transit network."
    "</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color: #888; font-size: 0.95rem;'>"
    "Powered by an Airflow → Snowflake → dbt → Streamlit pipeline ingesting "
    "live TTC vehicle data every 15 minutes."
    "</p>",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def get_summary():
    return query_df(
        """
        select
            count(*)                     as route_count,
            sum(total_observations)      as total_observations,
            sum(distinct_vehicles)       as distinct_vehicles,
            max(last_updated_at)         as last_updated_at
        from mart_route_delay_summary
        """
    )


stats = get_summary().iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Routes tracked",       f"{int(stats['ROUTE_COUNT']):,}")
col2.metric("Vehicle observations", f"{int(stats['TOTAL_OBSERVATIONS']):,}")
col3.metric("Distinct vehicles",    f"{int(stats['DISTINCT_VEHICLES']):,}")
col4.metric("Data refreshed",       format_relative(stats["LAST_UPDATED_AT"]))

st.markdown("### The pipeline")
st.markdown(
    """
| Layer | Tooling |
|---|---|
| **Ingestion** | Python + Apache Airflow — pulls live vehicle positions every 15 min |
| **Warehouse** | Snowflake — raw / staging / intermediate / marts schemas |
| **Transformation** | dbt — typed, tested SQL with lineage and CI-ready tests |
| **Dashboard** | Streamlit — three pages reading from the mart tables |
"""
)

st.markdown("### What's on each page")
nav_col1, nav_col2, nav_col3 = st.columns(3)
nav_col1.markdown(
    "**🚌 Route Reliability**  \nWhich TTC routes are reporting most consistently? "
    "Sortable leaderboard with green/yellow/red tiers."
)
nav_col2.markdown(
    "**🔥 Report Delay Heatmap**  \nWhen are vehicle reports most delayed? "
    "A 24 × 7 heatmap shows report delay by hour and weekday."
)
nav_col3.markdown(
    "**⏰ Best Observed Windows**  \nWhich hours have the most up-to-date vehicle "
    "reports? Green bars highlight the best observed windows."
)

with st.expander("How this metric is calculated"):
    st.markdown(
        "**Recently Reported %** is the share of vehicle observations where the "
        "vehicle reported its location within the last 2 minutes. "
        "**Avg Report Delay** is `max(0, seconds since last report - 120)`. "
        "This is a live reporting reliability proxy, not official TTC "
        "schedule adherence."
    )

footer()
