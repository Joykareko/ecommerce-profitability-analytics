-- Unit cost for every product; bundle cost is the sum of its components
with bundle_costs as (
    select b.bundle_sku, sum(b.quantity * p.unit_cost) as bundle_cost
    from {{ ref('stg_bundle_components') }} b
    join {{ ref('stg_products') }} p on p.sku = b.component_sku
    group by 1
)
select
    p.sku, p.brand, p.product_name, p.product_type,
    coalesce(p.unit_cost, bc.bundle_cost)                                     as unit_cost,
    case when p.unit_cost is null then 'Sum of bundle components' else 'Product master' end as cost_source,
    p.store_price, p.amazon_price, p.launch_date
from {{ ref('stg_products') }} p
left join bundle_costs bc on bc.bundle_sku = p.sku
