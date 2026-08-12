from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.db.session import SessionLocal
from app.api import deps
from app.core.exceptions import FinSightException

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/live")
def get_liveness():
    """Liveness probe indicates the process is up and running."""
    return {"status": "ok", "service": "FinSight API", "version": "1.0.0"}

@router.get("/ready")
def get_readiness(db: Session = Depends(get_db)):
    """Readiness probe verifies the process can connect to dependencies (DB)."""
    try:
        # Simple query to verify DB connection
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")
