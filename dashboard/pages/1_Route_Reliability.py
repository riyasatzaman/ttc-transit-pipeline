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
    footer,
    inject_global_css,
    insight_box,
    kpi_card,
    page_header,
    sidebar_branding,
)

st.set_page_config(
    page_title="Route Reliability — TTC",
    page_icon="📊",
    layout="wide",
)

inject_global_css()
sidebar_branding()

page_header(
    "Route Reliability Leaderboard",
    "",
    "Routes are sorted by highest report delay so inconsistent live "
    "reporting rises to the top.",
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

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Routes shown",          f"{len(df):,}"),                unsafe_allow_html=True)
c2.markdown(kpi_card("Avg recently reported", f"{avg_on_time:.2f}%"),         unsafe_allow_html=True)
c3.markdown(
    kpi_card(
        "Most Recently Reported",
        f"{best_row['ROUTE_ID']} · {best_row['ROUTE_NAME']}",
        f"↑ {best_row['PCT_ON_TIME']:.2f}% recent",
        sub_color="success",
    ),
    unsafe_allow_html=True,
)
c4.markdown(
    kpi_card(
        "Highest Report Delay",
        f"{worst_row['ROUTE_ID']} · {worst_row['ROUTE_NAME']}",
        f"avg {float(worst_row['AVG_DELAY_PROXY_SECONDS']):.1f}s",
        sub_color="danger",
    ),
    unsafe_allow_html=True,
)

insight_box(
    f"<strong>{best_row['ROUTE_ID']} · {best_row['ROUTE_NAME']}</strong> "
    f"has the most consistent recent reporting at "
    f"<strong>{best_row['PCT_ON_TIME']:.2f}%</strong>. "
    f"<strong>{worst_row['ROUTE_ID']} · {worst_row['ROUTE_NAME']}</strong> "
    f"has the highest average report delay at "
    f"<strong>{float(worst_row['AVG_DELAY_PROXY_SECONDS']):.1f}s</strong>."
)


display_df = df.rename(
    columns={
        "ROUTE_ID":                "Route",
        "ROUTE_NAME":              "Name",
        "TOTAL_OBSERVATIONS":      "Observations",
        "DISTINCT_VEHICLES":       "Vehicles",
        "PCT_ON_TIME":             "Recently Reported %",
        "PCT_DELAYED":             "Stale Reports %",
        "AVG_DELAY_PROXY_SECONDS": "Avg Report Delay (s)",
        "AVG_SPEED_KMH":           "Avg speed (km/h)",
        "LAST_OBSERVED_AT":        "Last Seen",
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    height=520,
    hide_index=True,
    column_config={
        "Recently Reported %": st.column_config.ProgressColumn(
            "Recently Reported %", format="%.1f%%", min_value=0, max_value=100,
        ),
        "Stale Reports %":      st.column_config.NumberColumn("Stale Reports %", format="%.2f%%"),
        "Avg Report Delay (s)": st.column_config.NumberColumn("Avg Report Delay (s)", format="%.1f"),
        "Avg speed (km/h)":     st.column_config.NumberColumn("Avg speed (km/h)", format="%.1f"),
        "Observations":         st.column_config.NumberColumn("Observations", format="%d"),
        "Vehicles":             st.column_config.NumberColumn("Vehicles", format="%d"),
        "Last Seen":            st.column_config.DatetimeColumn("Last Seen", format="YYYY-MM-DD HH:mm [UTC]"),
    },
)
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
