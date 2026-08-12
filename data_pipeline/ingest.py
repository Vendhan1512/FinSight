import sys
import os
import logging
from datetime import datetime

# Ensure we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud import crud_warehouse
from providers.alpha_vantage import AlphaVantageProvider
from providers.base import ProviderError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def ingest_symbol(symbol: str, run_id: str, provider: AlphaVantageProvider):
    logger.info(f"Starting ingestion for {symbol} using {provider.name}")
    db = SessionLocal()
    try:
        data = provider.fetch_daily_ohlcv(symbol)
        parsed_records = data["parsed"]
        
        # We need to map to MarketPrice model which expects source_id
        db_records = []
        for rec in parsed_records:
            db_records.append({
                "symbol": rec["symbol"],
                "timestamp": rec["timestamp"],
                "open": rec["open"],
                "high": rec["high"],
                "low": rec["low"],
                "close": rec["close"],
                "volume": rec["volume"],
                "source_id": provider.name
            })
            
        crud_warehouse.market_price.batch_upsert(db, db_records)
        
        logger.info(f"Successfully ingested {len(parsed_records)} records for {symbol}.")
        return len(parsed_records)

    except ProviderError as e:
        logger.error(f"Provider error during ingestion of {symbol}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during ingestion of {symbol}: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if not settings.alpha_vantage_api_key:
        logger.error("ALPHA_VANTAGE_API_KEY is missing from environment. Please configure it in .env.")
        sys.exit(1)
        
    provider = AlphaVantageProvider(api_key=settings.alpha_vantage_api_key)
    
    db = SessionLocal()
    # 1. Ensure Data Source exists
    crud_warehouse.data_source.get_or_create(db, id=provider.name, name="Alpha Vantage", provider="alpha_vantage")
    
    # 2. Start Ingestion Run
    run = crud_warehouse.ingestion_run.start_run(db, source_id=provider.name)
    db.close()
    
    symbols_to_ingest = ["AAPL"]
    
    total_processed = 0
    try:
        for sym in symbols_to_ingest:
            total_processed += ingest_symbol(sym, run.id, provider)
            
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "completed")
        db.close()
    except Exception:
        db = SessionLocal()
        crud_warehouse.ingestion_run.complete_run(db, run.id, total_processed, "failed")
        db.close()
