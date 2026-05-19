"""Page 3: Best Time to Ride.

Answers: when should you take a specific route to avoid delays?

Reads from MARTS.mart_hourly_reliability, collapses to per-hour averages
(across all days of the week), and highlights the bottom-25% "delay"
windows in green.

Uses `avg_secs_since_report` rather than `avg_delay_proxy_seconds` —
the delay proxy is floored at zero for busy routes, while the raw
secs_since_report has organic hourly variation everywhere.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import TTC_RED, PLOTLY_TEMPLATE, footer, page_header

st.set_page_config(
    page_title="Best Observed Windows — TTC",
    page_icon="⏰",
    layout="wide",
)

st.markdown(
    f"<style>div[data-testid='stMetric'] {{"
    f"background-color: rgba(218,41,28,0.06); padding: 0.75rem 1rem; "
    f"border-radius: 8px; border-left: 3px solid {TTC_RED};}}</style>",
    unsafe_allow_html=True,
)

page_header(
    "Best Observed Windows",
    "⏰",
    "Green bars mark the 25% of hours with the lowest signal lag "
    "for the selected route (indicator of more consistent service).",
)


@st.cache_data(ttl=300)
def get_route_options() -> pd.DataFrame:
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
def get_hourly(route_id: str) -> pd.DataFrame:
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

df_raw = get_hourly(route_id)

if df_raw.empty:
    st.warning(f"No data for route {route_id} yet.")
    footer()
    st.stop()

# Pad to all 24 hours so the chart always shows a full day. Hours we
# haven't observed get NaN (= no bar) instead of disappearing.
all_hours = pd.DataFrame({"HOUR_OF_DAY": range(24)})
df = all_hours.merge(df_raw, on="HOUR_OF_DAY", how="left")
df["hour_label"] = df["HOUR_OF_DAY"].apply(_format_hour)

observed = df.dropna(subset=["AVG_DELAY_S"]).copy()
threshold = float(observed["AVG_DELAY_S"].quantile(0.25))
df["is_best"] = (df["AVG_DELAY_S"].notna()) & (df["AVG_DELAY_S"] <= threshold)

# KPI tiles.
total_obs = int(observed["TOTAL_OBS"].sum())
hours_observed = int(observed.shape[0])
best_hours = sorted(df.loc[df["is_best"], "HOUR_OF_DAY"].astype(int).tolist())
ranges = _consecutive_ranges(best_hours)
best_label = (
    " · ".join(
        f"{_format_hour(a)}–{_format_hour((b + 1) % 24)}" for a, b in ranges
    )
    if ranges
    else "—"
)

c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("Observations",   f"{total_obs:,}")
c2.metric("Hours observed", f"{hours_observed} / 24")
# c3 uses a custom HTML block instead of st.metric so the time-range list
# can wrap. st.metric forces white-space:nowrap on the value, which
# truncates "12am-1am · 2am-3am · 5pm-6pm · ..." with an ellipsis.
c3.markdown(
    f"""
    <div style="
        background-color: rgba(218,41,28,0.06);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border-left: 3px solid {TTC_RED};
        min-height: 6.5rem;
    ">
        <div style="color: rgba(250,250,250,0.6); font-size: 0.875rem;">
            Best windows
        </div>
        <div style="
            color: #fafafa;
            font-size: 1.25rem;
            font-weight: 400;
            line-height: 1.4;
            margin-top: 0.25rem;
            white-space: normal;
            word-break: break-word;
        ">
            {best_label}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

fig = px.bar(
    df,
    x="HOUR_OF_DAY",
    y="AVG_DELAY_S",
    color="is_best",
    color_discrete_map={True: "#1e7e34", False: TTC_RED},
    labels={
        "HOUR_OF_DAY":  "Hour of day",
        "AVG_DELAY_S":  "Avg signal lag (s)",
        "is_best":      "Best window",
    },
    hover_data={"HOUR_OF_DAY": False, "hour_label": True, "TOTAL_OBS": True},
    template=PLOTLY_TEMPLATE,
)
fig.update_xaxes(
    tickmode="array",
    tickvals=list(range(24)),
    ticktext=[_format_hour(h) for h in range(24)],
)
fig.update_layout(
    showlegend=False,
    height=420,
    margin=dict(l=40, r=40, t=10, b=40),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Green bars highlight the lowest-lag observed hours for this route. "
    "Lower signal lag generally means more consistent live reporting and "
    "denser observed service."
)

with st.expander("How this metric is calculated"):
    st.markdown(
        "This dashboard uses live vehicle reporting lag (seconds since last "
        "position ping) as a route reliability proxy. Lower values indicate "
        "fresher live vehicle reporting and more consistent service presence. "
        "True schedule-adherence delay requires GTFS `stop_times` and spatial "
        "matching, which is listed as a planned improvement."
    )

footer()
