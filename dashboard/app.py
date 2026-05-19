"""TTC Transit Analytics — landing page.

Streamlit auto-discovers pages from the `pages/` directory adjacent to this
file, so navigation in the sidebar appears for free.
"""
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import TTC_RED, footer, format_relative

st.set_page_config(
    page_title="TTC Transit Reliability Monitor",
    page_icon="🚇",
    layout="wide",
)

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
    "A live analytics dashboard tracking route signal freshness and reliability "
    "patterns across Toronto's transit network."
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
    "**🚌 Route Reliability**  \nWhich TTC routes have the most consistent live "
    "reporting? Sortable leaderboard with green/yellow/red tiers."
)
nav_col2.markdown(
    "**🔥 Reliability Heatmap**  \nWhen during the week is a given route's "
    "signal lag highest? 24 × 7 grid with redder = higher signal lag."
)
nav_col3.markdown(
    "**⏰ Best Observed Windows**  \nWhich hours have the lowest signal lag "
    "for a given route? Hourly bar chart with the lowest-lag windows highlighted."
)

with st.expander("How this metric is calculated"):
    st.markdown(
        "This dashboard uses live vehicle reporting lag (seconds since last "
        "position ping) as a route reliability proxy. Lower values indicate "
        "fresher live vehicle reporting and more consistent service presence. "
        "True schedule-adherence delay requires GTFS `stop_times` and spatial "
        "matching, which is listed as a planned improvement."
    )

footer()
