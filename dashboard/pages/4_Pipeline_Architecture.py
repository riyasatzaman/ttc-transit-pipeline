"""Page 4: Pipeline Architecture.

Recruiter-facing static page that shows the data flow and tooling.
No Snowflake queries — content is intentionally hardcoded so it loads
instantly and stays in sync with the README.
"""
import streamlit as st

from utils.ui import (
    ACCENT,
    CARD,
    CARD_BORDER,
    TEXT_1,
    TEXT_2,
    footer,
    inject_global_css,
    kpi_row,
    page_header,
    sidebar_brand,
)

st.set_page_config(
    page_title="Pipeline Architecture — TTC",
    page_icon="⚙️",
    layout="wide",
)

inject_global_css()
sidebar_brand()

page_header(
    "Pipeline Architecture",
    "How live TTC vehicle data flows from the public feed to this dashboard.",
)

# --- By the numbers ---------------------------------------------------
kpi_row([
    {"label": "Automated checks",  "value": "44", "sub": "38 dbt tests + 6 pytest"},
    {"label": "Airflow DAGs",      "value": "2",  "sub": "ingestion + dbt build"},
    {"label": "Snowflake schemas", "value": "4",  "sub": "RAW → STAGING → INT → MARTS"},
    {"label": "dbt models",        "value": "6",  "sub": "2 staging + 2 int + 2 marts"},
])


# --- Numbered pipeline steps, as a 2-column grid --------------------------
def _step_card(num: str, label: str, sub: str = "") -> str:
    # Built as single-line HTML — a blank line inside a block passed to
    # st.markdown(unsafe_allow_html=True) ends the raw-HTML block early and
    # dumps everything after it onto the page as literal text.
    sub_html = (
        f'<div style="color:{TEXT_2};font-size:0.8rem;margin-top:0.3rem">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{CARD};border:1px solid {CARD_BORDER};border-left:3px solid {ACCENT};'
        f'border-radius:10px;padding:0.95rem 1.15rem;">'
        f'<div style="color:{TEXT_1};font-size:1rem;font-weight:600">'
        f'<span style="color:{ACCENT};font-weight:700;font-size:0.78rem;'
        f'letter-spacing:0.12em;margin-right:0.6rem">{num}</span>{label}</div>'
        f'{sub_html}</div>'
    )


_steps = [
    ("01", "Live TTC Vehicle Feed", "public UMOIQ API"),
    ("02", "Python Ingestion Script", ""),
    ("03", "Raw JSON Files", "data/raw/"),
    ("04", "Apache Airflow DAG", "ttc_ingestion_dag"),
    ("05", "Snowflake RAW Schema", "vehicle_positions, routes"),
    ("06", "dbt Models", "staging → intermediate → marts"),
    ("07", "Snowflake MARTS Schema", ""),
    ("08", "Streamlit Dashboard", "this app"),
]
st.markdown(
    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0 1.5rem 0">'
    + "".join(_step_card(n, l, s) for n, l, s in _steps)
    + "</div>",
    unsafe_allow_html=True,
)

# --- Known limitations -------------------------------------------------
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
