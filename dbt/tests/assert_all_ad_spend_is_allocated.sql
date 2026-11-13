-- Every dollar of advertising in the reporting period must be assigned to a product in the margin table
with spend as (
    select sum(spend) as total from {{ ref('stg_ad_spend') }}
    where ad_date between date '2025-04-01' and date '2026-09-30'
),
allocated as (select sum(marketing) as total from {{ ref('fct_contribution_margin') }})
select spend.total as spend, allocated.total as allocated
from spend, allocated
where abs(spend.total - allocated.total) > 1
