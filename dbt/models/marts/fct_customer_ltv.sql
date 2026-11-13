-- Average customer value (CM2 per customer) in the first 3, 6 and 12 months, by acquisition channel, first product and market.
-- Only customers whose window has fully passed are counted, so newer customers do not drag the averages down:
-- 12-month value uses customers acquired by 30 Sep 2025, 6-month value by 31 Mar 2026, 3-month value by 30 Jun 2026.
with c as (select * from {{ ref('fct_customers') }}),
long as (
    select 'Acquisition channel' as dimension, acquisition_channel as value, * from c
    union all select 'First product', first_sku, * from c
    union all select 'Market', market, * from c
    union all select 'All customers', 'All', * from c
)
select
    dimension, value,
    count(*)                                                                                   as customers,
    avg(cm2_first_3m)  filter (where first_order_date <= date '2026-06-30')                     as ltv_3m,
    avg(cm2_first_6m)  filter (where first_order_date <= date '2026-03-31')                     as ltv_6m,
    avg(cm2_first_12m) filter (where first_order_date <= date '2025-09-30')                     as ltv_12m,
    avg((orders_first_12m >= 2)::int) filter (where first_order_date <= date '2025-09-30')      as repeat_rate_12m,
    avg(ever_subscribed::int)                                                                   as subscriber_share
from long
group by all
