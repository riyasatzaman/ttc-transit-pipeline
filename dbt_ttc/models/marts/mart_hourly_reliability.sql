-- Mart: route × hour × day-of-week reliability.
--
-- Powers the dashboard's "Delay Heatmap" (x=hour, y=day, color=delay) and
-- "Best Time to Ride" (per-route bar chart by hour).
--
-- Effectively a passthrough of int_route_performance materialized as a
-- table so the dashboard's queries are fast and stable.

{{ config(materialized='table') }}

select
    route_id,
    route_name,
    direction_id,
    hour_of_day,
    day_of_week,
    total_observations,
    pct_on_time,
    pct_delayed,
    avg_delay_proxy_seconds,
    avg_secs_since_report,
    avg_speed_kmh,
    current_timestamp() as last_updated_at
from {{ ref('int_route_performance') }}
