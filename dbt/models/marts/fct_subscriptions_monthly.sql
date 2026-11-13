-- Subscriptions by month. Churn rate = cancellations in the month / subscriptions active at the start of it.
with months as (
    select unnest(generate_series(date '2025-04-01', date '2026-09-01', interval 1 month))::date as month
)
select
    m.month,
    count(*) filter (where s.started_on < m.month and (s.cancelled_on is null or s.cancelled_on >= m.month))           as active_at_start,
    count(*) filter (where date_trunc('month', s.started_on) = m.month)                                                as started,
    count(*) filter (where date_trunc('month', s.cancelled_on) = m.month)                                              as cancelled,
    count(*) filter (where date_trunc('month', s.cancelled_on) = m.month) * 1.0
      / nullif(count(*) filter (where s.started_on < m.month and (s.cancelled_on is null or s.cancelled_on >= m.month)), 0) as churn_rate
from months m
cross join {{ ref('stg_subscriptions') }} s
group by m.month
