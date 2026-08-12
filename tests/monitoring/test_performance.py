import pytest
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from analytics.monitoring.performance_engine import PerformanceEngine
from app.models.ml import Prediction
from app.models.warehouse import MarketPrice
from app.models.monitoring import ModelPerformance

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    
    session.query(ModelPerformance).filter(ModelPerformance.prediction_id == "mock_perf_pred").delete()
    session.query(Prediction).filter(Prediction.prediction_id == "mock_perf_pred").delete()
    session.query(MarketPrice).filter(MarketPrice.entity_id == "MOCK_PERF").delete()
    
    session.commit()
    session.close()

def test_resolve_pending_predictions(db):
    engine = PerformanceEngine(db)
    
    past_date = datetime.utcnow() - timedelta(days=25)
    target_date = past_date + timedelta(days=20)
    
    # 1. Create a prediction made 25 days ago (horizon 20 days has elapsed)
    pred = Prediction(
        prediction_id="mock_perf_pred",
        entity_id="MOCK_PERF",
        model_version="test-1.0",
        feature_version="1.0",
        prediction_time=past_date,
        predicted_value="OUTPERFORM",
        prediction_probability=0.8,
        features_json="{}"
    )
    db.add(pred)
    
    # 2. Create MarketPrice at T0 (prediction time)
    price_t0 = MarketPrice(
        entity_id="MOCK_PERF",
        timestamp=past_date,
        open_price=100.0, high_price=100.0, low_price=100.0, close_price=100.0,
        volume=1000, adjusted_close=100.0, provider_id="TEST"
    )
    db.add(price_t0)
    
    # 3. Create MarketPrice at T1 (target date). Price goes up -> OUTPERFORM
    price_t1 = MarketPrice(
        entity_id="MOCK_PERF",
        timestamp=target_date + timedelta(hours=1),
        open_price=110.0, high_price=110.0, low_price=110.0, close_price=110.0,
        volume=1000, adjusted_close=110.0, provider_id="TEST"
    )
    db.add(price_t1)
    db.commit()
    
    # Resolve
    count = engine.resolve_pending_predictions("test-1.0")
    
    assert count >= 1
    
    # Verify Performance record
    perf = db.query(ModelPerformance).filter(ModelPerformance.prediction_id == "mock_perf_pred").first()
    assert perf is not None
    assert perf.actual == "OUTPERFORM"
    assert perf.is_correct == 1
