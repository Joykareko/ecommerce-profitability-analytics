"""
Run the whole pipeline with one command:

    python run_pipeline.py

1. Loads the seeds (documented decisions and cost assumptions).
2. Builds every dbt model and runs every test. If any test fails, it stops here,
   so no report is built on broken data.
3. Exports the marts to data/processed/ as CSV files for Power BI.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DBT = ROOT / "dbt"
OUT = ROOT / "data" / "processed"
MARTS = ["fct_contribution_margin", "fct_marketing_monthly", "fct_revenue_reconciliation",
         "fct_subscriptions_monthly", "fct_inventory_cover", "fct_daily_sales", "fct_customers", "fct_customer_ltv", "meta_cleaning_log"]


def dbt(*args: str) -> None:
    result = subprocess.run(["dbt", *args, "--profiles-dir", "."], cwd=DBT)
    if result.returncode != 0:
        sys.exit(f"Stopped: 'dbt {' '.join(args)}' failed. Fix the errors or failing tests above first.")


def main() -> None:
    print("1/3 Loading seeds")
    dbt("seed")
    print("2/3 Building models and running tests")
    dbt("build", "--exclude", "resource_type:seed")
    print("3/3 Exporting marts for Power BI")
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "warehouse.duckdb"), read_only=True)
    for name in MARTS:
        con.sql(f"select * from main.{name}").df().to_csv(OUT / f"{name}.csv", index=False)
        print(f"     {name}.csv")
    print("Done. Outputs in data/processed")


if __name__ == "__main__":
    main()
