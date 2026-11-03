import json
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

app = FastAPI(
    title="SaaS Tenant Ingestion Gateway",
    description="Secure zero-trust API gateway for multi-tenant data ingestion into Bronze layer.",
    version="1.0.0"
)

# Anchor paths relative to this script's directory
BASE_DIR = Path(__file__).resolve().parent

def get_authorized_tenants():
    """Load authorized tenants from the central config.json boundary."""
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        logging.error(f"config.json not found at expected path: {config_path}")
        return []
    
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        return [t["TenantID"] for t in data.get("AuthorizedTenants", [])]
    except Exception as e:
        logging.error(f"Failed to read config.json: {e}")
        return []

@app.post("/api/v1/tenants/{tenant_id}/invoices")
async def ingest_tenant_invoices(tenant_id: str, request: Request):
    authorized_tenants = get_authorized_tenants()
    
    # 1. Zero-Trust Perimeter Check: Verify tenant exists in central config
    if tenant_id not in authorized_tenants:
        logging.warning(f"Unauthorized ingestion attempt for tenant: {tenant_id}. Authorized list: {authorized_tenants}")
        raise HTTPException(status_code=403, detail=f"Unauthorized tenant ID: {tenant_id}")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or empty JSON payload structure.")

    # 2. Validate payload matches URL route parameter (prevent header/payload spoofing)
    payload_tenant = body.get("TenantID")
    if payload_tenant and payload_tenant != tenant_id:
        logging.warning(f"Security Violation: URL tenant '{tenant_id}' does not match payload tenant '{payload_tenant}'.")
        raise HTTPException(
            status_code=400, 
            detail=f"Security Violation: URL tenant '{tenant_id}' does not match payload tenant '{payload_tenant}'."
        )

    # 3. Securely land payload into Bronze partition: ./data/bronze/tenant_id=.../invoices/
    bronze_dir = BASE_DIR / "data" / "bronze" / f"tenant_id={tenant_id}" / "invoices"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    file_path = bronze_dir / "raw_invoices_batch_01.json"
    with open(file_path, "w") as f:
        json.dump(body, f, indent=4)

    logging.info(f"Successfully ingested and landed payload for {tenant_id} at {file_path}")
    
    return {
        "status": "Success",
        "message": f"Payload successfully ingested for tenant {tenant_id}",
        "path": str(file_path)
    }

if __name__ == "__main__":
    uvicorn.run("gateway:app", host="127.0.0.1", port=8000, reload=True)