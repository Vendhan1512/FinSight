import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.crud import crud_warehouse
from app.models.warehouse import DataQualityResult
from data_pipeline.validation.validators import MarketValidator, SecValidator, FredValidator

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def _persist_validation_results(self, run_id: str, results: List[Any]):
        if not results:
            return
            
        db_records = []
        for r in results:
            db_records.append({
                "run_id": run_id,
                "check_type": r.check_name,
                "passed": r.status == "PASSED",
                "details": {
                    "dataset": r.dataset,
                    "record_scope": r.record_scope,
                    "severity": r.severity,
                    "message": r.message,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None
                }
            })
            
        stmt = insert(DataQualityResult).values(db_records)
        self.db.execute(stmt)
        self.db.commit()

    def run_market_ingestion(self, provider, symbols: List[str]):
        logger.info(f"Starting Market ingestion pipeline using {provider.name}")
        
        crud_warehouse.data_source.get_or_create(self.db, id=provider.name, name="Market Data", provider=provider.name)
        run = crud_warehouse.ingestion_run.start_run(self.db, source_id=provider.name)
        
        total_upserted = 0
        validator = MarketValidator()
        
        try:
            for symbol in symbols:
                data = provider.fetch_daily_ohlcv(symbol)
                parsed_records = data["parsed"]
                
                # Validation Phase
                valid_records = validator.validate(parsed_records)
                
                # Transform for DB
                db_records = []
                for rec in valid_records:
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
                    
                # Upsert Phase
                crud_warehouse.market_price.batch_upsert(self.db, db_records)
                total_upserted += len(db_records)
                
            # Quality Persistence Phase
            self._persist_validation_results(run.id, validator.results)
            
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "completed")
            logger.info(f"Market pipeline completed. Upserted {total_upserted} valid records.")
            return True
            
        except Exception as e:
            logger.exception("Market pipeline failed.")
            self._persist_validation_results(run.id, validator.results)
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "failed")
            return False

    def run_sec_ingestion(self, provider, ciks: List[str]):
        logger.info(f"Starting SEC ingestion pipeline using {provider.name}")
        
        crud_warehouse.data_source.get_or_create(self.db, id=provider.name, name="SEC EDGAR", provider=provider.name)
        run = crud_warehouse.ingestion_run.start_run(self.db, source_id=provider.name)
        
        total_upserted = 0
        validator = SecValidator()
        
        try:
            for cik in ciks:
                data = provider.fetch_company_facts(cik)
                mapped_facts = data["parsed"]["mapped_facts"]
                
                valid_records = validator.validate(mapped_facts)
                
                db_records = []
                for fact in valid_records:
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

                crud_warehouse.sec_data.batch_upsert_facts(self.db, db_records)
                total_upserted += len(db_records)
                
            self._persist_validation_results(run.id, validator.results)
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "completed")
            logger.info(f"SEC pipeline completed. Upserted {total_upserted} valid records.")
            return True
            
        except Exception as e:
            logger.exception("SEC pipeline failed.")
            self._persist_validation_results(run.id, validator.results)
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "failed")
            return False

    def run_fred_ingestion(self, provider, series_ids: List[str]):
        logger.info(f"Starting FRED ingestion pipeline using {provider.name}")
        
        crud_warehouse.data_source.get_or_create(self.db, id=provider.name, name="FRED", provider=provider.name)
        run = crud_warehouse.ingestion_run.start_run(self.db, source_id=provider.name)
        
        total_upserted = 0
        validator = FredValidator()
        
        try:
            for series_id in series_ids:
                # We skip metadata in this unified orchestrator for brevity, but a full prod one would do it.
                obs_data = provider.fetch_series_observations(series_id)
                parsed_records = obs_data["parsed"]
                
                valid_records = validator.validate(parsed_records)
                
                db_records = []
                for rec in valid_records:
                    db_records.append({
                        "series_id": rec["series_id"],
                        "observation_date": rec["observation_date"],
                        "value": rec["value"],
                        "realtime_start": rec["realtime_start"],
                        "realtime_end": rec["realtime_end"],
                        "source_id": provider.name
                    })
                    
                crud_warehouse.economic_data.batch_upsert_observations(self.db, db_records)
                total_upserted += len(db_records)
                
            self._persist_validation_results(run.id, validator.results)
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "completed")
            logger.info(f"FRED pipeline completed. Upserted {total_upserted} valid records.")
            return True
            
        except Exception as e:
            logger.exception("FRED pipeline failed.")
            self._persist_validation_results(run.id, validator.results)
            crud_warehouse.ingestion_run.complete_run(self.db, run.id, total_upserted, "failed")
            return False
