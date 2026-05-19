"""Page 2: Delay Heatmap.

Answers: when during the week is a given route most stressed?

Reads from MARTS.mart_hourly_reliability. We use `avg_secs_since_report`
rather than `avg_delay_proxy_seconds` as the cell value — the delay
proxy is floored at zero for busy routes and would render as a uniform
color wash.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.snowflake_connector import query_df
from utils.ui import TTC_RED, PLOTLY_TEMPLATE, footer, page_header

st.set_page_config(
    page_title="Reliability Heatmap — TTC",
    page_icon="🔥",
    layout="wide",
)

st.markdown(
    f"<style>div[data-testid='stMetric'] {{"
    f"background-color: rgba(218,41,28,0.06); padding: 0.75rem 1rem; "
    f"border-radius: 8px; border-left: 3px solid {TTC_RED};}}</style>",
    unsafe_allow_html=True,
)

page_header(
    "Reliability Heatmap",
    "🔥",
    "Each cell is the average signal lag (seconds). "
    "Redder = higher signal lag (indicator of service irregularity or sparser service).",
)


@st.cache_data(ttl=300)
def get_route_options() -> pd.DataFrame:
    return query_df(
        """
        select
            route_id,
            any_value(route_name)         as route_name,
            sum(total_observations)       as total_obs
        from mart_hourly_reliability
        group by route_id
        order by total_obs desc
        """
    )


@st.cache_data(ttl=300)
def get_heatmap_data(route_id: str) -> pd.DataFrame:
    return query_df(
        f"""
        select
            day_of_week,
            hour_of_day,
            sum(total_observations * avg_secs_since_report)
                / nullif(sum(total_observations), 0) as avg_delay_s,
            sum(total_observations) as total_obs
        from mart_hourly_reliability
        where route_id = '{route_id}'
        group by 1, 2
        order by 1, 2
        """
    )


routes = get_route_options()
options = {f"{r['ROUTE_ID']} — {r['ROUTE_NAME']}": r["ROUTE_ID"]
           for _, r in routes.iterrows()}
selected = st.selectbox(
    "Route (sorted by observation count, busiest first)",
    list(options.keys()),
)
route_id = options[selected]

df = get_heatmap_data(route_id)

if df.empty:
    st.warning(f"No data for route {route_id} yet.")
    footer()
    st.stop()

# Pivot, then re-index to a fixed 7-day × 24-hour grid so the heatmap
# always shows the full week (cells we haven't observed yet render as NaN
# = transparent rather than disappearing).
pivot = df.pivot(index="DAY_OF_WEEK", columns="HOUR_OF_DAY", values="AVG_DELAY_S")
pivot = pivot.reindex(index=range(7), columns=range(24))

# Snowflake DAYOFWEEK: 0=Sunday, ..., 6=Saturday.
day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
pivot.index = day_labels
pivot.columns = [
    "12am", "1am", "2am", "3am", "4am", "5am", "6am", "7am",
    "8am", "9am", "10am", "11am",
    "12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm",
    "8pm", "9pm", "10pm", "11pm",
]

# KPI tiles: where's the friction concentrated?
worst_cell = df.loc[df["AVG_DELAY_S"].idxmax()]
best_cell  = df.loc[df["AVG_DELAY_S"].idxmin()]
total = int(df["TOTAL_OBS"].sum())
hours_observed = int(df.shape[0])

c1, c2, c3 = st.columns(3)
c1.metric("Observations", f"{total:,}")
c2.metric(
    "Worst hour observed",
    f"{day_labels[int(worst_cell['DAY_OF_WEEK'])]} "
    f"{pivot.columns[int(worst_cell['HOUR_OF_DAY'])]}",
    f"{float(worst_cell['AVG_DELAY_S']):.1f}s",
    delta_color="inverse",
)
c3.metric(
    "Smoothest hour observed",
    f"{day_labels[int(best_cell['DAY_OF_WEEK'])]} "
    f"{pivot.columns[int(best_cell['HOUR_OF_DAY'])]}",
    f"{float(best_cell['AVG_DELAY_S']):.1f}s",
)

fig = px.imshow(
    pivot,
    labels=dict(x="Hour of day", y="Day of week", color="Avg signal lag (s)"),
    aspect="auto",
    color_continuous_scale="Reds",
    template=PLOTLY_TEMPLATE,
)
fig.update_layout(
    height=380,
    margin=dict(l=40, r=40, t=10, b=40),
    xaxis=dict(tickfont=dict(size=11)),
    yaxis=dict(tickfont=dict(size=12)),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Each cell shows average live signal lag. Higher values suggest less "
    "consistent vehicle reporting and potential service irregularity. "
    "Empty cells are hours not yet observed — coverage improves as the "
    "pipeline runs."
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
