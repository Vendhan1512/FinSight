import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.orchestration import DataFreshness

logger = logging.getLogger(__name__)

class QualityGateBreach(Exception):
    pass

class QualityGates:
    """
    Evaluates circuit breakers to ensure pipeline doesn't run on stale or invalid data.
    """
    
    @staticmethod
    def verify_freshness(db: Session, source_name: str, max_lag_hours: float = 24.0):
        """
        Ensures a data source is not overly stale. 
        Raises QualityGateBreach if freshness is degraded.
        """
        record = db.scalars(
            select(DataFreshness).where(DataFreshness.source_name == source_name)
        ).first()
        
        if not record:
            # First run, pass it.
            return True
            
        if record.data_lag_hours and record.data_lag_hours > max_lag_hours:
            logger.error(f"Quality Gate Failed: {source_name} is stale. Lag: {record.data_lag_hours} hrs.")
            raise QualityGateBreach(f"Stale data source: {source_name}")
            
        if record.freshness_status == "DEGRADED":
            logger.error(f"Quality Gate Failed: {source_name} explicitly marked DEGRADED.")
            raise QualityGateBreach(f"Degraded data source: {source_name}")
            
        return True
