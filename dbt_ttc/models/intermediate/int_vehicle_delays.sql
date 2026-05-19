-- Intermediate: per-observation enrichment of stg_vehicle_positions.
--
-- Adds:
--   - route_name from stg_routes (so the dashboard can show "Bathurst" not "7")
--   - hour_of_day / day_of_week for time-based aggregations
--   - seconds_since_prev_report: time gap to *this vehicle's* previous report.
--     Per-vehicle LAG is more interpretable than a per-route LAG, which would
--     be dominated by the many vehicles reporting on a route at the same time.
--   - is_delayed / delay_proxy_seconds: honest "something off" signal derived
--     from secs_since_report. Without stop-level GTFS data we can't compute
--     true schedule adherence; this proxies "vehicle hasn't pinged the feed
--     in a normal window" which correlates with breakdowns / loss-of-signal.

{{ config(materialized='view') }}

with positions as (
    select * from {{ ref('stg_vehicle_positions') }}
),

routes as (
    select route_id, route_long_name from {{ ref('stg_routes') }}
),

enriched as (
    select
        p.vehicle_id,
        p.route_id,
        coalesce(r.route_long_name, p.route_id) as route_name,
        p.direction_id,
        p.recorded_at,
        date_part('hour', p.recorded_at)         as hour_of_day,
        dayofweek(p.recorded_at)                 as day_of_week,
        p.latitude,
        p.longitude,
        p.speed_kmh,
        p.secs_since_report,
        datediff(
            'second',
            lag(p.recorded_at) over (
                partition by p.vehicle_id
                order by p.recorded_at
            ),
            p.recorded_at
        )                                        as seconds_since_prev_report,
        iff(p.secs_since_report > 120, true, false)        as is_delayed,
        greatest(0, p.secs_since_report - 120)             as delay_proxy_seconds
    from positions p
    left join routes r on p.route_id = r.route_id
)

select * from enriched
