"""
Headline findings and README charts, built from the dbt marts. Run after run_pipeline.py:

    python analysis.py

Writes reports/findings.md and the charts in docs/.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
DOCS, REPORTS = ROOT / "docs", ROOT / "reports"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
MUTED, GRID, INK, INK2, SURFACE = "#898781", "#ebeae6", "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.spines.left": False, "font.size": 10,
                     "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left", "lines.linewidth": 2})
STOCKOUT = (pd.Timestamp("2026-07-06"), pd.Timestamp("2026-07-26"))
RECOVERY_END = pd.Timestamp("2026-08-09")


def finish(fig, ax, name, subtitle):
    ax.set_title(ax.get_title(loc="left"), loc="left", pad=26)
    ax.text(0, 1.025, subtitle, transform=ax.transAxes, color=INK2, fontsize=9.5, va="bottom")
    fig.tight_layout()
    fig.savefig(DOCS / name, dpi=150)
    plt.close(fig)


def money(x: float) -> str:
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "warehouse.duckdb"), read_only=True)
    q = lambda sql: con.sql(sql).df()
    out: list[str] = ["# Findings", ""]

    # 1. Contribution margin by channel and the Amazon products that lose money
    ch = q("select channel, sum(net_revenue) nr, sum(cm1) cm1, sum(cm2) cm2, sum(marketing) mk, sum(cm3) cm3 "
           "from main.fct_contribution_margin group by 1").set_index("channel")
    out += ["## Contribution margin by channel", "", "| Channel | Net revenue | CM1 | CM2 | Advertising | CM3 | CM3 % |", "|---|---|---|---|---|---|---|"]
    for c, r in ch.iterrows():
        out.append(f"| {c} | {money(r.nr)} | {money(r.cm1)} | {money(r.cm2)} | {money(r.mk)} | {money(r.cm3)} | {r.cm3 / r.nr:.0%} |")
    sku = q("select sku, product_name, sum(units) units, sum(net_revenue) nr, sum(cm2) cm2, sum(marketing) mk, sum(cm3) cm3 "
            "from main.fct_contribution_margin where channel = 'Amazon' group by all order by cm3")
    units_rank = sku.sort_values("units", ascending=False).reset_index(drop=True)
    trio = sku.set_index("sku").loc["BB-TRV-TRIO"]
    out += ["", f"Travel Trio on Amazon: number {units_rank.index[units_rank['sku'] == 'BB-TRV-TRIO'][0] + 1} by units "
            f"({trio.units:,.0f}), CM2 {money(trio.cm2)}, advertising {money(trio.mk)}, CM3 {money(trio.cm3)}.", ""]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    s = sku.sort_values("cm3")
    colors = [ORANGE if v < 0 else BLUE for v in s["cm3"]]
    ax.barh(s["product_name"], s["cm3"], color=colors)
    for y, v in enumerate(s["cm3"]):
        ax.text(v + (6000 if v >= 0 else -6000), y, money(v), va="center", ha="left" if v >= 0 else "right", fontsize=8.5)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: money(v)))
    ax.set_xlim(s["cm3"].min() * 1.45, s["cm3"].max() * 1.25)
    ax.set_title("Amazon profit after advertising (CM3) by product")
    finish(fig, ax, "amazon_cm3_by_product.png", "April 2025 to September 2026. The Travel Trio sells well but loses money once ads are counted.")

    # 2. Customer value vs acquisition cost
    ltv = q("select * from main.fct_customer_ltv")
    all_c = ltv[ltv.dimension == "All customers"].iloc[0]
    subs = q("select ever_subscribed, avg(cm2_first_12m) v from main.fct_customers "
             "where first_order_date <= date '2025-09-30' group by 1").set_index("ever_subscribed")["v"]
    mk = q("select month, platform, spend, new_customers, cac from main.fct_marketing_monthly "
           "where platform in ('Meta', 'Google', 'TikTok') order by month")
    cac_q = q("select date_trunc('quarter', month)::date q, platform, sum(spend) / sum(new_customers) cac "
              "from main.fct_marketing_monthly where platform in ('Meta', 'Google', 'TikTok') group by all order by q, platform")
    meta = cac_q[cac_q.platform == "Meta"].set_index("q")["cac"]
    google = cac_q[cac_q.platform == "Google"].set_index("q")["cac"]
    out += ["## Customer value vs acquisition cost", "",
            f"Average store customer value (CM2, before advertising): {money(all_c.ltv_3m)} in 3 months, "
            f"{money(all_c.ltv_6m)} in 6 months, {money(all_c.ltv_12m)} in 12 months.",
            f"Customers who ever subscribed: {money(subs[True])} in 12 months, against {money(subs[False])} for those who never did.",
            f"Meta CAC: {money(meta.iloc[0])} in the first quarter, {money(meta.iloc[-1])} in the last. "
            f"Google CAC: {money(google.iloc[0])} to {money(google.iloc[-1])}.",
            f"12-month repeat rate: {all_c.repeat_rate_12m:.0%}.", ""]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    for p, col in [("Meta", BLUE), ("Google", AQUA), ("TikTok", ORANGE)]:
        d = mk[mk.platform == p]
        ax.plot(d["month"], d["cac"], color=col)
        ax.text(d["month"].iloc[-1] + pd.Timedelta(days=10), d["cac"].iloc[-1], f"{p}: {money(d['cac'].iloc[-1])}", va="center", fontsize=9)
    ax.axhline(all_c.ltv_12m, color=MUTED, linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(mk["month"].min(), all_c.ltv_12m + 1.2, f"What a customer earns back in 12 months: {money(all_c.ltv_12m)}", color=INK2, fontsize=8.5)
    ax.set_ylim(0, mk["cac"].max() * 1.15)
    ax.set_xlim(mk["month"].min(), mk["month"].max() + pd.Timedelta(days=95))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_title("Cost to acquire a store customer vs what they are worth")
    finish(fig, ax, "cac_vs_customer_value.png", "Monthly CAC by channel. Above the dashed line, a new customer does not pay back within a year.")

    # 3. Subscription churn after the discount cut
    ch_m = q("select month, churn_rate, cancelled, active_at_start from main.fct_subscriptions_monthly where month >= date '2025-06-01' order by month")
    before = ch_m[(ch_m.month >= pd.Timestamp("2025-09-01")) & (ch_m.month < pd.Timestamp("2026-03-01"))]
    out += ["## Subscriptions", "",
            f"Monthly churn averaged {before.churn_rate.mean():.1%} from September 2025 to February 2026, then "
            f"{ch_m.set_index('month').loc[pd.Timestamp('2026-03-01'), 'churn_rate']:.1%} in March and "
            f"{ch_m.set_index('month').loc[pd.Timestamp('2026-04-01'), 'churn_rate']:.1%} in April 2026, after the subscription discount was cut from 15% to 5%.", ""]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(ch_m["month"], ch_m["churn_rate"], color=BLUE, marker="o", markersize=4)
    ax.axvline(pd.Timestamp("2026-03-01"), color=MUTED, linestyle=(0, (3, 3)), linewidth=1)
    ax.text(pd.Timestamp("2026-03-08"), ch_m["churn_rate"].max() * 0.98, "Subscription discount\ncut from 15% to 5%", fontsize=8.5, color=INK2, va="top")
    ax.set_ylim(0, ch_m["churn_rate"].max() * 1.2)
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.04))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_title("Monthly subscription churn")
    finish(fig, ax, "subscription_churn.png", "Share of subscriptions active at the start of each month that cancelled during it.")

    # 4. Amazon stock-out: lost sales estimate
    d = q("select order_date, sum(units) units from main.fct_daily_sales where channel = 'Amazon' and sku = 'BB-CRM-UNS' group by 1 order by 1")
    d["order_date"] = pd.to_datetime(d["order_date"])
    d = d.set_index("order_date").reindex(pd.date_range("2025-04-01", "2026-09-30"), fill_value=0)["units"]
    # Expected sales: the same weeks last year, scaled by this year's growth before the stock-out (keeps the July peak and Prime Day)
    growth = d["2026-06-08":"2026-07-05"].sum() / d["2025-06-08":"2025-07-05"].sum()
    window = pd.date_range(STOCKOUT[0], RECOVERY_END)
    expected = d.reindex(window - pd.DateOffset(days=364)).values * growth
    lost_units = expected.sum() - d.reindex(window).sum()
    lost_revenue = lost_units * 19.99
    truth = json.loads((ROOT / "data" / "raw" / "_answer_key.json").read_text())["amazon_lost_revenue_usd"]
    out += ["## Amazon stock-out", "",
            f"The best seller sold {int(d[STOCKOUT[0]:STOCKOUT[1]].sum())} units on Amazon from 6 to 26 July 2026, over Prime Day. "
            f"Against the same weeks last year adjusted for growth, about {lost_units:,.0f} units and {money(lost_revenue)} of revenue were lost "
            f"by 9 August, including two weeks of slower sales while the listing recovered. "
            f"(The generator's answer key says {money(truth)}; this estimate is checked against it, never fed from it.)", ""]
    weekly = d.resample("W-SUN").sum().loc["2026-05-03":"2026-09-27"]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.axvspan(STOCKOUT[0], STOCKOUT[1], color=ORANGE, alpha=0.12, linewidth=0)
    ax.axvspan(STOCKOUT[1], RECOVERY_END, color=ORANGE, alpha=0.05, linewidth=0)
    ax.plot(weekly.index, weekly.values, color=BLUE, marker="o", markersize=4)
    ax.text(STOCKOUT[0] + pd.Timedelta(days=1), weekly.max() * 0.95, "Out of stock\nat Amazon", fontsize=8.5, color=INK2, va="top")
    ax.set_ylim(0, weekly.max() * 1.15)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_title("Comfort Cream Unscented: weekly units sold on Amazon")
    finish(fig, ax, "amazon_stockout.png", f"Summer 2026. Estimated lost revenue: {money(lost_revenue)}.")

    # 5. Other findings
    ref = q("with s as (select sku, sum(quantity) u from main.int_order_lines group by 1), "
            "r as (select sku, sum(quantity) ru from main.int_refunds group by 1) "
            "select sku, ru * 1.0 / u rate from s join r using (sku) order by rate desc")
    coc = q("select reason, count(*) n from main.int_refunds where sku = 'CV-CRM-COC' group by 1 order by n desc")
    rec = q("select sum(store_net_sales) actual, sum(total_claimed) claimed from main.fct_revenue_reconciliation").iloc[0]
    inv = q("select location, sku, product_name, weeks_of_cover, stock_value_at_cost from main.fct_inventory_cover order by weeks_of_cover desc")
    med = inv[(inv.location == "Warehouse")].weeks_of_cover.median()
    tac = q("select sum(spend) / sum(amazon_net_sales) tacos, sum(spend) / sum(claimed_revenue) acos from main.fct_marketing_monthly where platform = 'Amazon Ads'").iloc[0]
    seg = q("select segment, count(*) n, sum(lifetime_cm2) cm2 from main.fct_customers group by 1 order by cm2 desc")
    seg["share_customers"] = seg.n / seg.n.sum()
    seg["share_value"] = seg.cm2 / seg.cm2.sum()
    out += ["## Refunds", "",
            f"Coconut cream refund rate: {ref.set_index('sku').loc['CV-CRM-COC', 'rate']:.1%} of units, against a median of {ref.rate.median():.1%} across products. "
            f"Top reasons: " + ", ".join(f"{r.reason} ({r.n})" for r in coc.head(2).itertuples()) + ".", "",
            "## Platform claims", "",
            f"Meta, Google and TikTok together claimed {money(rec.claimed)} of store revenue against {money(rec.actual)} actually recorded "
            f"({rec.claimed / rec.actual - 1:.0%} more than reality).", "",
            "## Amazon advertising", "", f"TACoS {tac.tacos:.0%}; ACoS {tac.acos:.0%}.", "",
            "## Stock", "",
            f"{inv.iloc[0].product_name} has {inv.iloc[0].weeks_of_cover:.0f} weeks of warehouse stock; the median product has {med:.0f}.", "",
            "## Customer segments", "", "| Segment | Customers | Share of customers | Share of lifetime CM2 |", "|---|---|---|---|"]
    for r in seg.itertuples():
        out.append(f"| {r.segment} | {r.n:,} | {r.share_customers:.0%} | {r.share_value:.0%} |")
    (REPORTS / "findings.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
