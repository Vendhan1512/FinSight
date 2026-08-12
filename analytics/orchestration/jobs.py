import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.orchestration import PipelineJob, PipelineRun

logger = logging.getLogger(__name__)

class BaseJob(ABC):
    """
    Abstract Base Class for Pipeline Jobs.
    """
    name = "BaseJob"
    dependencies = [] # List of string job names that must SUCCESS before this runs
    max_retries = 3
    
    def __init__(self, db: Session, run_id: str):
        import uuid
        self.db = db
        self.run_id = uuid.UUID(run_id) if isinstance(run_id, str) else run_id
        self.job_id = None
        self.retry_count = 0

    def get_or_create_job_record(self) -> PipelineJob:
        job = self.db.scalars(
            select(PipelineJob).where(
                PipelineJob.run_id == self.run_id, 
                PipelineJob.job_name == self.name
            )
        ).first()
        
        if not job:
            job = PipelineJob(run_id=self.run_id, job_name=self.name, status="PENDING")
            self.db.add(job)
            self.db.commit()
            
        self.job_id = job.job_id
        return job

    def update_status(self, status: str, error_summary: str = None, processed: int = 0, failed: int = 0):
        job = self.db.scalars(select(PipelineJob).where(PipelineJob.job_id == self.job_id)).first()
        if not job: return
        
        job.status = status
        if status == "RUNNING":
            job.started_at = datetime.utcnow()
        elif status in ["SUCCESS", "FAILED", "PARTIAL", "SKIPPED"]:
            job.completed_at = datetime.utcnow()
            
        if error_summary:
            job.error_summary = error_summary
            
        job.records_processed = processed
        job.records_failed = failed
        job.retry_count = self.retry_count
        
        self.db.commit()

    @abstractmethod
    def execute(self) -> str:
        """
        Executes the job logic. Returns one of: SUCCESS, PARTIAL, FAILED.
        """
        pass

# --- Concrete Jobs ---

class MarketDataJob(BaseJob):
    name = "MarketDataJob"
    dependencies = []
    
    def execute(self) -> str:
        # Calls data_pipeline.orchestrator market ingestion logic
        # For this skeleton, we assume it's wired properly.
        logger.info("Executing MarketDataJob...")
        time.sleep(0.5) # Simulate IO
        return "SUCCESS"

class SECDataJob(BaseJob):
    name = "SECDataJob"
    dependencies = []
    
    def execute(self) -> str:
        logger.info("Executing SECDataJob...")
        time.sleep(0.5)
        return "SUCCESS"

class FREDDataJob(BaseJob):
    name = "FREDDataJob"
    dependencies = []
    
    def execute(self) -> str:
        logger.info("Executing FREDDataJob...")
        time.sleep(0.5)
        return "SUCCESS"

class NewsDataJob(BaseJob):
    name = "NewsDataJob"
    dependencies = []
    
    def execute(self) -> str:
        logger.info("Executing NewsDataJob...")
        time.sleep(0.5)
        return "SUCCESS"

class NLPJob(BaseJob):
    name = "NLPJob"
    dependencies = ["NewsDataJob"]
    
    def execute(self) -> str:
        logger.info("Executing NLPJob...")
        time.sleep(0.5)
        return "SUCCESS"

class FeatureJob(BaseJob):
    name = "FeatureJob"
    dependencies = ["MarketDataJob", "SECDataJob", "FREDDataJob"]
    
    def execute(self) -> str:
        logger.info("Executing FeatureJob...")
        time.sleep(0.5)
        return "SUCCESS"

class PredictionJob(BaseJob):
    name = "PredictionJob"
    dependencies = ["FeatureJob"]
    
    def execute(self) -> str:
        logger.info("Executing PredictionJob...")
        time.sleep(0.5)
        return "SUCCESS"

class RiskJob(BaseJob):
    name = "RiskJob"
    dependencies = ["MarketDataJob"]
    
    def execute(self) -> str:
        logger.info("Executing RiskJob...")
        time.sleep(0.5)
        return "SUCCESS"

class IntelligenceJob(BaseJob):
    name = "IntelligenceJob"
    dependencies = ["NLPJob", "PredictionJob", "RiskJob"]
    
    def execute(self) -> str:
        logger.info("Executing IntelligenceJob...")
        time.sleep(0.5)
        return "SUCCESS"
