from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import SessionLocal
from analytics.intelligence.assessment_service import AssessmentService
from analytics.intelligence.timeline import TimelineBuilder

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{entity_id}")
def get_integrated_assessment(
    entity_id: str, 
    cutoff: str = Query(None, description="ISO8601 string for cutoff time"), 
    db: Session = Depends(get_db)
):
    try:
        dt = datetime.fromisoformat(cutoff) if cutoff else datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cutoff format. Use ISO8601.")
        
    svc = AssessmentService(db, dt)
    assessment = svc.generate_assessment(entity_id)
    
    return {
        "assessment_id": assessment.assessment_id,
        "entity_id": assessment.entity_id,
        "data_cutoff_time": assessment.data_cutoff_time.isoformat(),
        "methodology_version": assessment.methodology_version,
        "data_quality_status": assessment.data_quality_status,
        "structured_assessment": assessment.structured_assessment
    }

@router.get("/{entity_id}/timeline")
def get_event_timeline(
    entity_id: str, 
    cutoff: str = Query(None, description="ISO8601 string for cutoff time"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    try:
        dt = datetime.fromisoformat(cutoff) if cutoff else datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cutoff format. Use ISO8601.")
        
    builder = TimelineBuilder(db, dt)
    timeline = builder.build_timeline(entity_id, limit)
    
    return {
        "entity_id": entity_id,
        "data_cutoff_time": dt.isoformat(),
        "timeline": timeline
    }
