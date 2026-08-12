import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class IntelligenceCutoff(Base):
    """
    Strict temporal firewall. No data past this cutoff can be queried.
    """
    __tablename__ = "intelligence_cutoffs"
    
    cutoff_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_cutoff_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String, nullable=True)

class IntelligenceAssessment(Base):
    """
    The unified deterministic assessment record.
    """
    __tablename__ = "intelligence_assessments"
    
    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, nullable=False, index=True)
    
    # Temporal boundaries
    assessment_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_cutoff_time = Column(DateTime, nullable=False) # Absolute ceiling for all data
    news_cutoff_time = Column(DateTime, nullable=False)
    market_cutoff_time = Column(DateTime, nullable=False)
    
    # Versioning
    model_version = Column(String, nullable=True)
    feature_version = Column(String, nullable=True)
    risk_engine_version = Column(String, nullable=True)
    news_model_versions = Column(JSON, nullable=True)
    methodology_version = Column(String, nullable=False)
    
    # Fused Data Outputs
    prediction = Column(Float, nullable=True)
    prediction_probability = Column(Float, nullable=True)
    
    risk_classification = Column(String, nullable=True)
    risk_metrics = Column(JSON, nullable=True)
    
    news_sentiment_summary = Column(JSON, nullable=True)
    news_topics = Column(JSON, nullable=True)
    news_entity_summary = Column(JSON, nullable=True)
    
    statistical_relationships = Column(JSON, nullable=True)
    explanation = Column(JSON, nullable=True)
    
    # Status
    data_quality_status = Column(String, nullable=False) # OK, INCOMPLETE, DEGRADED
    
    # Deterministic Narrative Payload
    # Grouped strictly into: OBSERVED FACTS, MODEL PREDICTIONS, STATISTICAL ASSOCIATIONS, RISK MEASUREMENTS, INTERPRETATIONS, LIMITATIONS
    structured_assessment = Column(JSON, nullable=False) 
