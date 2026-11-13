select cast(snapshot_date as date) as snapshot_date, location, sku, cast(on_hand as integer) as on_hand
from {{ source('raw', 'inventory_snapshots') }}
