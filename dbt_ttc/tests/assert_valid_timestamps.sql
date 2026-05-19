-- Singular test: recorded_at values should be plausible (not in the future
-- and not before the TTC live feed existed in any reasonable form).
--
-- Timezone subtlety: recorded_at is stored as TIMESTAMP_NTZ representing
-- UTC, but Snowflake's `current_timestamp()` returns TIMESTAMP_LTZ in the
-- *session* timezone (default America/Los_Angeles). A naive comparison
-- would interpret recorded_at as PST and flag every recent row as "in the
-- future" by ~7 hours. We explicitly pin the comparison to UTC to dodge
-- that. A 5-minute buffer absorbs trivial clock skew between Snowflake
-- and the ingestion host.

select recorded_at
from {{ ref('stg_vehicle_positions') }}
where recorded_at > convert_timezone('UTC', current_timestamp())::timestamp_ntz + interval '5 minutes'
   or recorded_at < '2020-01-01'::timestamp
