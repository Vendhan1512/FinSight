from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging

from app.models.monitoring import SystemAlert, AlertSeverity

logger = logging.getLogger(__name__)

class AlertingEngine:
    def __init__(self, db: Session):
        self.db = db
        
    def generate_alert(self, metric: str, observed_value: float, threshold: float, 
                      source: str, severity: AlertSeverity, message: str) -> SystemAlert:
        
        # Check if an identical ACTIVE alert exists
        existing = self.db.query(SystemAlert).filter(
            SystemAlert.metric == metric,
            SystemAlert.source == source,
            SystemAlert.status == "ACTIVE"
        ).first()
        
        if existing:
            # Update the existing alert with the new value
            existing.observed_value = observed_value
            existing.timestamp = datetime.utcnow()
            existing.message = message
            existing.severity = severity
            self.db.commit()
            return existing
            
        alert = SystemAlert(
            alert_id=str(uuid.uuid4()),
            metric=metric,
            observed_value=observed_value,
            threshold=threshold,
            timestamp=datetime.utcnow(),
            source=source,
            severity=severity,
            status="ACTIVE",
            message=message
        )
        self.db.add(alert)
        self.db.commit()
        
        logger.warning(f"[{severity.value}] Alert Generated: {source} - {metric} ({observed_value} vs {threshold}) - {message}")
        
        return alert

    def resolve_alert(self, metric: str, source: str) -> None:
        alerts = self.db.query(SystemAlert).filter(
            SystemAlert.metric == metric,
            SystemAlert.source == source,
            SystemAlert.status == "ACTIVE"
        ).all()
        
        for alert in alerts:
            alert.status = "RESOLVED"
            
        if alerts:
            self.db.commit()
            logger.info(f"Resolved alerts for {source} - {metric}")
