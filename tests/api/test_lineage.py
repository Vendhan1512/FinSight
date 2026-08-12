import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.db.base_class import Base
from app.api import deps
from app.models.auth import User
from app.core import security

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models import auth, intelligence, orchestration

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[deps.get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_analyst():
    db = TestingSessionLocal()
    analyst = User(username="analyst2", hashed_password=security.get_password_hash("analyst123"), role="ANALYST")
    db.add(analyst)
    db.commit()
    db.close()
    
    # Get token
    res = client.post("/api/v1/auth/login", data={"username": "analyst2", "password": "analyst123"})
    return res.json()["access_token"]

def test_intelligence_endpoint_contains_lineage(setup_analyst, monkeypatch):
    token = setup_analyst
    
    # Mock the AssessmentService to avoid running the full pipeline in tests
    from analytics.intelligence.assessment_service import AssessmentService
    
    class MockAssessment:
        assessment_id = "test-uuid"
        entity_id = "AAPL"
        assessment_time = datetime.utcnow()
        data_cutoff_time = datetime.utcnow()
        model_version = "v1.0"
        feature_version = "v1.0"
        methodology_version = "v2.1"
        data_quality_status = "PASS"
        structured_assessment = {
            "risk_classification": "MODERATE",
            "prediction": "OUTPERFORM",
            "prediction_probability": 0.75,
            "news_sentiment_summary": {"score": 0.8}
        }
    
    def mock_generate_assessment(self, entity_id):
        return MockAssessment()
        
    monkeypatch.setattr(AssessmentService, "generate_assessment", mock_generate_assessment)
    
    response = client.get(
        "/api/v1/intelligence/AAPL",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "lineage" in data
    lineage = data["lineage"]
    assert lineage["provenance_id"] == "test-uuid"
    assert lineage["model_version"] == "v1.0"
    assert lineage["methodology_version"] == "v2.1"
    assert "generated_at" in lineage

def test_timeline_endpoint_contains_lineage(setup_analyst, monkeypatch):
    token = setup_analyst
    
    from analytics.intelligence.timeline import TimelineBuilder
    def mock_build_timeline(self, entity_id, limit):
        return [{"event": "Test"}]
        
    monkeypatch.setattr(TimelineBuilder, "build_timeline", mock_build_timeline)
    
    response = client.get(
        "/api/v1/intelligence/AAPL/timeline?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "lineage" in data
    assert "provenance_id" in data["lineage"]

def test_invalid_cutoff_format(setup_analyst):
    token = setup_analyst
    
    response = client.get(
        "/api/v1/intelligence/AAPL?cutoff=not-a-date",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_DATE"
    assert "request_id" in response.json()
