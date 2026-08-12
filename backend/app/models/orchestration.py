import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class PipelineRun(Base):
    """
    Master record for a pipeline execution.
    """
    __tablename__ = "pipeline_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="PENDING") # PENDING, RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    trigger_type = Column(String, nullable=False, default="MANUAL") # MANUAL, CRON, BACKFILL
    backfill_date = Column(String, nullable=True) # ISO Date if this is a backfill
    error_summary = Column(String, nullable=True)

class PipelineJob(Base):
    """
    Individual job within a pipeline run (e.g. MarketDataJob, NLPJob).
    """
    __tablename__ = "pipeline_jobs"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_runs.run_id"), nullable=False, index=True)
    job_name = Column(String, nullable=False, index=True)
    
    status = Column(String, nullable=False, default="PENDING") # PENDING, RUNNING, SUCCESS, PARTIAL, FAILED, SKIPPED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    records_processed = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    
    source_version = Column(String, nullable=True) # e.g. provider API version
    code_version = Column(String, nullable=True)
    
    retry_count = Column(Integer, nullable=False, default=0)
    error_summary = Column(String, nullable=True)

class DataFreshness(Base):
    """
    Tracks the freshness and lag of downstream integrated data sources.
    """
    __tablename__ = "data_freshness"
    
    source_name = Column(String, primary_key=True) # e.g. 'ALPHA_VANTAGE', 'SEC_EDGAR', 'FRED'
    latest_source_timestamp = Column(DateTime, nullable=True) # The max date observed in the provider data
    latest_ingested_timestamp = Column(DateTime, nullable=True) # The max date physically written to our DB
    last_successful_run = Column(DateTime, nullable=True)
    
    data_lag_hours = Column(Float, nullable=True)
    freshness_status = Column(String, nullable=False, default="UNKNOWN") # FRESH, STALE, DEGRADED
