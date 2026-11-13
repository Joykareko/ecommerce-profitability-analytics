-- Marketing by month and platform: what each platform claims vs what the store can verify.
--   CAC = spend / new customers whose first order came from that platform (last-click UTM)
--   Platform ROAS = claimed revenue / spend (the platform's own view)
--   First-order ROAS = revenue from the new customers' first orders / spend (verifiable)
--   Amazon: TACoS = ad spend / all Amazon net sales; ACoS = ad spend / sales Amazon credits to ads
with spend as (
    select date_trunc('month', ad_date)::date as month, platform,
           sum(spend) as spend, sum(claimed_revenue) as claimed_revenue, sum(claimed_orders) as claimed_orders
    from {{ ref('stg_ad_spend') }} group by all
),
new_customers as (
    select date_trunc('month', order_date)::date as month,
           case lower(utm_source) when 'meta' then 'Meta' when 'google' then 'Google' when 'tiktok' then 'TikTok' else 'Organic' end as platform,
           count(*) as new_customers,
           sum(subtotal_usd - discount_usd) as first_order_revenue
    from {{ ref('int_store_orders') }}
    where is_first_order
    group by all
),
amazon_sales as (
    select date_trunc('month', order_date)::date as month, 'Amazon Ads' as platform,
           sum(gross_revenue - discount) as amazon_net_sales
    from {{ ref('int_order_lines') }} where channel = 'Amazon' group by all
)
select
    coalesce(s.month, n.month)                                  as month,
    coalesce(s.platform, n.platform)                            as platform,
    coalesce(s.spend, 0)                                        as spend,
    s.claimed_revenue,
    s.claimed_orders,
    n.new_customers,
    n.first_order_revenue,
    s.spend / nullif(n.new_customers, 0)                        as cac,
    s.claimed_revenue / nullif(s.spend, 0)                      as platform_roas,
    n.first_order_revenue / nullif(s.spend, 0)                  as first_order_roas,
    a.amazon_net_sales,
    s.spend / nullif(a.amazon_net_sales, 0)                     as tacos,
    s.spend / nullif(s.claimed_revenue, 0)                      as acos
from spend s
full outer join new_customers n on s.month = n.month and s.platform = n.platform
left join amazon_sales a on a.month = coalesce(s.month, n.month) and a.platform = coalesce(s.platform, n.platform)
where coalesce(s.month, n.month) between date '2025-04-01' and date '2026-09-01'
