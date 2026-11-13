-- Product master. Bundle costs are blank in the source and are worked out in int_product_costs.
select
    sku,
    brand,
    product_name,
    product_type,
    try_cast(nullif(unit_cost, '') as double)    as unit_cost,
    cast(store_price as double)                    as store_price,
    try_cast(nullif(amazon_price, '') as double) as amazon_price,
    cast(launch_date as date)                      as launch_date
from {{ source('raw', 'products') }}
