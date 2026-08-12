import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.models.warehouse import AnalyticalMarket
from app.models.news import NewsArticle
from app.models.ml import ModelPrediction
from app.models.nlp import NewsArticleEntity
from analytics.intelligence.assessment_service import AssessmentService
from analytics.intelligence.timeline import TimelineBuilder

@pytest.fixture
def mock_db_session():
    # In-memory SQLite for strict temporal testing
    engine = create_engine("sqlite:///:memory:")
    # We must import all models so Base knows about them
    from app.models import ml, intelligence, explainability, nlp, news, warehouse, market_events
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_temporal_firewall_blocks_future_news(mock_db_session):
    """Ensure that a news article published AFTER the cutoff is completely hidden."""
    cutoff = datetime(2023, 1, 1, 12, 0, 0)
    
    # Past article
    art_past = NewsArticle(
        article_id="past_1",
        title="Past News",
        published_at=cutoff - timedelta(days=1),
        source_id="mock",
        url="http://mock.com",
        content="Past Content",
        description="Desc"
    )
    # Future article (Should leak without firewall)
    art_future = NewsArticle(
        article_id="future_1",
        title="Future News",
        published_at=cutoff + timedelta(days=1),
        source_id="mock",
        url="http://mock.com",
        content="Future Content",
        description="Desc"
    )
    
    mock_db_session.add(art_past)
    mock_db_session.add(art_future)
    
    # Associate with entity AAPL
    mock_db_session.add(NewsArticleEntity(article_id="past_1", canonical_entity_id="AAPL"))
    mock_db_session.add(NewsArticleEntity(article_id="future_1", canonical_entity_id="AAPL"))
    
    mock_db_session.commit()
    
    # Run assessment
    svc = AssessmentService(mock_db_session, cutoff)
    assessment = svc.generate_assessment("AAPL")
    
    facts = assessment.structured_assessment["OBSERVED_FACTS"]
    assert facts["Recent_Articles_Count"] == 1, "Future article leaked into assessment!"

def test_temporal_firewall_blocks_future_market_data(mock_db_session):
    """Ensure that market prices AFTER the cutoff do not appear in timelines."""
    cutoff = datetime(2023, 1, 1, 12, 0, 0)
    
    mkt_past = AnalyticalMarket(
        symbol="AAPL",
        original_timestamp=cutoff - timedelta(days=1),
        open=100.0, high=105.0, low=99.0, close=104.0, volume=1000
    )
    mkt_future = AnalyticalMarket(
        symbol="AAPL",
        original_timestamp=cutoff + timedelta(days=1),
        open=104.0, high=110.0, low=103.0, close=109.0, volume=1000
    )
    mock_db_session.add(mkt_past)
    mock_db_session.add(mkt_future)
    mock_db_session.commit()
    
    builder = TimelineBuilder(mock_db_session, cutoff)
    timeline = builder.build_timeline("AAPL")
    
    # Ensure no event in timeline has a timestamp > cutoff
    for ev in timeline:
        assert ev["timestamp"] <= cutoff, f"Temporal leakage: {ev}"

def test_temporal_firewall_blocks_future_predictions(mock_db_session):
    """Ensure future model predictions are omitted."""
    import uuid
    cutoff = datetime(2023, 1, 1, 12, 0, 0)
    
    pred_future = ModelPrediction(
        prediction_id=uuid.uuid4(),
        entity_id="AAPL",
        prediction_time=cutoff + timedelta(days=1),
        fold_id=uuid.uuid4(),
        model_name="v1",
        prediction=150.0
    )
    mock_db_session.add(pred_future)
    mock_db_session.commit()
    
    svc = AssessmentService(mock_db_session, cutoff)
    assessment = svc.generate_assessment("AAPL")
    
    assert assessment.prediction is None, "Future prediction leaked!"
    assert assessment.structured_assessment["MODEL_PREDICTIONS"]["Prediction"] == "No prediction available."
