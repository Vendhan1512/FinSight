from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime

from app.db.base_class import Base

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class SystemAlert(Base):
    __tablename__ = "system_alerts"
    
    alert_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric = Column(String, nullable=False, index=True)
    observed_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, nullable=False) # e.g. "DATA_QUALITY", "DRIFT", "SYSTEM"
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(String, default="ACTIVE") # ACTIVE, RESOLVED
    message = Column(String, nullable=False)

class FeatureDriftMetric(Base):
    __tablename__ = "feature_drift_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    feature = Column(String, nullable=False, index=True)
    feature_version = Column(String, nullable=False)
    reference_period_start = Column(DateTime, nullable=False)
    reference_period_end = Column(DateTime, nullable=False)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    metric = Column(String, nullable=False) # e.g. "PSI", "KS"
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String, nullable=False) # OK, DRIFTED
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

class PredictionDriftMetric(Base):
    __tablename__ = "prediction_drift_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False, index=True)
    reference_period_start = Column(DateTime, nullable=False)
    reference_period_end = Column(DateTime, nullable=False)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    metric = Column(String, nullable=False) # e.g. "PSI", "KS"
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String, nullable=False) # OK, INVESTIGATE
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String, nullable=False, index=True)
    prediction_time = Column(DateTime, nullable=False)
    prediction = Column(String, nullable=False)
    prediction_probability = Column(Float, nullable=True)
    actual = Column(String, nullable=True) # E.g. OUTPERFORM, UNDERPERFORM
    horizon = Column(Integer, nullable=False) # Days
    model_version = Column(String, nullable=False, index=True)
    is_correct = Column(Integer, nullable=True) # 1 or 0
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

class DataQualityMetric(Base):
    __tablename__ = "data_quality_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    source_table = Column(String, nullable=False, index=True)
    record_count = Column(Integer, nullable=False)
    missing_rate = Column(Float, nullable=False)
    duplicate_rate = Column(Float, nullable=False)
    freshness_hours = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
