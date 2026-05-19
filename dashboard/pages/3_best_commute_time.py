"""Page 3: Best Time to Ride.

Answers: when should you take a specific route to avoid delays?

Reads from MARTS.mart_hourly_reliability, collapses to per-hour averages
(across all days of the week), and highlights the bottom-25% "delay"
windows in green.

We use `avg_secs_since_report` rather than `avg_delay_proxy_seconds` as
the primary signal. `delay_proxy_seconds` is `max(0, secs_since_report -
120)`, which floors at zero — for busy routes like the 504 King
streetcar it's ~0 for every hour, so the chart would be empty. The raw
`secs_since_report` has organic hourly variation on every route.
"""
import plotly.express as px
import streamlit as st

from utils.snowflake_connector import query_df

st.set_page_config(
    page_title="Best Time to Ride — TTC",
    page_icon="⏰",
    layout="wide",
)

st.markdown("<style>h1 { color: #DA291C; }</style>", unsafe_allow_html=True)
st.title("⏰ Best Time to Ride")
st.markdown(
    "When should you take a route for the smoothest experience? "
    "Green bars mark the 25% of hours with the lowest reporting friction "
    "for the selected route (proxy for less congestion / better service)."
)


@st.cache_data(ttl=300)
def get_route_options():
    return query_df(
        """
        select
            route_id,
            any_value(route_name)   as route_name,
            sum(total_observations) as total_obs
        from mart_hourly_reliability
        group by route_id
        order by total_obs desc
        """
    )


@st.cache_data(ttl=300)
def get_hourly(route_id: str):
    return query_df(
        f"""
        select
            hour_of_day,
            sum(total_observations * avg_secs_since_report)
                / nullif(sum(total_observations), 0) as avg_delay_s,
            sum(total_observations) as total_obs
        from mart_hourly_reliability
        where route_id = '{route_id}'
        group by 1
        order by 1
        """
    )


def _format_hour(h: int) -> str:
    if h == 0:
        return "12am"
    if h < 12:
        return f"{h}am"
    if h == 12:
        return "12pm"
    return f"{h - 12}pm"


def _consecutive_ranges(hours: list[int]) -> list[tuple[int, int]]:
    """Collapse a sorted hour list into [(start, end_inclusive), ...]."""
    if not hours:
        return []
    ranges: list[tuple[int, int]] = []
    start = prev = hours[0]
    for h in hours[1:]:
        if h == prev + 1:
            prev = h
        else:
            ranges.append((start, prev))
            start = prev = h
    ranges.append((start, prev))
    return ranges


routes = get_route_options()
options = {f"{r['ROUTE_ID']} — {r['ROUTE_NAME']}": r["ROUTE_ID"]
           for _, r in routes.iterrows()}
selected = st.selectbox(
    "Route (sorted by observation count, busiest first)",
    list(options.keys()),
)
route_id = options[selected]

df = get_hourly(route_id)

if df.empty:
    st.warning(f"No data for route {route_id} yet.")
    st.stop()

# Mark the best (lowest-delay) hours: bottom 25th percentile.
threshold = df["AVG_DELAY_S"].quantile(0.25)
df["is_best"] = df["AVG_DELAY_S"] <= threshold
df["hour_label"] = df["HOUR_OF_DAY"].apply(_format_hour)

fig = px.bar(
    df,
    x="HOUR_OF_DAY",
    y="AVG_DELAY_S",
    color="is_best",
    color_discrete_map={True: "#1e7e34", False: "#DA291C"},
    labels={
        "HOUR_OF_DAY":  "Hour of day",
        "AVG_DELAY_S":  "Avg seconds since last vehicle report",
        "is_best":      "Best window",
    },
    hover_data={"HOUR_OF_DAY": False, "hour_label": True, "TOTAL_OBS": True},
)
fig.update_xaxes(
    tickmode="array",
    tickvals=list(range(24)),
    ticktext=[_format_hour(h) for h in range(24)],
)
fig.update_layout(showlegend=False, height=420, margin=dict(l=40, r=40, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)

best_hours = sorted(df.loc[df["is_best"], "HOUR_OF_DAY"].astype(int).tolist())
ranges = _consecutive_ranges(best_hours)
if ranges:
    # Wrap the end hour with mod 24 so a range ending at midnight renders
    # as "12am" (next day) instead of falling into the >12 pm branch.
    range_strs = [
        f"{_format_hour(a)}–{_format_hour((b + 1) % 24)}" for a, b in ranges
    ]
    st.success(
        f"**Best windows to ride this route:** {' and '.join(range_strs)}"
    )

st.caption(
    f"Metric: average seconds since each vehicle last pinged the feed "
    f"(threshold ≤ {threshold:.1f}s). Lower values mean more responsive "
    "reporting — usually a sign of denser service and less friction. "
    "Hover any bar for hourly sample size."
)
