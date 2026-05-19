-- Intermediate: per-route × direction × hour × day-of-week aggregates.
--
-- Reduces the row-level int_vehicle_delays observations down to a
-- recruitable-friendly grain that all three marts read from:
--   - mart_route_delay_summary collapses this to route level
--   - mart_hourly_reliability uses this nearly verbatim
--   - mart_worst_stops would aggregate further (stop-level, later)

{{ config(materialized='view') }}

select
    route_id,
    route_name,
    direction_id,
    hour_of_day,
    day_of_week,
    count(*)                                                          as total_observations,
    sum(iff(is_delayed, 1, 0))                                        as delayed_observations,
    round(100.0 * sum(iff(is_delayed, 1, 0)) / count(*), 2)           as pct_delayed,
    round(100.0 - 100.0 * sum(iff(is_delayed, 1, 0)) / count(*), 2)   as pct_on_time,
    round(avg(delay_proxy_seconds), 2)                                as avg_delay_proxy_seconds,
    round(avg(secs_since_report), 2)                                  as avg_secs_since_report,
    round(avg(speed_kmh), 2)                                          as avg_speed_kmh
from {{ ref('int_vehicle_delays') }}
group by 1, 2, 3, 4, 5
