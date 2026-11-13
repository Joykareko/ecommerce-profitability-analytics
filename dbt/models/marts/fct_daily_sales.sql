-- Daily units and sales by channel and SKU (net of discounts, before refunds)
select order_date, channel, brand, sku,
       sum(quantity)                     as units,
       sum(gross_revenue)                as gross_revenue,
       sum(gross_revenue - discount)     as net_sales
from {{ ref('int_order_lines') }}
where order_date <= date '2026-09-30'
group by all
