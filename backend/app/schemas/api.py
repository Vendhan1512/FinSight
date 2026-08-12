from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class APIError(BaseModel):
    error_code: str
    message: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LineageMetadata(BaseModel):
    provenance_id: str
    model_version: Optional[str] = None
    feature_version: Optional[str] = None
    methodology_version: Optional[str] = None
    data_cutoff: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class IntelligenceAssessmentRequest(BaseModel):
    entity_id: str = Field(..., description="The symbol or portfolio ID")
    horizon: int = Field(1, ge=1, le=252, description="Prediction horizon in days")

class IntelligenceAssessmentResponse(BaseModel):
    assessment_id: str
    entity_id: str
    assessment_time: datetime
    risk_classification: str
    prediction: str
    prediction_probability: Optional[float]
    news_sentiment_summary: Dict[str, Any]
    lineage: LineageMetadata
