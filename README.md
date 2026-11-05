## Phase 3: Microsoft Fabric & Delta Lake Medallion Architecture

### Overview
Phase 3 transitions the platform data engine to Microsoft Fabric (OneLake), orchestrating raw multi-tenant data into structured Delta Lake tables with automated Data Factory pipelines and data quality guardrails.

### Architecture & Pipeline Flow
[ Raw Files / API Payload ] 
           │
           ▼
[ NB_01_Bronze_Ingestion ]    --> Stores raw Parquet files (partitioned by tenant_id)
           │
           ▼
[ NB_02_Silver_Transformation ] --> Delta Lake managed table: dim_invoices (deduplicated & cleaned)
           │
           ▼
[ NB_03_Gold_Aggregations ]     --> Delta Lake aggregated table: act_monthly_revenue
           │
           ▼
[ NB_04_Data_Quality ]         --> Automated assertions (null checks, range validation, PK uniqueness)

### Notebook Suite
1. NB_01_Bronze_Ingestion: Ingests incoming multi-tenant JSON/Parquet payloads into OneLake raw storage (Files/bronze/invoices).
2. NB_02_Silver_Transformation: Applies schema enforcement, date casting, deduplication, and lands managed Delta tables (Tables/dim_invoices).
3. NB_03_Gold_Aggregations: Generates tenant-partitioned executive financial metrics (Tables/fact_monthly_revenue).
4. NB_04_Data_Quality: Automated assertion engine validating primary key integrity, non-null tenant bindings, and strictly positive financial amounts.

### Data Factory Orchestration
* **Pipeline Name:** PL_SaaS_Medallion_Pipeline
* **Execution Chain:** Run_Bronze_Ingestion ➔ Run_Silver_Transformation ➔ Run_Gold_Aggregations ➔ Run_Data_Quality
* **Resilience:** Automatic retry policy configured across all notebook activities (2 retries, 30s interval).
