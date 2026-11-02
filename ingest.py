import os
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def load_config():
    config_path = Path("config.json")
    if not config_path.exists():
        logging.error("config.json not found. Please create configuration boundary.")
        return None
    with open(config_path, "r") as f:
        return json.load(f)

def generate_mock_tenant_payload(tenant_id):
    """Generates mock raw invoice data scoped strictly to the authorized tenant."""
    if tenant_id == "TENANT-001":
        return {
            "TenantID": tenant_id,
            "IngestionTimestamp": datetime.utcnow().isoformat() + "Z",
            "Invoices": [
                {
                    "InvoiceID": "INV-1001",
                    "Contact": {"ContactID": "CUST-101", "Name": "Alpha LLC"},
                    "Date": "2026-11-01",
                    "DueDate": "2026-12-01",
                    "Total": 1250.0,
                    "Status": "AUTHORISED"
                }
            ]
        }
    elif tenant_id == "TENANT-002":
        return {
            "TenantID": tenant_id,
            "IngestionTimestamp": datetime.utcnow().isoformat() + "Z",
            "Invoices": [
                {
                    "InvoiceID": "INV-2001",
                    "Contact": {"ContactID": "CUST-201", "Name": "Beta Corp"},
                    "Date": "2026-11-02",
                    "DueDate": "2026-12-02",
                    "Total": 4800.0,
                    "Status": "PAID"
                },
                {
                    "InvoiceID": "INV-2002",
                    "Contact": {"ContactID": "CUST-202", "Name": "Gamma Inc"},
                    "Date": "2026-11-03",
                    "DueDate": "2026-12-03",
                    "Total": 1550.25,
                    "Status": "AUTHORISED"
                }
            ]
        }
    return {"TenantID": tenant_id, "Invoices": []}

def ingest_bronze_layer():
    config = load_config()
    if not config:
        return

    authorized_tenants = config.get("authorized_tenants", [])
    if not authorized_tenants:
        logging.warning("No authorized tenants found in configuration.")
        return

    logging.info(f"Starting multi-tenant Bronze ingestion for {len(authorized_tenants)} tenants...")

    for tenant in authorized_tenants:
        tenant_id = tenant["tenant_id"]
        
        # Bronze isolation: Store raw records in tenant-specific directories
        bronze_dir = Path(f"./data/bronze/tenant_id={tenant_id}/invoices")
        bronze_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"Fetching authenticated payload for verified tenant: {tenant_id} ({tenant['tenant_name']})")
        
        # Simulating secure ingestion governed by trusted config identity rather than untrusted client payloads
        payload = generate_mock_tenant_payload(tenant_id)

        raw_file_path = bronze_dir / "raw_invoices_batch_01.json"
        with open(raw_file_path, "w") as f:
            json.dump(payload, f, indent=4)

        logging.info(f"Successfully landed raw payload for {tenant_id} at: {raw_file_path}")

    logging.info("Multi-tenant Bronze ingestion completed successfully.")

if __name__ == "__main__":
    ingest_bronze_layer()
