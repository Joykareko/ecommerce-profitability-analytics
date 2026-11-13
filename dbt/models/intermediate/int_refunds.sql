-- Refunds from both channels in US dollars. Store refunds for orders before April 2025 have no matching order.
select
    'Store'                         as channel,
    r.order_id, r.refund_date, r.sku, r.quantity, r.refund_amount, r.reason,
    o.order_id is null              as has_no_matching_order
from {{ ref('stg_shopify_refunds') }} r
left join {{ ref('int_store_orders') }} o using (order_id)
union all
select
    'Amazon', r.amazon_order_id, r.refund_date, m.sku, r.quantity, r.refund_amount, r.reason, false
from {{ ref('stg_amazon_returns') }} r
left join {{ ref('int_sku_map') }} m using (seller_sku)
