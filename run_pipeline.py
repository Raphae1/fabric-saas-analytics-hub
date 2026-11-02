import time
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def run_step(script_name):
    """Executes a pipeline step script and checks for success."""
    script_path = Path(script_name)
    if not script_path.exists():
        logging.error(f"Required pipeline script not found: {script_name}")
        return False
        
    logging.info(f"=== STARTING STAGE: {script_name} ===")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time
        logging.info(result.stdout)
        logging.info(f"=== STAGE COMPLETED: {script_name} (Duration: {duration:.2f}s) ===\n")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Stage failed in {script_name}:")
        logging.error(e.stderr)
        return False

def main():
    logging.info("Starting End-to-End Medallion Data Pipeline Orchestration...")
    pipeline_start = time.time()

    steps = [
        "ingest.py",         # Bronze Layer: Ingestion from API / mock source
        "transform.py",      # Silver Layer: Cleaning, flattening, & Parquet serialization
        "gold_aggregations.py" # Gold Layer: Business aggregations & dimensional models
    ]

    for step in steps:
        success = run_step(step)
        if not success:
            logging.critical(f"Pipeline halted due to failure in stage: {step}")
            sys.exit(1)

    total_duration = time.time() - pipeline_start
    logging.info(f"?? Pipeline Execution Successful! Total Duration: {total_duration:.2f}s")

if __name__ == "__main__":
    main()
