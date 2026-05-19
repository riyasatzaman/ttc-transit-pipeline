-- Staging model: cleaned and deduplicated vehicle position observations.
--
-- Source is append-only (every ingestion run inserts a fresh snapshot of the
-- live feed). Within a single feed call, the same (vehicle_id, recorded_at)
-- pair can occasionally appear in two consecutive runs because the upstream
-- feed reports `secsSinceReport` (so the vehicle hasn't moved between calls).
-- We keep the row from the most recent ingestion in that case.

{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'vehicle_positions') }}
),

cleaned as (
    select
        vehicle_id,
        cast(route_id as varchar)        as route_id,
        direction_tag,
        direction_id,
        cast(recorded_at as timestamp)   as recorded_at,
        latitude,
        longitude,
        speed_kmh,
        heading,
        secs_since_report,
        _ingested_at,
        source_file
    from source
    where vehicle_id is not null
      and route_id   is not null
      and recorded_at is not null
)

select *
from cleaned
qualify row_number() over (
    partition by vehicle_id, recorded_at
    order by _ingested_at desc
) = 1
