-- One row per day, platform and campaign, from four exports that each use their own format.
-- Claimed revenue is what each platform says its ads produced; platforms overlap, so it is not real revenue.
select strptime("Day", '%m/%d/%Y')::date as ad_date, 'Meta' as platform, "Campaign name" as campaign,
       cast(replace("Amount spent (USD)", ',', '') as double) as spend,
       cast("Purchase conversion value" as double) as claimed_revenue,
       cast("Purchases" as double) as claimed_orders
from {{ source('raw', 'meta_ads') }}
union all
-- Google reports cost in micros: millionths of a dollar
select cast("Date" as date), 'Google', "Campaign",
       cast("Cost (micros)" as bigint) / 1000000.0,
       cast("Conv. value" as double), cast("Conversions" as double)
from {{ source('raw', 'google_ads') }}
union all
select cast(stat_time_day as timestamp)::date, 'TikTok', campaign_name,
       cast(spend as double), cast(total_purchase_value as double), cast(conversions as double)
from {{ source('raw', 'tiktok_ads') }}
union all
select cast(date as date), 'Amazon Ads', campaign,
       cast(spend as double), cast(sales_14d as double), cast(orders_14d as double)
from {{ source('raw', 'amazon_ads') }}
