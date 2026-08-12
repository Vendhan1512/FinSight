from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, exc

from app.models.intelligence import IntelligenceCutoff

class TemporalFirewall:
    """
    Unified data-cutoff mechanism that strictly enforces temporal boundaries 
    for all data queries during an Intelligence Assessment.
    """
    
    def __init__(self, db: Session, cutoff_time: datetime):
        self.db = db
        self.cutoff_time = cutoff_time
        self._record_cutoff()

    def _record_cutoff(self):
        """Records the instantiated cutoff in the database for lineage."""
        try:
            record = IntelligenceCutoff(
                data_cutoff_time=self.cutoff_time,
                description="Assessment Temporal Firewall"
            )
            self.db.add(record)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()

    def enforce_market_query(self, query, model_class):
        """Injects a cutoff filter into a SQLAlchemy market data query."""
        if hasattr(model_class, 'original_timestamp'):
            return query.where(model_class.original_timestamp <= self.cutoff_time)
        return query

    def enforce_news_query(self, query, model_class):
        """Injects a cutoff filter into a SQLAlchemy news article query."""
        if hasattr(model_class, 'published_at'):
            return query.where(model_class.published_at <= self.cutoff_time)
        return query
        
    def enforce_prediction_query(self, query, model_class):
        """Injects a cutoff filter into a SQLAlchemy prediction query."""
        if hasattr(model_class, 'prediction_time'):
            return query.where(model_class.prediction_time <= self.cutoff_time)
        return query
        
    def enforce_sec_query(self, query, model_class):
        """Injects a cutoff filter into a SQLAlchemy SEC filing query."""
        if hasattr(model_class, 'original_timestamp'):
            # Note SEC typically uses Date for original_timestamp
            return query.where(model_class.original_timestamp <= self.cutoff_time.date())
        return query
        
    def get_cutoff(self) -> datetime:
        return self.cutoff_time
