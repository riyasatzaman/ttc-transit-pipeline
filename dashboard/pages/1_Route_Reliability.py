"""Page 1: Route Reliability Leaderboard.

Answers: which TTC routes are most and least reliable right now?

Reads from MARTS.mart_route_delay_summary. Colors pct_on_time using the
spec's tiers (>80 green, 60-80 yellow, <60 red). In practice most routes
sit above 95% because our delay proxy only fires on truly stale reports —
the more discriminating signal is `avg_delay_proxy_seconds`, which we
surface as a column.
"""
import pandas as pd
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import (
    ACCENT,
    GREEN,
    footer,
    html_table,
    inject_global_css,
    insight_box,
    kpi_row,
    page_header,
    sidebar_brand,
)

st.set_page_config(
    page_title="Route Reliability — TTC",
    page_icon="📊",
    layout="wide",
)

inject_global_css()
sidebar_brand()

page_header(
    "Route Reliability Leaderboard",
    "Routes sorted by highest report delay — inconsistent live reporting "
    "rises to the top.",
)

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
    footer()
    st.stop()

# KPI tiles up top.
best_row = df.iloc[-1]      # df is sorted ascending by pct_on_time
worst_row = df.iloc[0]
avg_on_time = float(df["PCT_ON_TIME"].mean())

kpi_row([
    {"label": "Routes shown",          "value": f"{len(df):,}"},
    {"label": "Avg recently reported", "value": f"{avg_on_time:.2f}%"},
    {
        "label": "Most Recently Reported",
        "value": f"{best_row['ROUTE_ID']} · {best_row['ROUTE_NAME']}",
        "sub": f'<span style="color:{GREEN}">↑ {best_row["PCT_ON_TIME"]:.2f}% recent</span>',
    },
    {
        "label": "Highest Report Delay",
        "value": f"{worst_row['ROUTE_ID']} · {worst_row['ROUTE_NAME']}",
        "sub": f'<span style="color:{ACCENT}">avg {float(worst_row["AVG_DELAY_PROXY_SECONDS"]):.1f}s</span>',
        "accent": True,
    },
])

insight_box(
    f"<strong>{best_row['ROUTE_ID']} · {best_row['ROUTE_NAME']}</strong> "
    f"has the most consistent recent reporting at "
    f"<strong>{best_row['PCT_ON_TIME']:.2f}%</strong>. "
    f"<strong>{worst_row['ROUTE_ID']} · {worst_row['ROUTE_NAME']}</strong> "
    f"has the highest average report delay at "
    f"<strong>{float(worst_row['AVG_DELAY_PROXY_SECONDS']):.1f}s</strong>."
)

display_df = pd.DataFrame({
    "Route":                  df["ROUTE_ID"],
    "Name":                   df["ROUTE_NAME"],
    "Observations":           df["TOTAL_OBSERVATIONS"].map("{:,.0f}".format),
    "Vehicles":               df["DISTINCT_VEHICLES"].map("{:,.0f}".format),
    "Recently Reported %":    df["PCT_ON_TIME"],
    "Stale Reports %":        df["PCT_DELAYED"].map("{:.2f}%".format),
    "Avg Report Delay (s)":   df["AVG_DELAY_PROXY_SECONDS"].map("{:.1f}".format),
    "Avg speed (km/h)":       df["AVG_SPEED_KMH"].map("{:.1f}".format),
    "Last Seen":              df["LAST_OBSERVED_AT"].dt.strftime("%Y-%m-%d %H:%M UTC"),
})
html_table(display_df, progress_col="Recently Reported %")

st.caption(
    f"Showing {len(df):,} routes with ≥ {min_obs:,} observations. "
    "**Recently Reported %** is the share of observations where a vehicle "
    "reported its location within the last 2 minutes. **Avg Report Delay** "
    "is the extra time beyond that 2-minute window."
)

with st.expander("How this metric is calculated"):
    st.markdown(
        "**Recently Reported %** is the share of vehicle observations where the "
        "vehicle reported its location within the last 2 minutes. "
        "**Avg Report Delay** is `max(0, seconds_since_last_report - 120)` — "
        "the extra time beyond the 2-minute window, in seconds. "
        "This is a live reporting reliability proxy, not official TTC "
        "schedule adherence."
    )

footer()
