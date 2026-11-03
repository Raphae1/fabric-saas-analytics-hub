import json
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

app = FastAPI(
    title="SaaS Tenant Ingestion Gateway",
    description="Zero-trust secure API gateway with token-bound tenant authorization.",
    version="2.0.0"
)

security = HTTPBearer()
BASE_DIR = Path(__file__).resolve().parent

def get_tenant_registry():
    """Load tenant registry mapping API keys to TenantIDs from config.json."""
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        logging.error(f"config.json not found at {config_path}")
        return {}
    
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        # Create a lookup dictionary: { api_key: tenant_id }
        registry = {}
        for t in data.get("AuthorizedTenants", []):
            tenant_id = t.get("TenantID")
            api_key = t.get("ApiKey")
            if tenant_id and api_key:
                registry[api_key] = tenant_id
        return registry
    except Exception as e:
        logging.error(f"Failed to parse config.json: {e}")
        return {}

@app.post("/api/v1/tenants/invoices")
async def ingest_tenant_invoices(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    registry = get_tenant_registry()
    
    # 1. Zero-Trust Token Authentication & Anti-Spoofing Binding
    if token not in registry:
        logging.warning(f"Unauthorized ingestion attempt with invalid token: {token}")
        raise HTTPException(status_code=403, detail="Invalid or unauthorized API token.")
    
    # The authenticated tenant is derived DIRECTLY from the token, preventing impersonation
    authenticated_tenant_id = registry[token]

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or empty JSON payload structure.")

    # 2. Enforce payload consistency (Optional: inject or verify tenant ID inside payload)
    body["TenantID"] = authenticated_tenant_id

    # 3. Securely land payload into Bronze partition: ./data/bronze/tenant_id=.../invoices/
    bronze_dir = BASE_DIR / "data" / "bronze" / f"tenant_id={authenticated_tenant_id}" / "invoices"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    file_path = bronze_dir / "raw_invoices_batch_01.json"
    with open(file_path, "w") as f:
        json.dump(body, f, indent=4)

    logging.info(f"Successfully ingested and landed payload for token-bound tenant {authenticated_tenant_id} at {file_path}")
    
    return {
        "status": "Success",
        "tenant_id": authenticated_tenant_id,
        "message": "Payload securely ingested via token-bound authorization.",
        "path": str(file_path)
    }

if __name__ == "__main__":
    uvicorn.run("gateway:app", host="127.0.0.1", port=8000, reload=True)