import os
import json
from pathlib import Path
import pandas as pd
import pytest

def test_bronze_layer_exists():
    """Verify that the bronze ingestion payload was generated."""
    bronze_file = Path("./data/bronze/invoices/raw_invoices_batch_01.json")
    assert bronze_file.exists(), "Bronze raw JSON file is missing."
    
    with open(bronze_file, "r") as f:
        data = json.load(f)
    assert "Invoices" in data, "Bronze payload does not contain 'Invoices' root key."
    assert len(data["Invoices"]) > 0, "Bronze invoices list is empty."

def test_silver_layer_transformations():
    """Verify Silver Parquet schema, data types, and row uniqueness."""
    silver_file = Path("./data/silver/invoices/dim_invoices.parquet")
    assert silver_file.exists(), "Silver parquet file is missing."
    
    df = pd.read_parquet(silver_file)
    
    # Check mandatory columns
    expected_columns = {"invoice_id", "contact_id", "invoice_date", "due_date", "total_amount", "status"}
    assert expected_columns.issubset(df.columns), f"Missing columns in Silver table. Found: {df.columns.tolist()}"
    
    # Check for null primary keys
    assert df["invoice_id"].isnull().sum() == 0, "Found null invoice IDs in Silver table."
    
    # Check deduplication integrity
    assert df["invoice_id"].is_unique, "Duplicate invoice IDs detected in Silver table."
    
    # Check data types
    assert pd.api.types.is_float_dtype(df["total_amount"]), "total_amount is not stored as a float type."

def test_gold_layer_aggregations():
    """Verify Gold fact table calculations and metrics."""
    cust_summary_file = Path("./data/gold/analytics/fact_customer_summary.parquet")
    monthly_revenue_file = Path("./data/gold/analytics/fact_monthly_revenue.parquet")
    
    assert cust_summary_file.exists(), "Customer summary Gold table is missing."
    assert monthly_revenue_file.exists(), "Monthly revenue Gold table is missing."
    
    df_cust = pd.read_parquet(cust_summary_file)
    assert "total_invoiced_amount" in df_cust.columns
    assert (df_cust["total_invoiced_amount"] >= 0).all(), "Negative revenue detected in customer summary."

    df_monthly = pd.read_parquet(monthly_revenue_file)
    assert "revenue" in df_monthly.columns
    assert (df_monthly["revenue"] >= 0).all(), "Negative revenue detected in monthly summary."
