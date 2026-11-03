import os
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def generate_user_tenant_mapping():
    gold_dir = Path("./data/gold/analytics")
    gold_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Generating tenant-to-user security mapping table...")

    # Define user-to-tenant access control list (ACL)
    mapping_data = [
        {
            "user_email": "admin@acme.com",
            "tenant_id": "TENANT-001",
            "access_role": "TenantAdmin",
            "tenant_name": "Acme Corp"
        },
        {
            "user_email": "finance@acme.com",
            "tenant_id": "TENANT-001",
            "access_role": "Analyst",
            "tenant_name": "Acme Corp"
        },
        {
            "user_email": "admin@globex.com",
            "tenant_id": "TENANT-002",
            "access_role": "TenantAdmin",
            "tenant_name": "Globex Corp"
        },
        {
            "user_email": "support@globex.com",
            "tenant_id": "TENANT-002",
            "access_role": "SupportAgent",
            "tenant_name": "Globex Corp"
        }
    ]

    df_mapping = pd.DataFrame(mapping_data)
    
    mapping_output_path = gold_dir / "dim_user_tenants.parquet"
    df_mapping.to_parquet(mapping_output_path, index=False)
    
    logging.info(f"Successfully saved security mapping table to: {mapping_output_path}")
    print("\n--- Gold Tier Security Mapping Table (`dim_user_tenants`) ---")
    print(df_mapping.to_string(index=False))

if __name__ == "__main__":
    generate_user_tenant_mapping()
