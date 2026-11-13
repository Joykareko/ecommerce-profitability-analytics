-- Real store orders only (test orders removed), with every amount converted to US dollars
with assumptions as (
    select
        max(case when name = 'store_shipping_first_unit' then value end) as ship_first,
        max(case when name = 'store_shipping_extra_unit' then value end) as ship_extra,
        max(case when name = 'payment_fee_rate'          then value end) as fee_rate,
        max(case when name = 'payment_fee_fixed'         then value end) as fee_fixed
    from {{ ref('cost_assumptions') }}
),
units as (
    select order_id, sum(quantity) as units from {{ ref('stg_shopify_order_lines') }} group by 1
)
select
    o.order_id, o.order_date, o.customer_id, o.utm_source, o.discount_code, o.is_subscription, o.currency,
    case when o.currency = 'CAD' then fx.cad_per_usd else 1 end            as fx_rate,
    o.subtotal_price  / case when o.currency = 'CAD' then fx.cad_per_usd else 1 end as subtotal_usd,
    o.total_discounts / case when o.currency = 'CAD' then fx.cad_per_usd else 1 end as discount_usd,
    o.shipping_price  / case when o.currency = 'CAD' then fx.cad_per_usd else 1 end as shipping_charged_usd,
    o.total_price     / case when o.currency = 'CAD' then fx.cad_per_usd else 1 end as total_usd,
    u.units,
    a.ship_first + a.ship_extra * (u.units - 1)                             as shipping_cost_usd,
    a.fee_rate * o.total_price / case when o.currency = 'CAD' then fx.cad_per_usd else 1 end + a.fee_fixed as payment_fee_usd,
    row_number() over (partition by o.customer_id order by o.created_at_utc) = 1 as is_first_order
from {{ ref('stg_shopify_orders') }} o
join units u using (order_id)
left join {{ ref('stg_fx_rates') }} fx on fx.month = date_trunc('month', o.order_date)
cross join assumptions a
where not o.is_test
