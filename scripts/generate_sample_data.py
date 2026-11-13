"""
Generate 18 months of synthetic raw data (April 2025 to September 2026) for a fictional
body-care company, Freshkind Brands, that sells sweat and odour care products through its
own Shopify store and on Amazon (fulfilled by Amazon, FBA).

Three brands: Brisk & Bold (men), Curvella (women) and SoleFresh (feet).

Raw files, written the way each system exports them:
    products.csv, bundle_components.csv        product master (bundle costs missing)
    shopify_orders.csv, shopify_order_lines.csv  own store orders
    shopify_refunds.csv, subscriptions.csv     money-back guarantee refunds, subscriptions
    amazon_orders.csv, amazon_sku_map.csv      Amazon orders with fees, listing to SKU map
    amazon_returns.csv                          Amazon refunds (in cents)
    inventory_snapshots.csv                     weekly stock on hand, warehouse and FBA
    meta_ads.csv, google_ads.csv, tiktok_ads.csv, amazon_ads.csv   ad platform exports
    fx_rates.csv                                monthly CAD to USD rates

Built-in stories for the pipeline to find (truth saved in _answer_key.json):
  1. A cheap Amazon bundle sells lots of units but loses money after fees and ads.
  2. The best seller runs out of stock at Amazon for three weeks in July 2026, over Prime Day.
  3. A new scent launched in February 2026 gets refunded far more than anything else.
  4. A smaller subscription discount from March 2026 causes a wave of cancellations.
  5. Meta keeps the same budget while the cost of each new customer rises sharply in 2026.
  6. Ad platforms claim more revenue than the store actually made.
  7. One product sits in the warehouse with about 40 weeks of stock.

All data is synthetic. Freshkind and its brands are invented.

    python scripts/generate_sample_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(23)
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
DAYS = pd.date_range("2025-04-01", "2026-09-30", freq="D")
SUB_CHANGE = pd.Timestamp("2026-03-01")          # subscription discount cut from 15% to 5%
STOCKOUT = (pd.Timestamp("2026-07-06"), pd.Timestamp("2026-07-26"))
RECOVERY_END = pd.Timestamp("2026-08-09")
PRIME_DAYS = [pd.Timestamp("2025-07-08"), pd.Timestamp("2025-07-09"), pd.Timestamp("2026-07-14"), pd.Timestamp("2026-07-15")]
BLACK_FRIDAY = (pd.Timestamp("2025-11-27"), pd.Timestamp("2025-12-01"))
COCONUT_LAUNCH = pd.Timestamp("2026-02-01")
SKU_RENAME = pd.Timestamp("2025-07-01")          # BB-CREAM-UNSC renamed to BB-CRM-UNS

# sku: brand, name, type, unit cost, store price, Amazon price, FBA fee, Amazon daily units, store weight
PRODUCTS = {
    "BB-CRM-UNS": ("Brisk & Bold", "Comfort Cream Unscented 6oz", "Cream deodorant", 3.10, 19.99, 19.99, 4.25, 70, 0.16),
    "BB-CRM-CED": ("Brisk & Bold", "Comfort Cream Cedar 6oz", "Cream deodorant", 3.10, 19.99, 19.99, 4.25, 25, 0.07),
    "BB-CRM-CIT": ("Brisk & Bold", "Comfort Cream Citrus 6oz", "Cream deodorant", 3.10, 19.99, 19.99, 4.25, 20, 0.06),
    "BB-PWD-UNS": ("Brisk & Bold", "Body Powder Talc-Free 4oz", "Powder", 2.40, 16.99, 16.99, 4.00, 30, 0.08),
    "BB-WIP-20": ("Brisk & Bold", "Body Wipes 20ct", "Wipes", 2.20, 12.99, 12.99, 3.90, 22, 0.05),
    "BB-TRV-TRIO": ("Brisk & Bold", "Travel Trio (3 minis)", "Bundle", 4.60, 24.99, 15.99, 6.80, 50, 0.04),
    "CV-BALM": ("Curvella", "Anti-Chafe Balm 2oz", "Balm", 2.90, 17.99, 17.99, 4.10, 28, 0.10),
    "CV-CRM-UNS": ("Curvella", "Cream Deodorant Unscented 3oz", "Cream deodorant", 3.10, 19.99, 19.99, 4.25, 18, 0.07),
    "CV-CRM-LAV": ("Curvella", "Cream Deodorant Lavender 3oz", "Cream deodorant", 3.10, 19.99, 19.99, 4.25, 12, 0.06),
    "CV-CRM-COC": ("Curvella", "Cream Deodorant Coconut 3oz", "Cream deodorant", 3.20, 19.99, 19.99, 4.25, 15, 0.06),
    "CV-PWD": ("Curvella", "Body Powder 4oz", "Powder", 2.40, 16.99, 16.99, 4.00, 14, 0.05),
    "SF-SPR": ("SoleFresh", "Foot Odor Spray 4oz", "Spray", 2.60, 15.99, 15.99, 4.40, 16, 0.06),
    "SF-PWD": ("SoleFresh", "Foot Powder 3oz", "Powder", 2.10, 13.99, 13.99, 4.00, 6, 0.02),
    "BUNDLE-STARTER": ("Brisk & Bold", "Starter Kit (cream, powder, wipes)", "Bundle", None, 42.99, None, None, 0, 0.05),
    "BUNDLE-GIFT-CV": ("Curvella", "Gift Set (cream, balm, powder)", "Bundle", None, 44.99, None, None, 0, 0.03),
}
BUNDLES = {"BUNDLE-STARTER": ["BB-CRM-UNS", "BB-PWD-UNS", "BB-WIP-20"], "BUNDLE-GIFT-CV": ["CV-CRM-LAV", "CV-BALM", "CV-PWD"]}
AMAZON_LISTINGS = {sku: [f"{sku}-FBA"] for sku, p in PRODUCTS.items() if p[5]}
AMAZON_LISTINGS["BB-CRM-UNS"].append("BB-CRM-UNS-6OZ")   # old duplicate listing, missing from the SKU map
SUBSCRIBABLE = {"BB-CRM-UNS", "BB-CRM-CED", "BB-CRM-CIT", "BB-PWD-UNS", "BB-WIP-20", "CV-BALM",
                "CV-CRM-UNS", "CV-CRM-LAV", "CV-CRM-COC", "CV-PWD", "SF-SPR", "SF-PWD"}
REFUND_RATE = {"CV-CRM-COC": 0.14, "BB-TRV-TRIO": 0.06}
REFUND_REASONS = ["Didn't work for me", "Irritation", "Didn't like the scent", "Arrived damaged", "Arrived late"]
MONTH_SEASON = {1: .85, 2: .85, 3: .95, 4: 1.0, 5: 1.15, 6: 1.35, 7: 1.45, 8: 1.35, 9: 1.1, 10: .95, 11: 1.05, 12: 1.15}


def season(day: pd.Timestamp, sku: str | None = None) -> float:
    s = MONTH_SEASON[day.month]
    if sku and sku.startswith("BUNDLE") and day.month in (11, 12):
        s *= 2.2                                               # gifting season
    return s * (1 + 0.015 * ((day.year - 2025) * 12 + day.month - 4)) * (1.08 if day.dayofweek in (5, 6) else 0.97)


def launched(sku: str, day: pd.Timestamp) -> bool:
    return sku != "CV-CRM-COC" or day >= COCONUT_LAUNCH


def fx(day: pd.Timestamp) -> float:
    return 1.33 + 0.03 * np.sin((day.year * 12 + day.month) / 2.0)


# ---------------------------------------------------------------- marketing spend and customer cost
def marketing() -> tuple[pd.DataFrame, dict]:
    rows = []
    for d in DAYS:
        t = max(0, (d - pd.Timestamp("2026-03-01")).days) / 213
        bf = 2.0 if BLACK_FRIDAY[0] <= d <= BLACK_FRIDAY[1] else 1.0
        meta = 1900 * (0.85 + 0.25 * (season(d) / 1.2)) * bf * RNG.uniform(0.9, 1.1)
        google = 950 * (0.9 + 0.15 * season(d)) * RNG.uniform(0.9, 1.1)
        tiktok = 0 if d < pd.Timestamp("2025-10-01") else (500 if d < pd.Timestamp("2026-04-01") else 1100) * RNG.uniform(0.85, 1.15)
        rows.append({"date": d, "meta": meta, "google": google, "tiktok": tiktok,
                     "cac_meta": 38 + 26 * min(t, 1), "cac_google": 31.0,
                     "cac_tiktok": 58 - 14 * min(1, max(0, (d - pd.Timestamp("2025-10-01")).days / 270))})
    return pd.DataFrame(rows), {}


def price_for(sku: str, day: pd.Timestamp, subscription: bool) -> float:
    p = PRODUCTS[sku][4]
    if subscription:
        p = round(p * (0.85 if day < SUB_CHANGE else 0.95), 2)
    return p


def pick_sku(day: pd.Timestamp, exclude: set[str] = frozenset()) -> str:
    skus = [s for s in PRODUCTS if launched(s, day) and s not in exclude]
    w = np.array([PRODUCTS[s][8] * (2.2 if s.startswith("BUNDLE") and day.month in (11, 12) else 1) for s in skus])
    return skus[RNG.choice(len(skus), p=w / w.sum())]


# ---------------------------------------------------------------- own store (Shopify)
def shopify(spend: pd.DataFrame):
    orders, lines, subs, truth_subs = [], [], [], []
    order_no, cust_no, sub_no = 1001, 50000, 1
    end = DAYS[-1]

    def add_order(day, customer, source, sku_list, subscription, code=None, currency="USD"):
        nonlocal order_no
        ts = day + pd.Timedelta(seconds=int(RNG.integers(6 * 3600, 24 * 3600)))
        subtotal = 0.0
        oid = f"#{order_no}"
        for sku in sku_list:
            qty = 1 if subscription else int(RNG.choice([1, 2], p=[0.9, 0.1]))
            unit = price_for(sku, day, subscription)
            lines.append({"order_id": oid, "sku": sku, "quantity": qty, "price": unit, "_day": day})
            subtotal += unit * qty
        rate = {"WELCOME10": 0.10, "BF25": 0.25}.get(code, 0.0)
        discount = round(subtotal * rate, 2)
        shipping = 0.0 if subtotal - discount >= 35 or subscription else 4.99
        tax = round((subtotal - discount) * 0.07, 2)
        orders.append({"order_id": oid, "created_at": ts, "customer_id": customer, "utm_source": source,
                       "discount_code": code or "", "subtotal_price": round(subtotal, 2), "total_discounts": discount,
                       "shipping_price": shipping, "total_tax": tax, "currency": currency,
                       "is_subscription": subscription, "_day": day})
        order_no += 1

    for _, m in spend.iterrows():
        day = m["date"]
        bf = 2.5 if BLACK_FRIDAY[0] <= day <= BLACK_FRIDAY[1] else (0.8 if BLACK_FRIDAY[1] < day <= BLACK_FRIDAY[1] + pd.Timedelta(days=14) else 1.0)
        arrivals = {"organic": 25 * season(day) * bf, "meta": m["meta"] / m["cac_meta"], "google": m["google"] / m["cac_google"],
                    "tiktok": (m["tiktok"] / m["cac_tiktok"]) if m["tiktok"] else 0}
        for source, mean in arrivals.items():
            for _ in range(RNG.poisson(mean)):
                cust_no += 1
                cust = f"C{cust_no}"
                currency = "CAD" if RNG.random() < 0.03 else "USD"
                first = pick_sku(day)
                basket = [first] + ([pick_sku(day, {first})] if RNG.random() < 0.3 else [])
                in_bf = BLACK_FRIDAY[0] <= day <= BLACK_FRIDAY[1]
                code = "BF25" if in_bf and RNG.random() < 0.85 else ("WELCOME10" if RNG.random() < 0.3 else None)
                is_sub = first in SUBSCRIBABLE and not in_bf and RNG.random() < 0.22
                add_order(day, cust, source, basket, False, code, currency)
                if is_sub:
                    interval = int(RNG.choice([30, 60], p=[0.6, 0.4]))
                    start, d, cancelled = day, day, None
                    while True:
                        d = d + pd.Timedelta(days=interval)
                        if d > end:
                            break
                        months = interval / 30
                        hazard = 0.16 if SUB_CHANGE <= d < SUB_CHANGE + pd.Timedelta(days=61) else 0.065
                        if RNG.random() < 1 - (1 - hazard) ** months:
                            cancelled = d - pd.Timedelta(days=int(RNG.integers(1, 8)))   # cancel when the renewal reminder arrives
                            break
                        add_order(d, cust, "subscription", [first], True, None, currency)
                    subs.append({"subscription_id": f"S{sub_no:06d}", "customer_id": cust, "sku": first,
                                 "interval_days": interval, "created_at": start.strftime("%Y-%m-%d"),
                                 "cancelled_at": cancelled.strftime("%Y-%m-%d") if cancelled is not None else ""})
                    sub_no += 1
                else:
                    d = day
                    while RNG.random() < 0.3:
                        d = d + pd.Timedelta(days=int(RNG.exponential(70)) + 10)
                        if d > end:
                            break
                        add_order(d, cust, RNG.choice(["email", "direct", "organic"]), [pick_sku(d)], False, None, currency)
    o, l = pd.DataFrame(orders), pd.DataFrame(lines)
    return o, l, pd.DataFrame(subs)


# ---------------------------------------------------------------- Amazon
def amazon() -> tuple[pd.DataFrame, float]:
    rows, lost = [], 0.0
    n = 0
    for day in DAYS:
        prime = 2.5 if day in PRIME_DAYS else 1.0
        for sku, p in PRODUCTS.items():
            if not p[5] or not launched(sku, day):
                continue
            mean = p[7] * season(day) * prime / 1.17
            if sku == "BB-CRM-UNS" and STOCKOUT[0] <= day <= STOCKOUT[1]:
                lost += mean * 1.17 * p[5]
                continue
            if sku == "BB-CRM-UNS" and STOCKOUT[1] < day <= RECOVERY_END:
                lost += mean * 0.3 * 1.17 * p[5]
                mean *= 0.7                                    # search ranking takes weeks to recover
            for _ in range(RNG.poisson(mean)):
                qty = int(RNG.choice([1, 2, 3], p=[0.86, 0.11, 0.03]))
                listing = AMAZON_LISTINGS[sku][1] if sku == "BB-CRM-UNS" and RNG.random() < 0.2 else AMAZON_LISTINGS[sku][0]
                n += 1
                ts = day + pd.Timedelta(seconds=int(RNG.integers(0, 86400)))
                rows.append({"amazon-order-id": f"11{RNG.integers(1, 9)}-{RNG.integers(1000000, 9999999)}-{n:07d}",
                             "purchase-date": ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"), "seller-sku": listing,
                             "quantity": qty, "item-price": round(p[5] * qty, 2),
                             "item-promotion-discount": round(p[5] * qty * 0.2, 2) if day in PRIME_DAYS else 0.0,
                             "referral-fee": -round(p[5] * qty * 0.15, 2), "fba-fee": -round(p[6] * qty, 2),
                             "order-status": "Cancelled" if RNG.random() < 0.03 else "Shipped", "currency": "USD",
                             "_sku": sku, "_day": day})
    return pd.DataFrame(rows), lost


def refunds(store_lines: pd.DataFrame, store_orders: pd.DataFrame, amz: pd.DataFrame):
    disc = store_orders.set_index("order_id")
    disc_rate = (disc["total_discounts"] / disc["subtotal_price"]).fillna(0)
    sr, ar = [], []
    for r in store_lines.itertuples():
        if r.sku.startswith("BUNDLE"):
            rate = 0.03
        else:
            rate = REFUND_RATE.get(r.sku, 0.03)
        if RNG.random() < rate:
            reason = RNG.choice(["Irritation", "Didn't like the scent"]) if r.sku == "CV-CRM-COC" and RNG.random() < 0.8 else RNG.choice(REFUND_REASONS)
            when = r._5 + pd.Timedelta(days=int(RNG.integers(5, 40)))
            sr.append({"refund_id": f"R{len(sr) + 1:06d}", "order_id": r.order_id, "created_at": when.strftime("%Y-%m-%d"),
                       "sku": r.sku, "quantity": r.quantity,
                       "amount": round(r.price * r.quantity * (1 - disc_rate[r.order_id]), 2), "reason": reason})
    shipped = amz[amz["order-status"] == "Shipped"]
    for r in shipped.itertuples():
        rate = REFUND_RATE.get(r._11, 0.04)
        if RNG.random() < rate:
            reason = RNG.choice(["Irritation", "Didn't like the scent"]) if r._11 == "CV-CRM-COC" and RNG.random() < 0.8 else RNG.choice(REFUND_REASONS)
            ar.append({"order-id": r._1, "return-date": (r._12 + pd.Timedelta(days=int(RNG.integers(5, 40)))).strftime("%Y-%m-%d"),
                       "sku": r._3, "quantity": r.quantity,
                       "refund-amount-cents": int(round((r._5 - r._6) * 100)), "reason": reason})
    # A few refunds for orders placed before the data starts
    for i in range(25):
        sr.append({"refund_id": f"R{len(sr) + 1:06d}", "order_id": f"#{int(RNG.integers(400, 1000))}",
                   "created_at": "2025-04-0" + str(int(RNG.integers(2, 9))), "sku": "BB-CRM-UNS", "quantity": 1,
                   "amount": 19.99, "reason": RNG.choice(REFUND_REASONS)})
    return pd.DataFrame(sr), pd.DataFrame(ar)


def inventory(store_lines: pd.DataFrame, amz: pd.DataFrame) -> pd.DataFrame:
    weekly_store = store_lines.assign(week=store_lines["_day"].dt.to_period("W-SUN")).groupby(["week", "sku"])["quantity"].sum()
    weekly_amz = amz.assign(week=amz["_day"].dt.to_period("W-SUN")).groupby(["week", "_sku"])["quantity"].sum()
    rows = []
    for monday in pd.date_range(DAYS[0], DAYS[-1], freq="W-MON"):
        wk = monday.to_period("W-SUN") - 1   # stock reflects the last full week of sales before the count
        for sku, p in PRODUCTS.items():
            if sku.startswith("BUNDLE") or not launched(sku, monday):
                continue
            store_rate = weekly_store.get((wk, sku), 0) + sum(weekly_store.get((wk, b), 0) for b, c in BUNDLES.items() if sku in c)
            cover = RNG.uniform(38, 45) if sku == "SF-PWD" else RNG.uniform(5, 10)
            if RNG.random() > 0.03:                               # some warehouse counts are missing
                rows.append({"snapshot_date": monday.strftime("%Y-%m-%d"), "location": "Warehouse", "sku": sku,
                             "on_hand": int(max(store_rate, 5) * cover)})
            amz_rate = weekly_amz.get((wk, sku), p[7] * 7)
            fba = 0 if sku == "BB-CRM-UNS" and STOCKOUT[0] <= monday <= STOCKOUT[1] else int(max(amz_rate, 5) * RNG.uniform(3, 7))
            rows.append({"snapshot_date": monday.strftime("%Y-%m-%d"), "location": "Amazon FBA", "sku": sku, "on_hand": fba})
    return pd.DataFrame(rows)


def ad_exports(spend: pd.DataFrame, store_orders: pd.DataFrame):
    new = store_orders[store_orders["utm_source"].isin(["meta", "google", "tiktok", "organic"])]
    real = new.assign(rev=new["subtotal_price"] - new["total_discounts"]).groupby(["_day", "utm_source"])["rev"].agg(["sum", "count"])
    all_rev = store_orders.assign(rev=store_orders["subtotal_price"] - store_orders["total_discounts"]).groupby("_day")["rev"].sum()
    meta, google, tiktok, amzads = [], [], [], []
    for _, m in spend.iterrows():
        d = m["date"]

        def got(src):
            return real.loc[(d, src)] if (d, src) in real.index else pd.Series({"sum": 0.0, "count": 0})
        rm, rg, rt = got("meta"), got("google"), got("tiktok")
        # Platforms take credit for repeat and organic orders too, so their totals overlap
        for camp, share, extra in [("Prospecting - Broad", 0.7, 0.35), ("Retargeting - Site visitors", 0.3, 0.25)]:
            meta.append({"Day": d.strftime("%m/%d/%Y"), "Campaign name": camp,
                         "Amount spent (USD)": f"{m['meta'] * share:,.2f}", "Impressions": int(m["meta"] * share * RNG.uniform(70, 90)),
                         "Link clicks": int(m["meta"] * share * RNG.uniform(1.0, 1.4)),
                         "Purchases": int(rm["count"] * share * 1.6 + RNG.poisson(5)),
                         "Purchase conversion value": round(rm["sum"] * share * 1.6 + all_rev[d] * extra * share, 2)})
        for camp, share in [("Brand Search", 0.35), ("Shopping - All products", 0.65)]:
            google.append({"Date": d.strftime("%Y-%m-%d"), "Campaign": camp, "Cost (micros)": int(m["google"] * share * 1e6),
                           "Clicks": int(m["google"] * share * RNG.uniform(0.8, 1.2)),
                           "Conversions": round(rg["count"] * share * 1.3 + (8 if camp == "Brand Search" else 0), 1),
                           "Conv. value": round(rg["sum"] * share * 1.3 + (all_rev[d] * 0.12 if camp == "Brand Search" else 0), 2)})
        if m["tiktok"]:
            tiktok.append({"stat_time_day": d.strftime("%Y-%m-%d 00:00:00"), "campaign_name": "Spark Ads - UGC",
                           "spend": round(m["tiktok"], 2), "impressions": int(m["tiktok"] * RNG.uniform(150, 200)),
                           "conversions": int(rt["count"] * 1.5), "total_purchase_value": round(rt["sum"] * 1.5, 2)})
        for camp, base, acos in [("SP - Travel Trio", 450, 0.38), ("SP - Comfort Cream", 500, 0.22),
                                 ("SP - Curvella", 300, 0.25), ("SP - SoleFresh", 150, 0.30)]:
            s = base * season(d) * RNG.uniform(0.85, 1.15)
            amzads.append({"date": d.strftime("%Y-%m-%d"), "campaign": camp, "spend": round(s, 2),
                           "sales_14d": round(s / acos * RNG.uniform(0.9, 1.1), 2), "orders_14d": int(s / acos / 19)})
    return pd.DataFrame(meta), pd.DataFrame(google), pd.DataFrame(tiktok), pd.DataFrame(amzads)


def make_messy(o: pd.DataFrame, l: pd.DataFrame):
    o, l = o.copy(), l.copy()
    rates = o["_day"].map(fx)
    cad = o["currency"] == "CAD"
    for c in ["subtotal_price", "total_discounts", "shipping_price", "total_tax"]:
        o.loc[cad, c] = (o.loc[cad, c] * rates[cad]).round(2)
    l = l.merge(o[["order_id", "currency"]], on="order_id")
    l.loc[l["currency"] == "CAD", "price"] = (l.loc[l["currency"] == "CAD", "price"] * l.loc[l["currency"] == "CAD", "_day"].map(fx)).round(2)
    o["total_price"] = (o["subtotal_price"] - o["total_discounts"] + o["shipping_price"] + o["total_tax"]).round(2)
    # Timestamps: Eastern time with offset, except 10% exported in UTC
    local = o["created_at"].dt.tz_localize("America/New_York", ambiguous=False, nonexistent="shift_forward")
    utc = RNG.random(len(o)) < 0.10
    o["created_at"] = np.where(utc, local.dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                               local.dt.strftime("%Y-%m-%dT%H:%M:%S%z"))
    o["tags"] = np.where(o["is_subscription"], "Subscription Recurring Order", "")
    o["is_subscription"] = np.where(RNG.random(len(o)) < 0.5, o["is_subscription"].map({True: "TRUE", False: "FALSE"}),
                                    o["is_subscription"].map({True: "1", False: "0"}))
    # SKU typos and the old name for the best seller
    old = (l["sku"] == "BB-CRM-UNS") & (l["_day"] < SKU_RENAME)
    l.loc[old, "sku"] = "BB-CREAM-UNSC"
    p = RNG.random(len(l))
    l.loc[p < 0.03, "sku"] = l.loc[p < 0.03, "sku"].str.lower()
    l.loc[(p >= 0.03) & (p < 0.05), "sku"] = l.loc[(p >= 0.03) & (p < 0.05), "sku"] + " "
    # Test orders and webhook duplicates
    tests = pd.DataFrame({"order_id": [f"#T{i}" for i in range(35)],
                          "created_at": [f"2025-{m:02d}-15T10:00:00-0400" for m in RNG.integers(4, 13, 35)],
                          "customer_id": "C_TEST", "utm_source": "", "discount_code": "TESTING100", "subtotal_price": 19.99,
                          "total_discounts": 19.99, "shipping_price": 0.0, "total_tax": 0.0, "total_price": 0.0,
                          "currency": "USD", "is_subscription": "0", "tags": "test order"})
    test_lines = pd.DataFrame({"order_id": tests["order_id"], "sku": "BB-CRM-UNS", "quantity": 1, "price": 19.99})
    dup = o.sample(frac=0.008, random_state=3)
    o = pd.concat([o, tests, dup]).drop(columns=["_day"], errors="ignore")
    l = pd.concat([l, test_lines, l[l["order_id"].isin(dup["order_id"])]]).drop(columns=["_day", "currency"], errors="ignore")
    return o.sample(frac=1, random_state=5), l.sample(frac=1, random_state=6)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    spend, _ = marketing()
    store_orders, store_lines, subs = shopify(spend)
    amz, lost = amazon()
    s_ref, a_ref = refunds(store_lines, store_orders, amz)
    inv = inventory(store_lines, amz)
    meta, google, tiktok, amzads = ad_exports(spend, store_orders)
    o_messy, l_messy = make_messy(store_orders, store_lines)

    products = pd.DataFrame([{"sku": s, "brand": p[0], "product_name": p[1], "product_type": p[2], "unit_cost": p[3],
                              "store_price": p[4], "amazon_price": p[5],
                              "launch_date": COCONUT_LAUNCH.strftime("%Y-%m-%d") if s == "CV-CRM-COC" else "2024-01-01"}
                             for s, p in PRODUCTS.items()])
    bundle_rows = pd.DataFrame([{"bundle_sku": b, "component_sku": c, "quantity": 1} for b, cs in BUNDLES.items() for c in cs])
    sku_map = pd.DataFrame([{"seller_sku": f"{s}-FBA", "sku": s} for s in AMAZON_LISTINGS])
    fx_rates = pd.DataFrame({"month": pd.period_range(DAYS[0], DAYS[-1], freq="M").astype(str)})
    fx_rates["cad_per_usd"] = [round(fx(pd.Timestamp(m)), 4) for m in fx_rates["month"]]

    out = {"products.csv": products, "bundle_components.csv": bundle_rows, "shopify_orders.csv": o_messy,
           "shopify_order_lines.csv": l_messy, "shopify_refunds.csv": s_ref, "subscriptions.csv": subs,
           "amazon_orders.csv": amz.drop(columns=["_sku", "_day"]), "amazon_sku_map.csv": sku_map,
           "amazon_returns.csv": a_ref, "inventory_snapshots.csv": inv, "meta_ads.csv": meta, "google_ads.csv": google,
           "tiktok_ads.csv": tiktok, "amazon_ads.csv": amzads, "fx_rates.csv": fx_rates}
    for name, df in out.items():
        df.to_csv(RAW / name, index=False)

    truth = {"note": "What the generator built in, for checking the pipeline. Not used by the analysis.",
             "amazon_stockout_sku": "BB-CRM-UNS", "amazon_stockout_window": [str(STOCKOUT[0].date()), str(STOCKOUT[1].date())],
             "ranking_recovery_until": str(RECOVERY_END.date()), "amazon_lost_revenue_usd": round(lost),
             "high_refund_sku": "CV-CRM-COC", "high_refund_rate": REFUND_RATE["CV-CRM-COC"], "normal_refund_rate": 0.03,
             "subscription_discount_change": str(SUB_CHANGE.date()), "subscription_discount": "15% before, 5% after",
             "monthly_cancel_rate": "6.5% normally, 16% for two months after the change",
             "meta_cost_per_new_customer": "38 until Feb 2026, rising to 64 by Sep 2026",
             "google_cost_per_new_customer": 31, "money_losing_amazon_sku": "BB-TRV-TRIO",
             "overstocked_sku": "SF-PWD (about 40 weeks of warehouse stock)",
             "old_amazon_listing_missing_from_map": "BB-CRM-UNS-6OZ", "renamed_store_sku": "BB-CREAM-UNSC -> BB-CRM-UNS"}
    (RAW / "_answer_key.json").write_text(json.dumps(truth, indent=2))
    print(f"store orders {len(o_messy):,} | store lines {len(l_messy):,} | subscriptions {len(subs):,} | "
          f"amazon orders {len(amz):,} | refunds {len(s_ref):,} + {len(a_ref):,} | inventory rows {len(inv):,}")


if __name__ == "__main__":
    main()
