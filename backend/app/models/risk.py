import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

# Import the Base from the existing schema to attach to the same metadata
from app.models.base import Base

class RiskCalculationRun(Base):
    """
    The formal ledger for VaR and CVaR calculations.
    Ensures that every risk metric is strictly bound to the exact 
    Point-in-Time it was calculated.
    """
    __tablename__ = "risk_calculation_runs"
    
    calculation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, nullable=False, index=True) # e.g., 'AAPL', 'PORTFOLIO_1'
    
    calculation_time = Column(DateTime, nullable=False, index=True) # T
    
    observation_window = Column(Integer, nullable=False) # e.g., 252 days
    confidence_level = Column(Float, nullable=False) # e.g., 0.95 or 0.99
    horizon = Column(Integer, nullable=False, default=1) # Target horizon (days)
    
    method = Column(String, nullable=False) # 'historical', 'parametric_normal'
    
    var_value = Column(Float, nullable=False)
    cvar_value = Column(Float, nullable=True) # Conditional Value at Risk
    
    sample_size = Column(Integer, nullable=False) # Number of actual historical observations used
    
    # Flags to indicate if the calculation is suspicious (e.g. kurtosis > 3 on Parametric Normal)
    warning_flags = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class HistoricalScenario(Base):
    """
    Registry for valid, verified historical stress periods.
    Prevents synthetic or fabricated crisis generation.
    """
    __tablename__ = "historical_scenarios"
    
    scenario_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    event_source = Column(String, nullable=False) # e.g. "NBER", "Market Observation"
    source_reference = Column(String, nullable=True) # URL or citation
    
    methodology_version = Column(String, nullable=False, default="v1.0")
    
    is_valid = Column(Boolean, default=True) # Dynamically flipped to False if data coverage fails
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RiskAssessment(Base):
    """
    The final integrated Risk Intelligence object.
    Stores the unified classification and the empirical justification.
    """
    __tablename__ = "risk_assessments"
    
    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, nullable=False, index=True) # Portfolio or Asset ID
    
    assessment_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_cutoff_time = Column(DateTime, nullable=False)
    
    risk_classification = Column(String, nullable=False) # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    
    # The JSON payload containing the RiskExplanation and all driving empirical metrics
    payload = Column(JSON, nullable=False)
    
    methodology_version = Column(String, nullable=False, default="v1.0")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
