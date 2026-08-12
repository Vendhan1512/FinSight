from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.api import deps
from app.core.exceptions import FinSightException

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=dict)
def health_check(db: Session = Depends(deps.get_db)):
    """
    Health check endpoint that verifies database connectivity.
    """
    try:
        # Simple query to verify DB connection
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise FinSightException(message="Database connection failed", status_code=503)
