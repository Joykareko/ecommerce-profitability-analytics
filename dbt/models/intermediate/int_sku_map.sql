-- Every Amazon listing mapped to one canonical SKU: the official map plus documented manual overrides
select seller_sku, sku, 'SKU map' as mapping_source from {{ ref('stg_amazon_sku_map') }}
union all
select seller_sku, sku, 'Manual override' from {{ ref('amazon_listing_overrides') }}
