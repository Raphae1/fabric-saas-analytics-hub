import os
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def build_gold_aggregations():
    silver_path = Path("./data/silver/invoices/dim_invoices.parquet")
    gold_dir = Path("./data/gold/analytics")
    gold_dir.mkdir(parents=True, exist_ok=True)

    if not silver_path.exists():
        logging.error(f"Silver table not found at {silver_path}. Run transform.py first.")
        return

    logging.info(f"Reading Silver table from: {silver_path}")
    df = pd.read_parquet(silver_path)

    if df.empty:
        logging.warning("Silver table is empty. No data to aggregate.")
        return

    # Aggregate 1: Customer Invoice Summary (Total spend & invoice count per customer)
    logging.info("Computing customer-level financial aggregations...")
    customer_summary = df.groupby("contact_id").agg(
        total_invoiced_amount=("total_amount", "sum"),
        invoice_count=("invoice_id", "count"),
        average_invoice_value=("total_amount", "mean")
    ).reset_index()

    # Aggregate 2: Monthly Financial Status Breakdown
    logging.info("Computing monthly status revenue breakdown...")
    df["invoice_month"] = df["invoice_date"].dt.to_period("M").astype(str)
    monthly_summary = df.groupby(["invoice_month", "status"]).agg(
        revenue=("total_amount", "sum"),
        transaction_count=("invoice_id", "count")
    ).reset_index()

    # Save Gold tables as Parquet for reporting and analytics consumption
    cust_output = gold_dir / "fact_customer_summary.parquet"
    monthly_output = gold_dir / "fact_monthly_revenue.parquet"

    customer_summary.to_parquet(cust_output, index=False)
    monthly_summary.to_parquet(monthly_output, index=False)

    logging.info(f"Gold tables successfully published to: {gold_dir}")
    
    print("\n--- Gold Tier: Customer Summary ---")
    print(customer_summary.to_string(index=False))
    
    print("\n--- Gold Tier: Monthly Revenue Summary ---")
    print(monthly_summary.to_string(index=False))

if __name__ == "__main__":
    build_gold_aggregations()
