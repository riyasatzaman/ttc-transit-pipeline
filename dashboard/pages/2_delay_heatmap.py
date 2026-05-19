"""Page 2: Delay Heatmap.

Answers: when during the week are delays worst for a given route?

Reads from MARTS.mart_hourly_reliability. Rows are aggregated to the
route × hour × day-of-week grain; we use Plotly's imshow to render a
24-column × 7-row heatmap with red = worse "delay".

We use `avg_secs_since_report` rather than `avg_delay_proxy_seconds` as
the cell value for the same reason page 3 does: the delay proxy is
floored at zero (it's `max(0, secs_since_report - 120)`) and stays ~0
on busy routes, which renders the heatmap as a uniform color wash.
"""
import plotly.express as px
import streamlit as st

from utils.snowflake_connector import query_df

st.set_page_config(
    page_title="Delay Heatmap — TTC",
    page_icon="🔥",
    layout="wide",
)

st.markdown("<style>h1 { color: #DA291C; }</style>", unsafe_allow_html=True)
st.title("🔥 Delay Heatmap")
st.markdown(
    "When during the week is a given route most stressed? "
    "Each cell is the average seconds since the vehicle last pinged the feed "
    "for that hour × day-of-week. Redder = less responsive reporting "
    "(proxy for congestion / sparser service)."
)


@st.cache_data(ttl=300)
def get_route_options():
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
def get_heatmap_data(route_id: str):
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
    st.stop()

# Pivot for the heatmap: rows = day, cols = hour, values = avg_delay_s.
pivot = df.pivot(index="DAY_OF_WEEK", columns="HOUR_OF_DAY", values="AVG_DELAY_S")

# Snowflake DAYOFWEEK: 0=Sunday, ..., 6=Saturday.
day_labels = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
pivot.index = pivot.index.map(day_labels)

fig = px.imshow(
    pivot,
    labels=dict(x="Hour of day", y="Day of week", color="Avg secs since report"),
    aspect="auto",
    color_continuous_scale="Reds",
)
fig.update_layout(height=400, margin=dict(l=40, r=40, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)

total = int(df["TOTAL_OBS"].sum())
st.caption(
    f"Showing {total:,} observations for route {selected}. "
    "Empty rows are days we haven't observed yet — fills in as the "
    "ingestion DAG keeps running."
)
