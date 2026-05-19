-- Singular test: stg_vehicle_positions should never contain null route_ids.
-- The staging model already filters them out; this test fails fast if that
-- contract ever silently breaks.

select route_id
from {{ ref('stg_vehicle_positions') }}
where route_id is null
