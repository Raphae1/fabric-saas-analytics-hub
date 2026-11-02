import os
import logging
import shutil
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def build_gold_aggregations():
    silver_file = Path("./data/silver/invoices/dim_invoices.parquet")
    gold_dir = Path("./data/gold/analytics")

    if not silver_file.exists():
        logging.error(f"Silver dataset not found at {silver_file}. Run transform.py first.")
        return

    logging.info("Reading Silver dataset for multi-tenant Gold aggregations...")
    df = pd.read_parquet(silver_file)

    if "tenant_id" not in df.columns:
        logging.error("Security Error: 'tenant_id' column missing from Silver dataset!")
        return

    gold_dir.mkdir(parents=True, exist_ok=True)

    # 1. Tenant-Scoped Customer Summary (Fact Customer Summary)
    logging.info("Calculating tenant-scoped customer summaries...")
    df_cust = df.groupby(["tenant_id", "contact_id"]).agg(
        total_invoiced_amount=("total_amount", "sum"),
        invoice_count=("invoice_id", "count"),
        average_invoice_value=("total_amount", "mean")
    ).reset_index()

    cust_summary_path = gold_dir / "fact_customer_summary.parquet"
    df_cust.to_parquet(cust_summary_path, index=False)
    logging.info(f"Successfully saved tenant-scoped customer summary to: {cust_summary_path}")

    # 2. Tenant-Scoped Monthly Revenue Summary (Fact Monthly Revenue)
    logging.info("Calculating tenant-scoped monthly revenue summaries...")
    df["invoice_month"] = df["invoice_date"].dt.to_period("M").astype(str)
    
    df_monthly = df.groupby(["tenant_id", "invoice_month", "status"]).agg(
        revenue=("total_amount", "sum"),
        transaction_count=("invoice_id", "count")
    ).reset_index()

    monthly_revenue_path = gold_dir / "fact_monthly_revenue.parquet"
    df_monthly.to_parquet(monthly_revenue_path, index=False)
    logging.info(f"Successfully saved tenant-scoped monthly revenue summary to: {monthly_revenue_path}")

    print("\n--- Multi-Tenant Gold Tier: Customer Summary ---")
    print(df_cust.to_string(index=False))

    print("\n--- Multi-Tenant Gold Tier: Monthly Revenue Summary ---")
    print(df_monthly.to_string(index=False))

if __name__ == "__main__":
    build_gold_aggregations()
