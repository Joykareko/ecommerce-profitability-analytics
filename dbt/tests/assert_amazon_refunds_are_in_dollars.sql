-- No single Amazon order is worth more than about $80, so a larger refund means cents were not converted
select * from {{ ref('stg_amazon_returns') }} where refund_amount > 100
