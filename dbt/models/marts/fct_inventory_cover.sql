-- Latest stock on hand and weeks of cover by SKU and location.
-- Warehouse demand = store units, including units used inside bundles; Amazon FBA demand = Amazon units.
-- Weeks of cover = stock on hand / average weekly units over the 8 weeks before the snapshot.
with latest as (
    select location, max(snapshot_date) as snapshot_date from {{ ref('stg_inventory_snapshots') }} group by 1
),
store_units as (
    select l.order_date, coalesce(b.component_sku, l.sku) as sku, l.quantity * coalesce(b.quantity, 1) as units
    from {{ ref('int_order_lines') }} l
    left join {{ ref('stg_bundle_components') }} b on b.bundle_sku = l.sku
    where l.channel = 'Store'
),
demand as (
    select 'Warehouse' as location, sku, sum(units) / 8.0 as avg_weekly_units
    from store_units, latest
    where latest.location = 'Warehouse' and order_date between latest.snapshot_date - 56 and latest.snapshot_date - 1
    group by all
    union all
    select 'Amazon FBA', l.sku, sum(l.quantity) / 8.0
    from {{ ref('int_order_lines') }} l, latest
    where latest.location = 'Amazon FBA' and l.channel = 'Amazon'
      and l.order_date between latest.snapshot_date - 56 and latest.snapshot_date - 1
    group by all
)
select i.snapshot_date, i.location, i.sku, p.brand, p.product_name, i.on_hand,
       d.avg_weekly_units,
       i.on_hand / nullif(d.avg_weekly_units, 0) as weeks_of_cover,
       i.on_hand * p.unit_cost                   as stock_value_at_cost
from {{ ref('stg_inventory_snapshots') }} i
join latest using (location, snapshot_date)
left join demand d using (location, sku)
left join {{ ref('int_product_costs') }} p using (sku)
