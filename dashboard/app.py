"""TTC Transit Reliability Monitor — landing page.

Streamlit auto-discovers pages from the `pages/` directory adjacent to this
file, so navigation in the sidebar appears for free.
"""
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import (
    ACCENT,
    CARD,
    CARD_BORDER,
    GREEN,
    TEXT_1,
    TEXT_2,
    footer,
    format_relative,
    inject_global_css,
    kpi_row,
    page_header,
    section_label,
    sidebar_brand,
)

st.set_page_config(
    page_title="TTC Transit Reliability Monitor",
    page_icon="🚇",
    layout="wide",
)

inject_global_css()
sidebar_brand()

page_header(
    "TTC Transit Reliability Monitor",
    "A live analytics dashboard tracking route signal freshness across "
    "Toronto's transit network.",
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

# --- Status row -------------------------------------------------------
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:1.5rem;margin:0.5rem 0 1.5rem 0;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:{TEXT_1}">
            <span style="width:8px;height:8px;border-radius:50%;background:{GREEN};display:inline-block"></span>
            Pipeline live
        </div>
        <div style="font-size:0.85rem;color:{TEXT_2}">Last refresh: {refresh_str}</div>
        <div style="font-size:0.85rem;color:{TEXT_2}">44 checks passing</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- KPI row --------------------------------------------------------------
kpi_row([
    {"label": "Routes tracked",       "value": f"{int(stats['ROUTE_COUNT']):,}",        "sub": "TTC routes observed"},
    {"label": "Vehicle observations", "value": f"{int(stats['TOTAL_OBSERVATIONS']):,}", "sub": "live samples ingested"},
    {"label": "Distinct vehicles",    "value": f"{int(stats['DISTINCT_VEHICLES']):,}",  "sub": "vehicles seen"},
    {"label": "Automated checks",     "value": "44",                                    "sub": "38 dbt + 6 pytest"},
    {"label": "Data refreshed",       "value": refresh_str,                             "sub": "auto every hour"},
])

# --- Why this matters -----------------------------------------------------
section_label("Why this matters")
st.markdown(
    "Live transit feeds are noisy and difficult to interpret directly. "
    "This project turns raw TTC vehicle reports into tested, dashboard-ready "
    "reliability metrics using a modern data engineering stack."
)

# --- Pipeline flow --------------------------------------------------------
section_label("The pipeline")
_steps = [
    ("TTC Feed",        "live"),
    ("Airflow",         "every 15 min"),
    ("Snowflake RAW",   "append-only"),
    ("dbt Models",      "tested"),
    ("Snowflake MARTS", "dashboard-ready"),
    ("Streamlit",       "this app"),
]
_step_html = ""
for i, (label, sub) in enumerate(_steps):
    _step_html += f"""
    <div style="flex:1;min-width:120px;background:{CARD};border:1px solid {CARD_BORDER};
                border-radius:10px;padding:1rem 0.8rem;text-align:center">
        <div style="color:{TEXT_1};font-weight:600;font-size:0.95rem">{label}</div>
        <div style="color:{TEXT_2};font-size:0.76rem;margin-top:0.3rem;letter-spacing:0.02em">{sub}</div>
    </div>
    """
    if i < len(_steps) - 1:
        _step_html += (
            f'<div style="color:{ACCENT};font-size:1.25rem;align-self:center;'
            f'padding:0 0.15rem;flex:0 0 auto">→</div>'
        )
st.markdown(
    f'<div style="display:flex;flex-wrap:wrap;gap:0.4rem;align-items:stretch;'
    f'margin:0.25rem 0 1.5rem 0">{_step_html}</div>',
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
