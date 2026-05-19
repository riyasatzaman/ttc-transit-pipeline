-- Mart: stop-level delay leaderboard. DEFERRED.
--
-- This mart is intentionally disabled in the MVP because the UMOIQ
-- vehicleLocations feed does not provide per-stop arrivals. Implementing it
-- faithfully requires:
--
--   1. Ingesting static GTFS stops + trips + stop_times into RAW
--   2. Computing schedule-vs-actual time deltas at each stop
--      (typically via spatial join of vehicle positions to nearest stop,
--       then matching to the trip's scheduled stop_time)
--
-- The spec is explicit ("Do not fake stop-level precision"), so we keep this
-- file as a documented stub rather than building a mart that pretends to
-- know stop-level data we never observed. See the README "Future
-- improvements" section for the plan.

{{ config(enabled=false) }}

select
    cast(null as varchar)       as stop_id,
    cast(null as varchar)       as stop_name,
    cast(null as varchar)       as route_id,
    cast(null as number(10, 2)) as avg_delay_at_stop,
    cast(null as number(5, 2))  as delay_frequency,
    cast(null as number(10, 0)) as total_observations
where false
