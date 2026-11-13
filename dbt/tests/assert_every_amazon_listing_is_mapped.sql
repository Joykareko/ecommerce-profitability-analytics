-- Fails if any Amazon listing has no canonical SKU, which would make its sales disappear
select distinct a.seller_sku
from {{ ref('stg_amazon_orders') }} a
left join {{ ref('int_sku_map') }} m using (seller_sku)
where m.sku is null
