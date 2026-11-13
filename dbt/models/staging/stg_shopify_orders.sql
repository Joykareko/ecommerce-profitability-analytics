-- Store orders: one row per order.
-- Fixes: two timestamp styles, the subscription flag written two ways, webhook duplicates.
-- Test orders are flagged here and removed in the intermediate layer.
with parsed as (
    select
        order_id,
        -- Timestamps are Eastern time with an offset (-0400) or UTC with a trailing Z
        strptime(replace(created_at, 'Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z') as created_at_utc,
        created_at like '%Z'                                              as was_utc_format,
        customer_id,
        nullif(utm_source, '')                                            as utm_source,
        nullif(discount_code, '')                                         as discount_code,
        cast(subtotal_price as double)                                    as subtotal_price,
        cast(total_discounts as double)                                   as total_discounts,
        cast(shipping_price as double)                                    as shipping_price,
        cast(total_tax as double)                                         as total_tax,
        cast(total_price as double)                                       as total_price,
        currency,
        upper(is_subscription) in ('TRUE', '1')                           as is_subscription,
        coalesce(tags, '')                                                as tags
    from {{ source('raw', 'shopify_orders') }}
)
select
    *,
    -- Report every order on its Eastern time business day
    cast(timezone('America/New_York', created_at_utc) as date) as order_date,
    -- coalesce matters: comparing a NULL discount code gives NULL, and NULL rows would vanish from "where not is_test"
    coalesce(tags ilike '%test%' or customer_id = 'C_TEST' or discount_code = 'TESTING100', false) as is_test
from parsed
qualify row_number() over (partition by order_id order by created_at_utc) = 1
