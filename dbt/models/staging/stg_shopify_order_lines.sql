-- Products in each store order. Fixes lowercase SKUs, trailing spaces, the pre-July 2025 SKU name and duplicates.
with cleaned as (
    select
        l.order_id,
        l.sku                                   as raw_sku,
        coalesce(a.sku, upper(trim(l.sku)))     as sku,
        cast(l.quantity as integer)             as quantity,
        cast(l.price as double)                 as unit_price
    from {{ source('raw', 'shopify_order_lines') }} l
    left join {{ ref('sku_aliases') }} a on upper(trim(l.sku)) = a.raw_sku
)
select * from cleaned
qualify row_number() over (partition by order_id, sku order by unit_price) = 1
