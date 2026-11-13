-- One row per product sold, across both channels, in US dollars, with every cost needed for contribution margin.
-- Store order-level costs (discount, shipping, payment fees) are shared across lines by revenue.
with store as (
    select
        'Store'                                              as channel,
        l.order_id,
        o.order_date,
        o.customer_id,
        l.sku,
        l.quantity,
        l.unit_price * l.quantity / o.fx_rate                as gross_revenue,
        (l.unit_price * l.quantity / o.fx_rate) / nullif(o.subtotal_usd, 0) as revenue_share,
        o.discount_usd, o.payment_fee_usd, o.shipping_cost_usd, o.shipping_charged_usd
    from {{ ref('stg_shopify_order_lines') }} l
    join {{ ref('int_store_orders') }} o using (order_id)
),
store_lines as (
    select channel, order_id, order_date, customer_id, sku, quantity, gross_revenue,
           revenue_share * discount_usd                                         as discount,
           0.0                                                                    as marketplace_fees,
           revenue_share * payment_fee_usd                                      as payment_fees,
           revenue_share * (shipping_cost_usd - shipping_charged_usd)         as net_shipping_cost
    from store
),
amazon_lines as (
    select
        'Amazon'                     as channel,
        a.amazon_order_id            as order_id,
        a.order_date,
        null                         as customer_id,
        m.sku,
        a.quantity,
        a.item_price                 as gross_revenue,
        a.promotion_discount         as discount,
        a.referral_fee + a.fba_fee   as marketplace_fees,
        0.0                          as payment_fees,
        0.0                          as net_shipping_cost
    from {{ ref('stg_amazon_orders') }} a
    left join {{ ref('int_sku_map') }} m using (seller_sku)
    where a.order_status = 'Shipped'
)
select l.*, p.brand, p.product_name, l.quantity * p.unit_cost as cogs
from (select * from store_lines union all select * from amazon_lines) l
left join {{ ref('int_product_costs') }} p using (sku)
