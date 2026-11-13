-- Canadian dollars per US dollar, one rate per month
select cast(month || '-01' as date) as month, cast(cad_per_usd as double) as cad_per_usd
from {{ source('raw', 'fx_rates') }}
