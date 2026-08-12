from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.warehouse import (
    DataSource,
    IngestionRun,
    MarketAsset,
    MarketPrice,
    SECCompany,
    SECFiling,
    FinancialFact,
    EconomicSeries,
    EconomicObservation
)

class CRUDDataSource(CRUDBase[DataSource]):
    def get_or_create(self, db: Session, id: str, name: str, provider: str) -> DataSource:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            obj = self.create(db, obj_in={"id": id, "name": name, "provider": provider})
        return obj

class CRUDIngestionRun(CRUDBase[IngestionRun]):
    def start_run(self, db: Session, source_id: str) -> IngestionRun:
        return self.create(db, obj_in={"source_id": source_id, "status": "running"})
        
    def complete_run(self, db: Session, run_id: str, records_processed: int, status: str = "completed"):
        run = self.get(db, run_id)
        if run:
            run.status = status
            run.completed_at = datetime.utcnow()
            run.records_processed = records_processed
            db.commit()

class CRUDMarketPrice(CRUDBase[MarketPrice]):
    def batch_upsert(self, db: Session, records: list[dict]):
        if not records:
            return
        stmt = insert(self.model).values(records)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uix_market_price",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "ingested_at": datetime.utcnow()
            }
        )
        db.execute(upsert_stmt)
        db.commit()

class CRUDSecData:
    def upsert_company(self, db: Session, cik: str, name: str, ticker: str = None):
        stmt = insert(SECCompany).values(cik=cik, name=name, ticker=ticker)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['cik'],
            set_={"name": stmt.excluded.name, "ticker": stmt.excluded.ticker}
        )
        db.execute(upsert_stmt)
        db.commit()
        
    def batch_upsert_facts(self, db: Session, records: list[dict]):
        if not records:
            return
        stmt = insert(FinancialFact).values(records)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uix_financial_fact",
            set_={
                "value": stmt.excluded.value,
                "ingested_at": datetime.utcnow()
            }
        )
        db.execute(upsert_stmt)
        db.commit()

class CRUDEconomicData:
    def batch_upsert_observations(self, db: Session, records: list[dict]):
        if not records:
            return
        stmt = insert(EconomicObservation).values(records)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uix_economic_obs",
            set_={
                "value": stmt.excluded.value,
                "realtime_end": stmt.excluded.realtime_end,
                "ingested_at": datetime.utcnow()
            }
        )
        db.execute(upsert_stmt)
        db.commit()

data_source = CRUDDataSource(DataSource)
ingestion_run = CRUDIngestionRun(IngestionRun)
market_price = CRUDMarketPrice(MarketPrice)
sec_data = CRUDSecData()
economic_data = CRUDEconomicData()
