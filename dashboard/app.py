"""TTC Transit Analytics — landing page.

Streamlit auto-discovers pages from the `pages/` directory adjacent to this
file, so navigation in the sidebar appears for free.
"""
import streamlit as st

from utils.snowflake_connector import query_df

st.set_page_config(
    page_title="TTC Transit Analytics",
    page_icon="🚇",
    layout="wide",
)

# TTC red accent on headings only — keep the rest of the theme default.
st.markdown(
    """
    <style>
        h1 { color: #DA291C; }
        .stMetric { background-color: rgba(218, 41, 28, 0.04); padding: 0.5rem 1rem; border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("TTC Transit Analytics Pipeline")

st.markdown(
    """
    Live route reliability and delay analytics for the Toronto Transit Commission.

    This dashboard is powered by a production-style data pipeline:
    - **Ingestion**: Python + Apache Airflow pulls live vehicle positions from
      the TTC every 15 minutes
    - **Warehouse**: Snowflake holds raw and modeled data
    - **Transformation**: dbt builds staging, intermediate, and mart layers
    - **Dashboard**: Streamlit reads the mart tables

    Use the sidebar to navigate:
    - **Route Reliability** — which TTC routes are most/least on time?
    - **Delay Heatmap** — when during the week are delays worst?
    - **Best Time to Ride** — when should you take a specific route?
    """
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


stats = get_summary()
row = stats.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Routes tracked",       f"{int(row['ROUTE_COUNT']):,}")
col2.metric("Vehicle observations", f"{int(row['TOTAL_OBSERVATIONS']):,}")
col3.metric("Distinct vehicles",    f"{int(row['DISTINCT_VEHICLES']):,}")
col4.metric(
    "Data last refreshed",
    row["LAST_UPDATED_AT"].strftime("%Y-%m-%d %H:%M"),
)

st.markdown("---")
st.caption(
    "Built by Riyasat Zaman. "
    "[Source on GitHub](https://github.com/riyasatzaman/ttc-transit-pipeline)"
)
