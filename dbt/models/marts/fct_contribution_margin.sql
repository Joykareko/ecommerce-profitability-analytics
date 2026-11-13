-- Contribution margin by month, channel, brand and SKU.
--   Net revenue = gross revenue - discounts - refunds
--   CM1 = net revenue - cost of goods
--   CM2 = CM1 - marketplace fees (Amazon referral and FBA) - payment fees - net store shipping
--   CM3 = CM2 - advertising
-- Advertising: Amazon campaigns are shared across the SKUs they promote by Amazon net sales;
-- Meta, Google and TikTok spend is shared across store SKUs by store net sales.
with lines as (
    select date_trunc('month', order_date)::date as month, channel, sku,
           sum(quantity) as units, sum(gross_revenue) as gross_revenue, sum(discount) as discounts,
           sum(cogs) as cogs, sum(marketplace_fees) as marketplace_fees,
           sum(payment_fees) as payment_fees, sum(net_shipping_cost) as net_shipping_cost
    from {{ ref('int_order_lines') }}
    group by all
),
refunds as (
    select date_trunc('month', refund_date)::date as month, channel, sku, sum(refund_amount) as refunds
    from {{ ref('int_refunds') }}
    group by all
),
base as (
    select
        coalesce(l.month, r.month)           as month,
        coalesce(l.channel, r.channel)       as channel,
        coalesce(l.sku, r.sku)               as sku,
        coalesce(l.units, 0)                 as units,
        coalesce(l.gross_revenue, 0)         as gross_revenue,
        coalesce(l.discounts, 0)             as discounts,
        coalesce(r.refunds, 0)               as refunds,
        coalesce(l.cogs, 0)                  as cogs,
        coalesce(l.marketplace_fees, 0)      as marketplace_fees,
        coalesce(l.payment_fees, 0)          as payment_fees,
        coalesce(l.net_shipping_cost, 0)     as net_shipping_cost
    from lines l
    full outer join refunds r on l.month = r.month and l.channel = r.channel and l.sku = r.sku
    where coalesce(l.month, r.month) between date '2025-04-01' and date '2026-09-01'
),
amazon_campaign_spend as (
    select date_trunc('month', ad_date)::date as month, campaign, sum(spend) as spend
    from {{ ref('stg_ad_spend') }} where platform = 'Amazon Ads' group by all
),
amazon_shares as (
    select b.month, b.sku, m.campaign,
           (b.gross_revenue - b.discounts) / sum(b.gross_revenue - b.discounts) over (partition by b.month, m.campaign) as share
    from base b
    join {{ ref('ad_campaign_mapping') }} m on b.sku like m.sku_pattern
    where b.channel = 'Amazon' and b.gross_revenue > 0
),
amazon_marketing as (
    select s.month, 'Amazon' as channel, s.sku, sum(s.share * c.spend) as marketing
    from amazon_shares s join amazon_campaign_spend c using (month, campaign)
    group by all
),
store_spend as (
    select date_trunc('month', ad_date)::date as month, sum(spend) as spend
    from {{ ref('stg_ad_spend') }} where platform in ('Meta', 'Google', 'TikTok') group by all
),
store_marketing as (
    select b.month, 'Store' as channel, b.sku,
           (b.gross_revenue - b.discounts) / sum(b.gross_revenue - b.discounts) over (partition by b.month) * s.spend as marketing
    from base b join store_spend s using (month)
    where b.channel = 'Store' and b.gross_revenue > 0
),
marketing as (select * from amazon_marketing union all select * from store_marketing),
calc as (
    select b.*, p.brand, p.product_name,
           coalesce(mk.marketing, 0)                                         as marketing,
           b.gross_revenue - b.discounts - b.refunds                          as net_revenue
    from base b
    left join marketing mk using (month, channel, sku)
    left join {{ ref('int_product_costs') }} p using (sku)
)
select
    month, channel, brand, sku, product_name, units,
    gross_revenue, discounts, refunds, net_revenue, cogs,
    net_revenue - cogs                                                                   as cm1,
    marketplace_fees, payment_fees, net_shipping_cost,
    net_revenue - cogs - marketplace_fees - payment_fees - net_shipping_cost             as cm2,
    marketing,
    net_revenue - cogs - marketplace_fees - payment_fees - net_shipping_cost - marketing as cm3
from calc
