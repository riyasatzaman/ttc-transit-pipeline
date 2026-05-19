-- Staging model: one row per TTC route.
--
-- Source is append-only — each ingestion run adds a snapshot of every route.
-- Route metadata almost never changes, so we keep only the most recent
-- observation per route_id (latest _ingested_at wins).
--
-- The UMOIQ feed gives us a single `route_title` like "7-Bathurst". We split
-- on the first hyphen into short_name ("7") and long_name ("Bathurst") so the
-- dashboard can label routes nicely.

{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'routes') }}
),

deduped as (
    select
        route_id,
        route_title,
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
    route_title,
    split_part(route_title, '-', 1) as route_short_name,
    trim(substr(route_title, position('-' in route_title) + 1)) as route_long_name,
    _ingested_at
from deduped
