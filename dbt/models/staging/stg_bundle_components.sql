select bundle_sku, component_sku, cast(quantity as integer) as quantity
from {{ source('raw', 'bundle_components') }}
