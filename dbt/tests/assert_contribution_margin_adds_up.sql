-- CM3 must equal net revenue minus every cost line
select * from {{ ref('fct_contribution_margin') }}
where abs(cm3 - (net_revenue - cogs - marketplace_fees - payment_fees - net_shipping_cost - marketing)) > 0.01
