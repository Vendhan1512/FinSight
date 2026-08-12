import logging
import time
from typing import Dict, List, Type
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.orchestration import PipelineRun, PipelineJob
from analytics.orchestration.jobs import (
    BaseJob, MarketDataJob, SECDataJob, FREDDataJob, NewsDataJob,
    FeatureJob, NLPJob, PredictionJob, RiskJob, IntelligenceJob
)

logger = logging.getLogger(__name__)

class OrchestrationEngine:
    """
    DAG-based Pipeline Orchestrator. 
    Executes jobs sequentially based on resolved dependencies.
    """
    
    # Registry of available jobs
    JOB_REGISTRY: Dict[str, Type[BaseJob]] = {
        "MarketDataJob": MarketDataJob,
        "SECDataJob": SECDataJob,
        "FREDDataJob": FREDDataJob,
        "NewsDataJob": NewsDataJob,
        "FeatureJob": FeatureJob,
        "NLPJob": NLPJob,
        "PredictionJob": PredictionJob,
        "RiskJob": RiskJob,
        "IntelligenceJob": IntelligenceJob
    }
    
    def __init__(self, db: Session):
        self.db = db
        
    def start_pipeline(self, trigger_type: str = "MANUAL", backfill_date: str = None) -> str:
        """Initializes a new Pipeline Run and returns the run_id."""
        run = PipelineRun(
            trigger_type=trigger_type, 
            backfill_date=backfill_date,
            status="RUNNING"
        )
        self.db.add(run)
        self.db.commit()
        return str(run.run_id)
        
    def resolve_dag(self) -> List[str]:
        """
        Topological sort of the job registry based on dependencies.
        Returns a linearly executable list of job names.
        """
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(n: str):
            if n in temp_mark:
                raise ValueError("DAG contains a circular dependency!")
            if n not in visited:
                temp_mark.add(n)
                job_class = self.JOB_REGISTRY[n]
                for m in job_class.dependencies:
                    visit(m)
                temp_mark.remove(n)
                visited.add(n)
                order.append(n)
                
        for job_name in self.JOB_REGISTRY.keys():
            if job_name not in visited:
                visit(job_name)
                
        return order
        
    def execute_pipeline(self, run_id: str):
        """Executes the resolved DAG linearly. Handles retries and state tracking."""
        import uuid
        run_uuid = uuid.UUID(run_id) if isinstance(run_id, str) else run_id
        try:
            execution_order = self.resolve_dag()
            logger.info(f"Pipeline {run_id} execution order: {execution_order}")
        except Exception as e:
            logger.error(f"Failed to resolve DAG: {e}")
            self._fail_run(run_id, str(e))
            return
            
        job_statuses = {} # Track successes to decide whether to skip downstream
        
        for job_name in execution_order:
            job_class = self.JOB_REGISTRY[job_name]
            job_instance = job_class(self.db, run_id)
            job_instance.get_or_create_job_record()
            
            # 1. Dependency Check
            dependencies_met = True
            for dep in job_class.dependencies:
                if job_statuses.get(dep) != "SUCCESS":
                    dependencies_met = False
                    logger.warning(f"Skipping {job_name}: Dependency {dep} did not succeed.")
                    break
                    
            if not dependencies_met:
                job_instance.update_status("SKIPPED", error_summary="Upstream dependency failed")
                job_statuses[job_name] = "SKIPPED"
                continue
                
            # 2. Execution with Retries
            job_instance.update_status("RUNNING")
            status = "FAILED"
            error_msg = ""
            
            for attempt in range(job_class.max_retries):
                job_instance.retry_count = attempt
                try:
                    status = job_instance.execute()
                    if status in ["SUCCESS", "PARTIAL"]:
                        break # Done!
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Job {job_name} failed attempt {attempt+1}: {error_msg}")
                    # Exponential backoff 2^attempt
                    time.sleep(2 ** attempt)
                    
            job_instance.update_status(status, error_summary=error_msg)
            job_statuses[job_name] = status
            
        # 3. Finalize Run Status
        has_failures = any(s in ["FAILED", "SKIPPED"] for s in job_statuses.values())
        final_status = "FAILED" if has_failures else "SUCCESS"
        
        run = self.db.scalars(select(PipelineRun).where(PipelineRun.run_id == run_uuid)).first()
        if run:
            run.status = final_status
            run.completed_at = datetime.utcnow()
            self.db.commit()
            
        logger.info(f"Pipeline {run_id} finished with status {final_status}")

    def _fail_run(self, run_id: str, error_summary: str):
        import uuid
        run_uuid = uuid.UUID(run_id) if isinstance(run_id, str) else run_id
        run = self.db.scalars(select(PipelineRun).where(PipelineRun.run_id == run_uuid)).first()
        if run:
            run.status = "FAILED"
            run.completed_at = datetime.utcnow()
            run.error_summary = error_summary
            self.db.commit()
