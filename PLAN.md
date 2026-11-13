# E-commerce Profitability Analytics: project plan

## The business

Freshkind Brands (fictional) sells sweat and odour care products under three brands: Brisk & Bold (men), Curvella (women) and SoleFresh (feet). It sells through its own Shopify store, with one-off orders and subscriptions, and on Amazon, fulfilled by Amazon (FBA). It advertises on Meta, Google, TikTok and Amazon.

## The questions

1. Which products and channels actually make money after discounts, refunds, fees, shipping and advertising?
2. Where are we losing sales or tying up cash because of stock?
3. Which marketing spend brings in customers at a sensible cost, and how much do the ad platforms overstate their results?
4. Are subscribers staying, and what made them leave?
5. Is any product causing unhappy customers?

## Stages

| Stage | What | Status |
| --- | --- | --- |
| 1 | Plan and synthetic data generator | Done |
| 2 | Cleaning, quality checks, dbt models (staging, intermediate, marts), 70 tests | Done |
| 3 | Findings, charts, customer lifetime value and segments, README | Done |
| 4 | Power BI dashboard (Joy builds it, step by step) | Next |

## Raw data (data/raw), April 2025 to September 2026

| File | Rows | What it is | Mess built in |
| --- | --- | --- | --- |
| products.csv | 15 | Product master | Bundle costs missing; work them out from bundle_components.csv |
| shopify_orders.csv | 144k | Own store orders | Two timestamp styles (Eastern time with offset, or UTC), 3% in Canadian dollars, subscription flag written as TRUE/FALSE or 1/0, 35 test orders, about 1,100 duplicate rows |
| shopify_order_lines.csv | 165k | Products in each order | Lowercase SKUs, trailing spaces, an old SKU name used before July 2025 |
| shopify_refunds.csv | 5.5k | Money-back guarantee refunds | 25 refunds for orders placed before the data starts |
| subscriptions.csv | 13k | Subscriptions with start and cancel dates | |
| amazon_orders.csv | 192k | Amazon orders with referral and FBA fees | Fees are negative numbers, cancelled orders included, an old listing missing from the SKU map |
| amazon_returns.csv | 8.4k | Amazon refunds | Amounts in cents, not dollars |
| inventory_snapshots.csv | 1.9k | Weekly stock, warehouse and Amazon | Some warehouse weeks missing |
| meta_ads.csv, google_ads.csv, tiktok_ads.csv, amazon_ads.csv | daily | Ad platform exports | Three date formats, spend with thousands commas, Google cost in micros (millionths), platforms claim overlapping credit |
| fx_rates.csv | 18 | Monthly CAD per USD | |

`_answer_key.json` records what the generator built in, so the pipeline's findings can be checked against the truth. The analysis never reads it.

## Stories the pipeline should find

1. The Travel Trio is Amazon's second best seller by units, but after fees and its advertising it loses money.
2. The best seller ran out at Amazon from 6 to 26 July 2026, over Prime Day, and sales took two weeks to recover.
3. The Coconut cream launched in February 2026 is refunded about 14% of the time, against about 3% for other products, mostly for irritation and scent.
4. Cutting the subscription discount from 15% to 5% in March 2026 more than doubled cancellations for two months.
5. Meta's cost per new customer rose from about $38 to $63 during 2026 on the same budget, while Google stayed around $31.
6. Ad platforms together claim more revenue than the store made.
7. SoleFresh Foot Powder has about 40 weeks of stock in the warehouse.
