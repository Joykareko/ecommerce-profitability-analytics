-- One row per store customer: how they were acquired, what they bought first, what they are worth, and a behavioural segment.
-- Customer value uses CM2 (after product, payment, shipping and refunds, before advertising), so it can be compared with CAC.
-- Amazon does not share customer identities with sellers, so this covers store customers only.
{% set as_of = "date '2026-09-30'" %}
with refunds as (
    select order_id, sum(refund_amount) as refunds from {{ ref('int_refunds') }} where channel = 'Store' group by 1
),
line_costs as (
    select order_id, sum(cogs) as cogs, sum(payment_fees) as payment_fees, sum(net_shipping_cost) as net_shipping_cost
    from {{ ref('int_order_lines') }} where channel = 'Store' group by 1
),
orders as (
    select o.order_id, o.customer_id, o.order_date, o.is_subscription, o.is_first_order, o.utm_source, o.currency,
           o.subtotal_usd - o.discount_usd                                              as net_sales,
           o.subtotal_usd - o.discount_usd - coalesce(r.refunds, 0)
             - lc.cogs - lc.payment_fees - lc.net_shipping_cost                         as cm2
    from {{ ref('int_store_orders') }} o
    join line_costs lc using (order_id)
    left join refunds r using (order_id)
),
first_orders as (
    select customer_id, order_id as first_order_id, order_date as first_order_date,
           case lower(utm_source) when 'meta' then 'Meta' when 'google' then 'Google'
                                  when 'tiktok' then 'TikTok' else 'Organic' end         as acquisition_channel,
           case currency when 'CAD' then 'Canada' else 'United States' end              as market
    from orders where is_first_order
),
first_product as (
    select l.order_id as first_order_id, l.sku as first_sku, l.brand as first_brand
    from {{ ref('int_order_lines') }} l
    join first_orders f on f.first_order_id = l.order_id
    qualify row_number() over (partition by l.order_id order by l.gross_revenue desc, l.sku) = 1
),
subs as (
    select customer_id,
           true as ever_subscribed,
           bool_or(cancelled_on is null) as active_subscriber
    from {{ ref('stg_subscriptions') }} group by 1
),
totals as (
    select o.customer_id,
           count(*)                                                                        as orders,
           sum(o.net_sales)                                                                as net_sales,
           sum(o.cm2)                                                                      as lifetime_cm2,
           sum(o.cm2) filter (where o.order_date <  f.first_order_date + 91)               as cm2_first_3m,
           sum(o.cm2) filter (where o.order_date <  f.first_order_date + 182)              as cm2_first_6m,
           sum(o.cm2) filter (where o.order_date <  f.first_order_date + 365)              as cm2_first_12m,
           count(*) filter (where o.order_date < f.first_order_date + 365)                 as orders_first_12m,
           max(o.order_date)                                                               as last_order_date
    from orders o join first_orders f using (customer_id)
    group by 1
)
select
    f.customer_id, f.first_order_date, date_trunc('month', f.first_order_date)::date as cohort_month,
    f.acquisition_channel, f.market, fp.first_sku, fp.first_brand,
    coalesce(s.ever_subscribed, false)    as ever_subscribed,
    coalesce(s.active_subscriber, false)  as active_subscriber,
    t.orders, t.net_sales, t.lifetime_cm2, t.cm2_first_3m, t.cm2_first_6m, t.cm2_first_12m, t.orders_first_12m,
    t.last_order_date,
    {{ as_of }} - t.last_order_date        as days_since_last_order,
    {{ as_of }} - f.first_order_date       as days_as_customer,
    -- Simple, explainable segments based on subscription status, recency and frequency
    case
        when coalesce(s.active_subscriber, false)                                   then 'Active subscriber'
        when f.first_order_date >= {{ as_of }} - 60                                  then 'New customer'
        when t.orders >= 3 and {{ as_of }} - t.last_order_date <= 120                then 'Loyal repeat buyer'
        when coalesce(s.ever_subscribed, false)                                      then 'Lapsed subscriber'
        when t.orders >= 2 and {{ as_of }} - t.last_order_date <= 180                then 'Returning buyer'
        when t.orders = 1                                                            then 'One-time buyer'
        else 'Drifting away'
    end as segment
from first_orders f
join totals t using (customer_id)
left join first_product fp using (first_order_id)
left join subs s using (customer_id)
