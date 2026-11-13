select
    r.refund_id,
    r.order_id,
    cast(r.created_at as date)              as refund_date,
    coalesce(a.sku, upper(trim(r.sku)))     as sku,
    cast(r.quantity as integer)             as quantity,
    cast(r.amount as double)                as refund_amount,
    r.reason
from {{ source('raw', 'shopify_refunds') }} r
left join {{ ref('sku_aliases') }} a on upper(trim(r.sku)) = a.raw_sku
