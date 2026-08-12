import sys
import os
import logging
from datetime import datetime

# Ensure we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud import crud_warehouse
from app.models.warehouse import EconomicSeries
from sqlalchemy.dialects.postgresql import insert
from providers.fred import FredProvider
from providers.base import ProviderError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FRED_SERIES_TO_INGEST = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "GDP", "GS10"]

def ingest_series(series_id: str, run_id: str, provider: FredProvider):
    logger.info(f"Starting FRED ingestion for series {series_id}")
    db = SessionLocal()
    try:
        meta_raw = provider.fetch_series_metadata(series_id)
        if "seriess" in meta_raw and len(meta_raw["seriess"]) > 0:
            meta = meta_raw["seriess"][0]
            stmt_meta = insert(EconomicSeries).values(
                id=series_id,
                title=meta.get("title", ""),
                frequency=meta.get("frequency_short", ""),
                units=meta.get("units_short", "")
            )
            upsert_meta = stmt_meta.on_conflict_do_update(
                index_elements=['id'],
                set_={"title": stmt_meta.excluded.title, "ingested_at": datetime.utcnow()}
            )
            db.execute(upsert_meta)
            db.commit()
            
        obs_data = provider.fetch_series_observations(series_id)
        parsed_records = obs_data["parsed"]
        
        db_records = []
        for rec in parsed_records:
            db_records.append({
                "series_id": rec["series_id"],
                "observation_date": rec["observation_date"],
                "value": rec["value"],
                "realtime_start": rec["realtime_start"],
                "realtime_end": rec["realtime_end"],
                "source_id": provider.name
            })
            
        crud_warehouse.economic_data.batch_upsert_observations(db, db_records)
        
        logger.info(f"Ingested {len(parsed_records)} observations for {series_id}.")
        return len(parsed_records)

    except ProviderError as e:
        logger.error(f"Provider error during FRED ingestion of {series_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during FRED ingestion of {series_id}: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if not settings.fred_api_key:
        logger.error("FRED_API_KEY is missing from environment. Please configure it in .env.")
        sys.exit(1)
        
    provider = FredProvider(api_key=settings.fred_api_key)
    
    db = SessionLocal()
    crud_warehouse.data_source.get_or_create(db, id=provider.name, name="FRED", provider="fred")
    run = crud_warehouse.ingestion_run.start_run(db, source_id=provider.name)
    db.close()
    
    total_processed = 0
    try:
        for series in FRED_SERIES_TO_INGEST:
            total_processed += ingest_series(series, run.id, provider)
            
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "completed")
        db.close()
    except Exception:
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "failed")
        db.close()
