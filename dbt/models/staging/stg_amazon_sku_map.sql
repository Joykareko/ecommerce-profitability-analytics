select seller_sku, sku from {{ source('raw', 'amazon_sku_map') }}
