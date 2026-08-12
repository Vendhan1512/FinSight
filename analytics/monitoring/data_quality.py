from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.models.monitoring import DataQualityMetric, AlertSeverity
from analytics.monitoring.alerting import AlertingEngine

logger = logging.getLogger(__name__)

class DataQualityEngine:
    def __init__(self, db: Session):
        self.db = db
        self.alerting = AlertingEngine(db)
        
    def check_table_quality(self, table_name: str, time_col: str = "timestamp") -> DataQualityMetric:
        # For simplicity, executing raw SQL to get basic metrics
        # In production, use SQLAlchemy ORM or Pandas
        
        try:
            # Record count
            count_res = self.db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            # Freshness (hours since last record)
            latest_res = self.db.execute(text(f"SELECT MAX({time_col}) FROM {table_name}")).scalar()
            
            freshness_hours = -1.0
            if latest_res:
                if isinstance(latest_res, str):
                    latest_res = datetime.fromisoformat(latest_res.replace('Z', '+00:00')[:19])
                diff = datetime.utcnow() - latest_res
                freshness_hours = diff.total_seconds() / 3600.0
                
            metric = DataQualityMetric(
                source_table=table_name,
                record_count=count_res or 0,
                missing_rate=0.0, # Placeholder for missing rate calculation
                duplicate_rate=0.0, # Placeholder
                freshness_hours=freshness_hours,
                calculated_at=datetime.utcnow()
            )
            
            self.db.add(metric)
            self.db.commit()
            
            # Alert on stale data (>24h)
            if freshness_hours > 24:
                self.alerting.generate_alert(
                    metric="data_freshness",
                    observed_value=freshness_hours,
                    threshold=24.0,
                    source=f"DATA_{table_name.upper()}",
                    severity=AlertSeverity.WARNING,
                    message=f"Table {table_name} is stale. Last updated {freshness_hours:.1f} hours ago."
                )
            else:
                self.alerting.resolve_alert("data_freshness", f"DATA_{table_name.upper()}")
                
            return metric
            
        except Exception as e:
            logger.error(f"Error checking data quality for {table_name}: {e}")
            raise
