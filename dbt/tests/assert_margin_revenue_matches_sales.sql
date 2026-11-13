-- Gross revenue in the margin table must equal the sales lines it was built from, over the same reporting period
-- (a few Amazon orders placed just after midnight UTC on 1 April fall on 31 March in Eastern time and sit outside it)
with a as (select sum(gross_revenue) as v from {{ ref('fct_contribution_margin') }}),
     b as (select sum(gross_revenue) as v from {{ ref('int_order_lines') }} where order_date between date '2025-04-01' and date '2026-09-30')
select a.v, b.v from a, b where abs(a.v - b.v) > 1
