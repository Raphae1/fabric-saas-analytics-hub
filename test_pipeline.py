import os
import json
from pathlib import Path
import pandas as pd
import pytest

def test_bronze_multi_tenant_isolation():
    """Verify that raw JSON payloads are correctly isolated by tenant directory."""
    for tenant_id in ["TENANT-001", "TENANT-002"]:
        bronze_file = Path(f"./data/bronze/tenant_id={tenant_id}/invoices/raw_invoices_batch_01.json")
        assert bronze_file.exists(), f"Bronze raw JSON file missing for {tenant_id}."
        
        with open(bronze_file, "r") as f:
            data = json.load(f)
        assert data.get("TenantID") == tenant_id, f"Payload tenant ID mismatch for {tenant_id}."
        assert "Invoices" in data, f"Missing 'Invoices' key in Bronze payload for {tenant_id}."

def test_silver_multi_tenant_transformations():
    """Verify Silver Parquet dataset contains tenant_id and isolates records correctly."""
    silver_file = Path("./data/silver/invoices/dim_invoices.parquet")
    assert silver_file.exists(), "Silver parquet dataset is missing."
    
    df = pd.read_parquet(silver_file)
    expected_columns = {"tenant_id", "invoice_id", "contact_id", "invoice_date", "due_date", "total_amount", "status"}
    assert expected_columns.issubset(df.columns), f"Missing columns in Silver table. Found: {df.columns.tolist()}"
    
    assert df["invoice_id"].isnull().sum() == 0, "Found null invoice IDs in Silver table."
    assert df["tenant_id"].isnull().sum() == 0, "Found null tenant IDs in Silver table."
    assert df.duplicated(subset=["tenant_id", "invoice_id"]).sum() == 0, "Duplicate tenant-invoice IDs detected."
    
    unique_tenants = df["tenant_id"].unique()
    assert "TENANT-001" in unique_tenants, "TENANT-001 missing from Silver dataset."
    assert "TENANT-002" in unique_tenants, "TENANT-002 missing from Silver dataset."

def test_gold_multi_tenant_aggregations():
    """Verify Gold fact tables preserve tenant boundaries and metrics."""
    cust_summary_file = Path("./data/gold/analytics/fact_customer_summary.parquet")
    monthly_revenue_file = Path("./data/gold/analytics/fact_monthly_revenue.parquet")
    
    assert cust_summary_file.exists(), "Customer summary Gold table is missing."
    assert monthly_revenue_file.exists(), "Monthly revenue Gold table is missing."
    
    df_cust = pd.read_parquet(cust_summary_file)
    assert "tenant_id" in df_cust.columns, "tenant_id missing from customer summary."
    assert (df_cust["total_invoiced_amount"] >= 0).all(), "Negative revenue detected in customer summary."

    df_monthly = pd.read_parquet(monthly_revenue_file)
    assert "tenant_id" in df_monthly.columns, "tenant_id missing from monthly revenue summary."
    assert (df_monthly["revenue"] >= 0).all(), "Negative revenue detected in monthly summary."

def test_gold_security_mapping():
    """Verify RLS security mapping table exists and maps users correctly to tenants."""
    mapping_file = Path("./data/gold/analytics/dim_user_tenants.parquet")
    assert mapping_file.exists(), "Security mapping table dim_user_tenants.parquet is missing."
    
    df_mapping = pd.read_parquet(mapping_file)
    expected_columns = {"user_email", "tenant_id", "access_role", "tenant_name"}
    assert expected_columns.issubset(df_mapping.columns), f"Missing columns in security mapping. Found: {df_mapping.columns.tolist()}"
    
    # Ensure no nulls in security mapping
    assert df_mapping["user_email"].isnull().sum() == 0, "Null user emails found in security mapping."
    assert df_mapping["tenant_id"].isnull().sum() == 0, "Null tenant IDs found in security mapping."
    
    # Ensure our target test tenants are covered
    mapped_tenants = df_mapping["tenant_id"].unique()
    assert "TENANT-001" in mapped_tenants, "TENANT-001 missing from security mapping table."
    assert "TENANT-002" in mapped_tenants, "TENANT-002 missing from security mapping table."
