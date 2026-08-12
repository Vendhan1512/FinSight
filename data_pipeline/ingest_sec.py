import sys
import os
import logging
from datetime import datetime

# Ensure we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud import crud_warehouse
from providers.sec_edgar import SecEdgarProvider
from providers.base import ProviderError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def ingest_sec_facts(cik: str, run_id: str, provider: SecEdgarProvider):
    logger.info(f"Starting SEC EDGAR ingestion for CIK {cik}")
    db = SessionLocal()
    try:
        data = provider.fetch_company_facts(cik)
        parsed_data = data["parsed"]
        mapped_facts = parsed_data["mapped_facts"]
        
        # Map to FinancialFact schema
        db_records = []
        for fact in mapped_facts:
            # We assume the accession_number is already inserted into sec_filings for foreign key constraint
            # In a full pipeline, we would upsert the sec_filings table first. For now, we rely on the DB structure.
            # To prevent FK violations if filing doesn't exist, we should ideally fetch filing metadata.
            # But based on the schema, financial_facts references sec_filings.
            db_records.append({
                "accession_number": fact["accession_number"],
                "metric": fact["metric"],
                "concept": fact["concept"],
                "value": fact["value"],
                "unit": fact["unit"],
                "start_date": fact["start_date"],
                "end_date": fact["end_date"],
                "source_id": provider.name
            })

        crud_warehouse.sec_data.batch_upsert_facts(db, db_records)
        
        logger.info(f"Successfully ingested {len(mapped_facts)} financial facts for CIK {cik}.")
        return len(mapped_facts)

    except ProviderError as e:
        logger.error(f"Provider error during ingestion of {cik}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during ingestion of {cik}: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if not settings.sec_user_agent or "developer@example.com" in settings.sec_user_agent:
        logger.warning("SEC_USER_AGENT is using the default developer email.")
        
    provider = SecEdgarProvider(user_agent=settings.sec_user_agent)
    
    db = SessionLocal()
    crud_warehouse.data_source.get_or_create(db, id=provider.name, name="SEC EDGAR", provider="sec_edgar")
    run = crud_warehouse.ingestion_run.start_run(db, source_id=provider.name)
    db.close()
    
    ciks_to_ingest = ["0000320193"]
    total_processed = 0
    try:
        for cik in ciks_to_ingest:
            total_processed += ingest_sec_facts(cik, run.id, provider)
            
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "completed")
        db.close()
    except Exception:
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "failed")
        db.close()
