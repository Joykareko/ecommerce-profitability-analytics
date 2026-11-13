-- Store revenue the ad platforms claim vs revenue the store actually recorded, by month.
-- Platforms each take credit for the same orders, so their claims add up to more than reality.
with claimed as (
    select date_trunc('month', ad_date)::date as month,
           sum(case when platform = 'Meta' then claimed_revenue end)   as meta_claimed,
           sum(case when platform = 'Google' then claimed_revenue end) as google_claimed,
           sum(case when platform = 'TikTok' then claimed_revenue end) as tiktok_claimed
    from {{ ref('stg_ad_spend') }} group by all
),
actual as (
    select date_trunc('month', order_date)::date as month, sum(subtotal_usd - discount_usd) as store_net_sales
    from {{ ref('int_store_orders') }} group by all
)
select a.month, a.store_net_sales,
       coalesce(meta_claimed, 0) as meta_claimed, coalesce(google_claimed, 0) as google_claimed,
       coalesce(tiktok_claimed, 0) as tiktok_claimed,
       coalesce(meta_claimed, 0) + coalesce(google_claimed, 0) + coalesce(tiktok_claimed, 0) as total_claimed,
       (coalesce(meta_claimed, 0) + coalesce(google_claimed, 0) + coalesce(tiktok_claimed, 0)) / a.store_net_sales as claimed_to_actual
from actual a left join claimed c using (month)
where a.month between date '2025-04-01' and date '2026-09-01'
