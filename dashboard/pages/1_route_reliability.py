"""Page 1: Route Reliability Leaderboard.

Answers: which TTC routes are most and least reliable right now?

Reads from MARTS.mart_route_delay_summary. Colors pct_on_time using the
spec's tiers (>80 green, 60-80 yellow, <60 red). In practice most routes
sit well above 95% because our delay proxy only fires on truly stale
reports — the more discriminating signal is `avg_delay_proxy_seconds`,
which we expose as a secondary column.
"""
import pandas as pd
import streamlit as st

from utils.snowflake_connector import query_df

st.set_page_config(
    page_title="Route Reliability — TTC",
    page_icon="📊",
    layout="wide",
)

st.markdown("<style>h1 { color: #DA291C; }</style>", unsafe_allow_html=True)
st.title("🚌 Route Reliability Leaderboard")
st.markdown(
    "Which TTC routes are most and least reliable right now? "
    "Sorted worst-first so the routes needing attention rise to the top."
)

# Filter: hide routes with tiny samples that aren't meaningful yet.
min_obs = st.slider(
    "Minimum observations (filter out routes with sparse data)",
    min_value=0, max_value=1000, value=100, step=50,
)


@st.cache_data(ttl=300)
def get_leaderboard(min_obs: int) -> pd.DataFrame:
    return query_df(
        f"""
        select
            route_id,
            route_name,
            total_observations,
            distinct_vehicles,
            pct_on_time,
            pct_delayed,
            avg_delay_proxy_seconds,
            avg_speed_kmh,
            last_observed_at
        from mart_route_delay_summary
        where total_observations >= {min_obs}
        order by pct_on_time asc, avg_delay_proxy_seconds desc
        """
    )


df = get_leaderboard(min_obs)

if df.empty:
    st.warning(
        f"No routes have ≥ {min_obs} observations yet. "
        "Wait for more data or lower the threshold."
    )
    st.stop()

# Color tiers per spec. With current data most routes are green; that's
# honest — the TTC's reporting is pretty reliable.
def color_pct_on_time(val: float) -> str:
    if val >= 80:
        return "background-color: #1e7e34; color: white;"
    if val >= 60:
        return "background-color: #d39e00; color: white;"
    return "background-color: #b21f2d; color: white;"


styled = (
    df.rename(
        columns={
            "ROUTE_ID":                "Route",
            "ROUTE_NAME":              "Name",
            "TOTAL_OBSERVATIONS":      "Observations",
            "DISTINCT_VEHICLES":       "Vehicles",
            "PCT_ON_TIME":             "On-time %",
            "PCT_DELAYED":             "Delayed %",
            "AVG_DELAY_PROXY_SECONDS": "Avg delay (s)",
            "AVG_SPEED_KMH":           "Avg speed (km/h)",
            "LAST_OBSERVED_AT":        "Last observed",
        }
    )
    .style
    .map(color_pct_on_time, subset=["On-time %"])
    .format(
        {
            "On-time %":        "{:.2f}",
            "Delayed %":        "{:.2f}",
            "Avg delay (s)":    "{:.1f}",
            "Avg speed (km/h)": "{:.1f}",
            "Observations":     "{:,.0f}",
            "Vehicles":         "{:,.0f}",
            "Last observed":    "{:%Y-%m-%d %H:%M UTC}",
        }
    )
)

st.dataframe(styled, use_container_width=True, height=600)
st.caption(
    f"Showing {len(df)} routes with ≥ {min_obs:,} observations. "
    "Data refreshed by Airflow every hour."
)
