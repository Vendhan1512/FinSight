import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.db.session import Base

class FeatureRun(Base):
    """Records metadata for every batch execution of the Feature Pipeline Orchestrator."""
    __tablename__ = "feature_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_set = Column(String, nullable=False, index=True) # e.g., 'technical_v1'
    feature_version = Column(String, nullable=False)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    source_versions = Column(JSON, nullable=True) # e.g. {"market_data": "v1", "macro": "v2"}
    
    rows_processed = Column(Integer, default=0)
    rows_created = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    
    quality_status = Column(String, nullable=True) # PASSED, FAILED
    leakage_status = Column(String, nullable=True) # PASSED, FAILED
    
    observations = relationship("FeatureObservation", back_populates="run", cascade="all, delete-orphan")


class FeatureObservation(Base):
    """
    The Versioned Feature Store table.
    Contains ONLY validated data. NEVER stores future information.
    """
    __tablename__ = "feature_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String, nullable=False, index=True)
    feature_version = Column(String, nullable=False)
    
    entity_id = Column(String, nullable=False, index=True) # Symbol or CIK
    
    observation_time = Column(DateTime, nullable=False) # When the event occurred (e.g. Q1 end)
    availability_time = Column(DateTime, nullable=False, index=True) # When the data was publicly known
    
    feature_value = Column(Float, nullable=True)
    
    source_dataset = Column(String, nullable=False)
    source_version = Column(String, nullable=True)
    
    calculation_run_id = Column(UUID(as_uuid=True), ForeignKey("feature_runs.run_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    run = relationship("FeatureRun", back_populates="observations")
