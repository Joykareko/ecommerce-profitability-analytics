-- Amazon refunds arrive in cents
select
    "order-id"                                         as amazon_order_id,
    cast("return-date" as date)                        as refund_date,
    sku                                                as seller_sku,
    cast(quantity as integer)                          as quantity,
    cast("refund-amount-cents" as integer) / 100.0     as refund_amount,
    reason
from {{ source('raw', 'amazon_returns') }}
