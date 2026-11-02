import os
import json
import logging
import shutil
from pathlib import Path
from datetime import timezone
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def transform_bronze_to_silver():
    bronze_base = Path("./data/bronze")
    silver_dir = Path("./data/silver/invoices")
    silver_output_path = silver_dir / "dim_invoices.parquet"

    # Clean up old single-file parquet or directory if it exists to prevent PyArrow conflicts
    if silver_output_path.exists():
        if silver_output_path.is_file():
            logging.info(f"Removing legacy single-file Parquet at {silver_output_path}")
            silver_output_path.unlink()
        elif silver_output_path.is_dir():
            shutil.rmtree(silver_output_path)

    silver_dir.mkdir(parents=True, exist_ok=True)

    if not bronze_base.exists():
        logging.error(f"Bronze base directory not found at {bronze_base}. Run ingest.py first.")
        return

    # Discover all tenant partitions in the Bronze layer
    tenant_dirs = [d for d in bronze_base.iterdir() if d.is_dir() and d.name.startswith("tenant_id=")]
    if not tenant_dirs:
        logging.warning("No tenant partitions found in Bronze layer.")
        return

    logging.info(f"Processing Silver transformations across {len(tenant_dirs)} tenant partitions...")
    all_tenant_rows = []

    for tenant_dir in tenant_dirs:
        tenant_id = tenant_dir.name.split("=")[1]
        raw_file = tenant_dir / "invoices" / "raw_invoices_batch_01.json"

        if not raw_file.exists():
            logging.warning(f"Raw payload missing for tenant {tenant_id} at {raw_file}")
            continue

        logging.info(f"Reading raw Bronze payload for tenant: {tenant_id}")
        with open(raw_file, "r") as f:
            raw_data = json.load(f)

        # Verify tenant boundary integrity: ensure payload tenant matches directory partition
        payload_tenant = raw_data.get("TenantID")
        if payload_tenant != tenant_id:
            logging.error(f"Security Warning: Payload tenant ID '{payload_tenant}' does not match directory partition '{tenant_id}'! Dropping payload.")
            continue

        invoices = raw_data.get("Invoices", [])
        for inv in invoices:
            contact = inv.get("Contact", {})
            all_tenant_rows.append({
                "tenant_id": tenant_id,
                "invoice_id": inv.get("InvoiceID"),
                "contact_id": contact.get("ContactID"),
                "invoice_date": pd.to_datetime(inv.get("Date")),
                "due_date": pd.to_datetime(inv.get("DueDate")),
                "total_amount": float(inv.get("Total", 0.0)),
                "status": str(inv.get("Status")).upper().strip()
            })

    if not all_tenant_rows:
        logging.warning("No valid tenant records found to transform.")
        return

    df = pd.DataFrame(all_tenant_rows)

    # Data Quality & Tenant-Scoped Deduplication
    initial_count = len(df)
    df = df.drop_duplicates(subset=["tenant_id", "invoice_id"])
    logging.info(f"Tenant-scoped deduplication check: {initial_count} rows processed, {len(df)} unique records retained.")

    # Save structured output into Silver layer partitioned by tenant_id
    df.to_parquet(silver_output_path, partition_cols=["tenant_id"], index=False)
    
    logging.info(f"Successfully wrote partitioned Silver dataset to: {silver_output_path}")
    print("\n--- Multi-Tenant Silver Table Preview ---")
    print(df.to_string(index=False))

if __name__ == "__main__":
    transform_bronze_to_silver()
