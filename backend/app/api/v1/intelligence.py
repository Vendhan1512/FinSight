from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.api import deps
from app.core.exceptions import FinSightException
from analytics.intelligence.assessment_service import AssessmentService
from analytics.intelligence.timeline import TimelineBuilder
from app.models.auth import User
from app.schemas.api import IntelligenceAssessmentResponse, LineageMetadata

# No prefix here because it's defined in main.py
router = APIRouter()

@router.get("/{entity_id}", response_model=IntelligenceAssessmentResponse)
def get_integrated_assessment(
    entity_id: str, 
    cutoff: str = Query(None, description="ISO8601 string for cutoff time"), 
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["VIEWER", "ANALYST", "ADMIN"]))
):
    try:
        dt = datetime.fromisoformat(cutoff) if cutoff else datetime.utcnow()
    except ValueError:
        raise FinSightException("INVALID_DATE", "Invalid cutoff format. Use ISO8601.", 400)
        
    svc = AssessmentService(db, dt)
    try:
        assessment = svc.generate_assessment(entity_id)
    except Exception as e:
        raise FinSightException("ASSESSMENT_FAILED", str(e), 500)
    
    # Map to schema and inject Lineage
    struct = assessment.structured_assessment
    
    lineage = LineageMetadata(
        provenance_id=str(assessment.assessment_id),
        model_version=assessment.model_version,
        feature_version=assessment.feature_version,
        methodology_version=assessment.methodology_version,
        data_cutoff=assessment.data_cutoff_time
    )
    
    return IntelligenceAssessmentResponse(
        assessment_id=str(assessment.assessment_id),
        entity_id=assessment.entity_id,
        assessment_time=assessment.assessment_time,
        risk_classification=struct.get("risk_classification", "UNKNOWN"),
        prediction=str(struct.get("prediction", "UNKNOWN")),
        prediction_probability=struct.get("prediction_probability"),
        news_sentiment_summary=struct.get("news_sentiment_summary", {}),
        lineage=lineage
    )

@router.get("/{entity_id}/timeline")
def get_event_timeline(
    entity_id: str, 
    cutoff: str = Query(None, description="ISO8601 string for cutoff time"),
    limit: int = Query(20, ge=1, le=100), # Pagination limit
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["VIEWER", "ANALYST", "ADMIN"]))
):
    try:
        dt = datetime.fromisoformat(cutoff) if cutoff else datetime.utcnow()
    except ValueError:
        raise FinSightException("INVALID_DATE", "Invalid cutoff format. Use ISO8601.", 400)
        
    builder = TimelineBuilder(db, dt)
    timeline = builder.build_timeline(entity_id, limit)
    
    return {
        "entity_id": entity_id,
        "data_cutoff_time": dt.isoformat(),
        "timeline": timeline,
        "lineage": {
            "provenance_id": str(uuid.uuid4()),
            "data_cutoff": dt.isoformat(),
            "generated_at": datetime.utcnow().isoformat()
        }
    }
