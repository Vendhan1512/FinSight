from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.auth import User
from app.core.exceptions import FinSightException
from analytics.orchestration.engine import OrchestrationEngine

router = APIRouter()

@router.post("/pipeline/trigger")
def trigger_pipeline(
    backfill_date: str = Query(None, description="ISO8601 Date for backfill runs"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["ADMIN"])) # ONLY Admin
):
    try:
        engine = OrchestrationEngine(db)
        trigger_type = "BACKFILL" if backfill_date else "MANUAL"
        run_id = engine.start_pipeline(trigger_type=trigger_type, backfill_date=backfill_date)
        
        # In a real async environment (e.g. Celery), we would dispatch this to a worker.
        # Here we run synchronously for demonstration purposes.
        engine.execute_pipeline(run_id)
        
        return {
            "message": "Pipeline execution completed.",
            "run_id": run_id,
            "trigger_type": trigger_type
        }
    except Exception as e:
        raise FinSightException("PIPELINE_ERROR", str(e), 500)
