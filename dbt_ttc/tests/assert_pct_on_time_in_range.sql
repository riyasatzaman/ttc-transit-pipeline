-- Singular test: pct_on_time must stay within 0-100 in all dashboard marts.
-- Catches arithmetic bugs (e.g. dividing by the wrong denominator) that
-- would silently produce nonsense leaderboard values.

select 'mart_route_delay_summary' as failing_mart, route_id, pct_on_time
from {{ ref('mart_route_delay_summary') }}
where pct_on_time < 0 or pct_on_time > 100

union all

select 'mart_hourly_reliability'  as failing_mart, route_id, pct_on_time
from {{ ref('mart_hourly_reliability') }}
where pct_on_time < 0 or pct_on_time > 100
