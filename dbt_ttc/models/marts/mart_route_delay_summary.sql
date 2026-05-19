-- Mart: route reliability leaderboard.
-- One row per route. The dashboard's "Route Reliability" page sorts on
-- pct_on_time and highlights routes by tier (>80 green, 60-80 yellow, <60 red).
--
-- Sourced directly from int_vehicle_delays so the percentages are the true
-- overall rate, not an average-of-averages across hour/day groups.

{{ config(materialized='table') }}

with delays as (
    select * from {{ ref('int_vehicle_delays') }}
)

select
    route_id,
    any_value(route_name)                                              as route_name,
    count(*)                                                           as total_observations,
    count(distinct vehicle_id)                                         as distinct_vehicles,
    round(avg(delay_proxy_seconds), 2)                                 as avg_delay_proxy_seconds,
    round(avg(secs_since_report), 2)                                   as avg_secs_since_report,
    round(avg(speed_kmh), 2)                                           as avg_speed_kmh,
    round(100.0 * sum(iff(is_delayed, 1, 0)) / count(*), 2)            as pct_delayed,
    round(100.0 - 100.0 * sum(iff(is_delayed, 1, 0)) / count(*), 2)    as pct_on_time,
    max(recorded_at)                                                   as last_observed_at,
    current_timestamp()                                                as last_updated_at
from delays
group by route_id
