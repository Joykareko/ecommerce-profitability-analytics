-- Fails if a test order reaches the sales tables
select l.order_id
from {{ ref('int_order_lines') }} l
join {{ ref('stg_shopify_orders') }} o using (order_id)
where o.is_test
