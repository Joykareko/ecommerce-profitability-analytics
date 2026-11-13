select
    subscription_id,
    customer_id,
    sku,
    cast(interval_days as integer)                     as interval_days,
    cast(created_at as date)                           as started_on,
    try_cast(nullif(cancelled_at, '') as date)         as cancelled_on
from {{ source('raw', 'subscriptions') }}
