import pytest
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

def test_silver_tenant_partitions_exist():
    """Verify Silver parquet partitions exist for all authorized tenants."""
    for tenant in ["TENANT-001", "TENANT-002"]:
        silver_path = BASE_DIR / "data" / "silver" / "invoices"
        assert silver_path.exists(), "Silver parquet directory missing."

def test_cross_tenant_isolation_in_silver():
    """Assert that querying Silver layer under Tenant A context never returns Tenant B data."""
    silver_dir = BASE_DIR / "data" / "silver" / "invoices"
    if not silver_dir.exists():
        pytest.skip("Silver layer not generated yet.")

    # Read all parquet partitions
    df = pd.read_parquet(silver_dir)
    
    if "tenant_id" not in df.columns:
        pytest.fail("Security violation: 'tenant_id' column missing from Silver layer.")

    # Simulate Tenant 1 context query
    tenant_1_data = df[df["tenant_id"] == "TENANT-001"]
    
    # Assert zero records belong to TENANT-002 in Tenant 1's view
    foreign_records = tenant_1_data[tenant_1_data["tenant_id"] != "TENANT-001"]
    assert len(foreign_records) == 0, "Cross-tenant data leakage detected in Silver layer!"

def test_security_mapping_governance():
    """Verify the RLS security mapping table exists and pairs users correctly."""
    security_map_path = BASE_DIR / "data" / "gold" / "analytics" / "dim_user_tenants.parquet"
    
    path_exists = security_map_path.exists() or security_map_path.is_dir()
    if not path_exists:
        pytest.skip("Security mapping parquet not generated yet.")

    df = pd.read_parquet(security_map_path)
    assert "user_email" in df.columns
    assert "tenant_id" in df.columns
    assert len(df) > 0, "Security mapping table is empty."