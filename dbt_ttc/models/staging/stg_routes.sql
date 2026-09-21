-- Staging model: one row per TTC route.
--
-- Source is append-only — each ingestion run adds a snapshot of every route.
-- Route metadata almost never changes, so we keep only the most recent
-- observation per route_id (latest _ingested_at wins).
--
-- The feed gives us route_short_name and route_long_name directly, so we
-- just pass them through.

{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'routes') }}
),

deduped as (
    select
        route_id,
        route_short_name,
        route_long_name,
        _ingested_at
    from source
    where route_id is not null
    qualify row_number() over (
        partition by route_id
        order by _ingested_at desc
    ) = 1
)

select
    route_id,
    route_short_name,
    route_long_name,
    _ingested_at
from deduped
