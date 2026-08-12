from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.api import deps
from app.models.auth import User
from app.models.monitoring import SystemAlert, DataQualityMetric, ModelPerformance, FeatureDriftMetric

router = APIRouter()

@router.get("/system/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@router.get("/alerts")
def get_alerts(
    status: str = "ACTIVE",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["ADMIN", "ANALYST"]))
):
    alerts = db.query(SystemAlert).filter(SystemAlert.status == status).order_by(SystemAlert.timestamp.desc()).all()
    return alerts

@router.get("/performance/{model_version}")
def get_model_performance(
    model_version: str,
    days: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["ADMIN", "ANALYST"]))
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    perf = db.query(ModelPerformance).filter(
        ModelPerformance.model_version == model_version,
        ModelPerformance.calculated_at >= cutoff
    ).order_by(ModelPerformance.calculated_at.asc()).all()
    
    # Calculate aggregate accuracy
    total = len(perf)
    correct = sum(1 for p in perf if p.is_correct == 1)
    accuracy = (correct / total) if total > 0 else 0.0
    
    return {
        "model_version": model_version,
        "total_resolved_predictions": total,
        "directional_accuracy": accuracy,
        "history": perf
    }

@router.get("/drift/{feature_name}")
def get_feature_drift(
    feature_name: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_role(["ADMIN", "ANALYST"]))
):
    drift = db.query(FeatureDriftMetric).filter(
        FeatureDriftMetric.feature == feature_name
    ).order_by(FeatureDriftMetric.calculated_at.desc()).limit(10).all()
    
    return drift
