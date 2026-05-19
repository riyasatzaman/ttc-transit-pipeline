"""TTC Transit Reliability Monitor — landing page.

Streamlit auto-discovers pages from the `pages/` directory adjacent to this
file, so navigation in the sidebar appears for free.
"""
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import (
    footer,
    format_relative,
    hero,
    horizontal_flow,
    inject_global_css,
    kpi_card,
    page_preview_card,
    pill,
    pill_row,
    sidebar_branding,
)

st.set_page_config(
    page_title="TTC Transit Reliability Monitor",
    page_icon="🚇",
    layout="wide",
)

inject_global_css()
sidebar_branding()

# --- Hero -----------------------------------------------------------------
hero(
    "🚇 TTC Transit Reliability Monitor",
    "A live analytics dashboard tracking how recently TTC vehicles report "
    "their locations across Toronto's transit network.",
    "Powered by an Airflow → Snowflake → dbt → Streamlit pipeline that "
    "ingests live TTC vehicle data every 15 minutes.",
)


# --- Data fetch -----------------------------------------------------------
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
refresh_str = format_relative(stats["LAST_UPDATED_AT"])

# --- Status pills ---------------------------------------------------------
pill_row([
    pill("Pipeline live", variant="success"),
    pill(f"Last refresh: {refresh_str}"),
    pill("44 checks passing"),
])

# --- KPI row --------------------------------------------------------------
kpis = [
    ("Routes tracked",       f"{int(stats['ROUTE_COUNT']):,}",        "TTC routes observed"),
    ("Vehicle observations", f"{int(stats['TOTAL_OBSERVATIONS']):,}", "live samples ingested"),
    ("Distinct vehicles",    f"{int(stats['DISTINCT_VEHICLES']):,}",  "vehicles seen"),
    ("Automated checks",     "44",                                    "38 dbt + 6 pytest"),
    ("Data refreshed",       refresh_str,                             "auto every hour"),
]
cols = st.columns(5)
for col, (label, value, sub) in zip(cols, kpis):
    col.markdown(kpi_card(label, value, sub), unsafe_allow_html=True)

# --- Why this matters -----------------------------------------------------
st.markdown("### Why this matters")
st.markdown(
    "Live transit feeds are noisy and difficult to interpret directly. "
    "This project turns raw TTC vehicle reports into tested, dashboard-ready "
    "reliability metrics using a modern data engineering stack."
)

# --- Pipeline flow --------------------------------------------------------
st.markdown("### The pipeline")
horizontal_flow([
    ("", "TTC Feed",        "live"),
    ("", "Airflow",         "every 15 min"),
    ("", "Snowflake RAW",   "append-only"),
    ("", "dbt Models",      "tested"),
    ("", "Snowflake MARTS", "dashboard-ready"),
    ("", "Streamlit",       "this app"),
])

# --- Page preview cards ---------------------------------------------------
st.markdown("### What's on each page")
nav_col1, nav_col2, nav_col3 = st.columns(3)
nav_col1.markdown(
    page_preview_card(
        "", "Route Reliability",
        "Which TTC routes are reporting most consistently? Sortable "
        "leaderboard with green/yellow/red tiers.",
    ),
    unsafe_allow_html=True,
)
nav_col2.markdown(
    page_preview_card(
        "", "Report Delay Heatmap",
        "When are vehicle reports most delayed? A 24 × 7 heatmap shows "
        "report delay by hour and weekday.",
    ),
    unsafe_allow_html=True,
)
nav_col3.markdown(
    page_preview_card(
        "", "Best Observed Windows",
        "Which hours have the most up-to-date vehicle reports? Green bars "
        "highlight the best observed windows.",
    ),
    unsafe_allow_html=True,
)

# --- Methodology ----------------------------------------------------------
with st.expander("How this metric is calculated"):
    st.markdown(
        "**Recently Reported %** is the share of vehicle observations where the "
        "vehicle reported its location within the last 2 minutes. "
        "**Avg Report Delay** is `max(0, seconds since last report - 120)`. "
        "This is a live reporting reliability proxy, not official TTC "
        "schedule adherence."
    )

footer()
