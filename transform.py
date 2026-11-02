import os
import json
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def transform_bronze_to_silver():
    bronze_dir = Path("./data/bronze/invoices")
    silver_dir = Path("./data/silver/invoices")
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    raw_file = bronze_dir / "raw_invoices_batch_01.json"
    if not raw_file.exists():
        logging.error(f"Bronze raw file not found at {raw_file}. Run ingest.py first.")
        return

    logging.info(f"Reading raw Bronze payload from: {raw_file}")
    with open(raw_file, "r") as f:
        raw_data = json.load(f)

    invoices = raw_data.get("Invoices", [])
    if not invoices:
        logging.warning("No invoice records found in Bronze payload.")
        return

    # Flatten and clean data into a Pandas DataFrame (simulating PySpark DataFrame transformations)
    logging.info("Transforming and flattening records for Silver layer...")
    cleaned_rows = []
    for inv in invoices:
        contact = inv.get("Contact", {})
        cleaned_rows.append({
            "invoice_id": inv.get("InvoiceID"),
            "contact_id": contact.get("ContactID"),
            "invoice_date": pd.to_datetime(inv.get("Date")),
            "due_date": pd.to_datetime(inv.get("DueDate")),
            "total_amount": float(inv.get("Total", 0.0)),
            "status": str(inv.get("Status")).upper().strip()
        })

    df = pd.DataFrame(cleaned_rows)

    # Data Quality & Deduplication
    initial_count = len(df)
    df = df.drop_duplicates(subset=["invoice_id"])
    logging.info(f"Deduplication check: {initial_count} rows processed, {len(df)} unique records retained.")

    # Save structured output into Silver layer (Parquet format preferred for analytics lakes)
    silver_output_path = silver_dir / "dim_invoices.parquet"
    df.to_parquet(silver_output_path, index=False)
    
    logging.info(f"Successfully wrote transformed Silver table to: {silver_output_path}")
    print("\n--- Silver Table Preview ---")
    print(df.to_string(index=False))

if __name__ == "__main__":
    transform_bronze_to_silver()
