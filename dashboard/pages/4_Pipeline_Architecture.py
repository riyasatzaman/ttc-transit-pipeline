"""Page 4: Pipeline Architecture.

Recruiter-facing static page that shows the data flow and tooling.
No Snowflake queries — content is intentionally hardcoded so it loads
instantly and stays in sync with the README.
"""
import streamlit as st

from utils.ui import TTC_RED, footer, page_header

st.set_page_config(
    page_title="Pipeline Architecture — TTC",
    page_icon="⚙️",
    layout="wide",
)

# Metric-tile styling consistent with the other pages.
st.markdown(
    f"<style>div[data-testid='stMetric'] {{"
    f"background-color: rgba(218,41,28,0.06); padding: 0.75rem 1rem; "
    f"border-radius: 8px; border-left: 3px solid {TTC_RED};}}</style>",
    unsafe_allow_html=True,
)

page_header(
    "Pipeline Architecture",
    "⚙️",
    "How live TTC vehicle data flows from the public feed to this dashboard.",
)


# --- 1. Pipeline flow diagram --------------------------------------------------
def _step(emoji: str, label: str, sub: str = "") -> str:
    sub_html = (
        f"<div style='color:#888;font-size:0.85rem;margin-top:0.2rem;'>{sub}</div>"
        if sub else ""
    )
    return (
        f"<div style='background-color:rgba(218,41,28,0.06);"
        f"border-left:3px solid {TTC_RED};border-radius:8px;"
        f"padding:0.75rem 1rem;margin:0.4rem 0;'>"
        f"<div style='color:#fafafa;font-size:1rem;font-weight:500;'>{emoji} {label}</div>"
        f"{sub_html}</div>"
    )


def _arrow(note: str = "") -> str:
    note_html = (
        f"<span style='color:#888;font-size:0.85rem;margin-left:0.5rem;'>{note}</span>"
        if note else ""
    )
    return (
        f"<div style='text-align:center;color:{TTC_RED};font-size:1.5rem;"
        f"line-height:1;margin:0.1rem 0;'>↓{note_html}</div>"
    )


st.markdown(
    _step("🌐", "Live TTC Vehicle Feed", "public UMOIQ API")
    + _arrow("every 15 minutes")
    + _step("🐍", "Python Ingestion Script")
    + _arrow()
    + _step("📁", "Raw JSON files", "data/raw/")
    + _arrow()
    + _step("✈️", "Apache Airflow DAG", "ttc_ingestion_dag")
    + _arrow()
    + _step("❄️", "Snowflake — RAW schema", "vehicle_positions, routes")
    + _arrow()
    + _step("🔧", "dbt — Staging → Intermediate → Marts")
    + _arrow()
    + _step("❄️", "Snowflake — MARTS schema")
    + _arrow()
    + _step("📊", "Streamlit Dashboard", "this app"),
    unsafe_allow_html=True,
)

# --- 2. Stack cards ------------------------------------------------------------
st.markdown("### Stack")
s1, s2, s3, s4 = st.columns(4)
s1.markdown(
    "**✈️ Airflow**  \nOrchestrates ingestion every 15 min and dbt hourly. "
    "Two DAGs: `ttc_ingestion_dag` and `ttc_dbt_dag`."
)
s2.markdown(
    "**❄️ Snowflake**  \nCloud warehouse. Four schemas: RAW · STAGING · "
    "INTERMEDIATE · MARTS. RAW is append-only."
)
s3.markdown(
    "**🔧 dbt**  \nSix SQL models across staging, intermediate, and mart "
    "layers. Schema tested with 44 automated checks."
)
s4.markdown(
    "**📊 Streamlit**  \nThree analytics pages reading from Snowflake "
    "MARTS. Deployed on Streamlit Community Cloud."
)

# --- 3. Data quality summary ---------------------------------------------------
st.markdown("### By the numbers")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Automated checks passing", "44")
m2.metric("Airflow DAGs",             "2")
m3.metric("Snowflake schemas",        "4")
m4.metric("dbt models",               "6")

# --- 4. Schema design ----------------------------------------------------------
with st.expander("Snowflake schema design"):
    st.markdown(
        """
| Schema | Type | Key tables |
|---|---|---|
| `RAW` | Source | `vehicle_positions`, `routes` |
| `STAGING` | dbt views | `stg_vehicle_positions`, `stg_routes` |
| `INTERMEDIATE` | dbt views | `int_vehicle_delays`, `int_route_performance` |
| `MARTS` | dbt tables | `mart_route_delay_summary`, `mart_hourly_reliability` |
"""
    )

# --- 5. Known limitations ------------------------------------------------------
with st.expander("Known limitations & planned improvements"):
    st.markdown(
        """
**Current MVP uses live vehicle report delay as a reliability proxy.**
True schedule-adherence delay requires GTFS `stop_times` and spatial
matching — listed as a planned improvement.

**Planned:**
- GTFS schedule adherence (unlocks `mart_worst_stops`)
- Incremental dbt models
- Managed Airflow deployment (Astronomer or MWAA)
- GitHub Actions CI on dbt tests
- Observability alerts on DAG failures
"""
    )

footer()
