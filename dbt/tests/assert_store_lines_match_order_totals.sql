-- Fails if the products in an order do not add up to the order subtotal (catches lost or duplicated lines)
select o.order_id, o.subtotal_usd, sum(l.gross_revenue) as lines_total
from {{ ref('int_store_orders') }} o
join {{ ref('int_order_lines') }} l on l.order_id = o.order_id and l.channel = 'Store'
group by 1, 2
having abs(o.subtotal_usd - sum(l.gross_revenue)) > 0.05
