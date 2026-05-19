"""Page 4: Pipeline Architecture.

Recruiter-facing static page that shows the data flow and tooling.
No Snowflake queries — content is intentionally hardcoded so it loads
instantly and stays in sync with the README.
"""
import streamlit as st

from utils.ui import (
    BORDER,
    CARD_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TTC_RED,
    arch_arrow,
    arch_step,
    footer,
    inject_global_css,
    kpi_card,
    page_header,
    page_preview_card,
    sidebar_branding,
)

st.set_page_config(
    page_title="Pipeline Architecture — TTC",
    page_icon="⚙️",
    layout="wide",
)

inject_global_css()
sidebar_branding()

page_header(
    "Pipeline Architecture",
    "⚙️",
    "How live TTC vehicle data flows from the public feed to this dashboard.",
)

# --- 1. Vertical pipeline flow --------------------------------------------
st.markdown(
    arch_step("🌐", "Live TTC Vehicle Feed", "public UMOIQ API")
    + arch_arrow("every 15 minutes")
    + arch_step("🐍", "Python Ingestion Script")
    + arch_arrow()
    + arch_step("📁", "Raw JSON files", "data/raw/")
    + arch_arrow()
    + arch_step("✈️", "Apache Airflow DAG", "ttc_ingestion_dag")
    + arch_arrow()
    + arch_step("❄️", "Snowflake — RAW schema", "vehicle_positions, routes")
    + arch_arrow()
    + arch_step("🔧", "dbt — Staging → Intermediate → Marts")
    + arch_arrow()
    + arch_step("❄️", "Snowflake — MARTS schema")
    + arch_arrow()
    + arch_step("📊", "Streamlit Dashboard", "this app"),
    unsafe_allow_html=True,
)

# --- 2. Stack cards -------------------------------------------------------
st.markdown("### Stack")
s1, s2, s3, s4 = st.columns(4)
s1.markdown(
    page_preview_card(
        "✈️", "Airflow",
        "Orchestrates ingestion every 15 min and dbt hourly. Two DAGs: "
        "<code>ttc_ingestion_dag</code> and <code>ttc_dbt_dag</code>.",
    ),
    unsafe_allow_html=True,
)
s2.markdown(
    page_preview_card(
        "❄️", "Snowflake",
        "Cloud warehouse. Four schemas: RAW · STAGING · INTERMEDIATE · MARTS. "
        "RAW is append-only.",
    ),
    unsafe_allow_html=True,
)
s3.markdown(
    page_preview_card(
        "🔧", "dbt",
        "Six SQL models across staging, intermediate, and mart layers. "
        "Schema tested with 44 automated checks.",
    ),
    unsafe_allow_html=True,
)
s4.markdown(
    page_preview_card(
        "📊", "Streamlit",
        "Three analytics pages reading from Snowflake MARTS. Deployed on "
        "Streamlit Community Cloud.",
    ),
    unsafe_allow_html=True,
)

# --- 3. By the numbers ----------------------------------------------------
st.markdown("### By the numbers")
m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    kpi_card("Automated checks passing", "44", "38 dbt tests + 6 pytest"),
    unsafe_allow_html=True,
)
m2.markdown(kpi_card("Airflow DAGs",      "2", "ingestion + dbt build"),  unsafe_allow_html=True)
m3.markdown(kpi_card("Snowflake schemas", "4", "RAW → STAGING → INT → MARTS"), unsafe_allow_html=True)
m4.markdown(kpi_card("dbt models",        "6", "2 staging + 2 int + 2 marts"), unsafe_allow_html=True)


# --- 4. Snowflake schema layer cards --------------------------------------
def _schema_card(name: str, kind: str, tables: list[str]) -> str:
    rows = "".join(
        f"<div style='color:{TEXT_PRIMARY};font-size:0.86rem;font-family:"
        f"\"SF Mono\",Menlo,monospace;margin-top:0.25rem;letter-spacing:-0.01em;'>"
        f"{t}</div>"
        for t in tables
    )
    return (
        f"<div style='background-color:{CARD_BG};border:1px solid {BORDER};"
        f"border-radius:14px;padding:1rem 1.15rem;height:100%;min-height:130px;'>"
        f"<div style='color:{TTC_RED};font-weight:700;font-size:0.95rem;"
        f"letter-spacing:0.04em;'>{name}</div>"
        f"<div style='color:{TEXT_MUTED};font-size:0.78rem;margin-top:0.15rem;"
        f"text-transform:uppercase;letter-spacing:0.05em;'>{kind}</div>"
        f"<div style='margin-top:0.6rem;'>{rows}</div></div>"
    )


st.markdown("### Snowflake schema layers")
sl1, sl2, sl3, sl4 = st.columns(4)
sl1.markdown(
    _schema_card("RAW", "Source", ["vehicle_positions", "routes"]),
    unsafe_allow_html=True,
)
sl2.markdown(
    _schema_card("STAGING", "dbt views", ["stg_vehicle_positions", "stg_routes"]),
    unsafe_allow_html=True,
)
sl3.markdown(
    _schema_card("INTERMEDIATE", "dbt views",
                 ["int_vehicle_delays", "int_route_performance"]),
    unsafe_allow_html=True,
)
sl4.markdown(
    _schema_card("MARTS", "dbt tables",
                 ["mart_route_delay_summary", "mart_hourly_reliability"]),
    unsafe_allow_html=True,
)

# --- 5. Known limitations -------------------------------------------------
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
