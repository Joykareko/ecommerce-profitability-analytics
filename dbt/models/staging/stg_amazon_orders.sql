-- Amazon orders. Fees arrive as negative numbers and are turned into positive costs.
select
    "amazon-order-id"                                                        as amazon_order_id,
    cast(timezone('America/New_York',
         strptime("purchase-date", '%Y-%m-%dT%H:%M:%S%z')) as date)          as order_date,
    "seller-sku"                                                             as seller_sku,
    cast(quantity as integer)                                                as quantity,
    cast("item-price" as double)                                             as item_price,
    cast("item-promotion-discount" as double)                                as promotion_discount,
    -cast("referral-fee" as double)                                          as referral_fee,
    -cast("fba-fee" as double)                                               as fba_fee,
    "order-status"                                                           as order_status,
    currency
from {{ source('raw', 'amazon_orders') }}
