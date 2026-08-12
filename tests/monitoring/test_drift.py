import pytest
import numpy as np
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from analytics.monitoring.drift_engine import DriftEngine
from app.models.monitoring import FeatureDriftMetric, SystemAlert

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    # Cleanup drift metrics and alerts after test
    session.query(FeatureDriftMetric).delete()
    session.query(SystemAlert).delete()
    session.commit()
    session.close()

def test_calculate_psi(db):
    engine = DriftEngine(db)
    
    # Test identical distributions (PSI should be ~0)
    expected = np.random.normal(0, 1, 1000)
    actual = np.random.normal(0, 1, 1000)
    psi = engine.calculate_psi(expected, actual)
    
    assert psi < 0.1 # Minor variance due to randomness
    
    # Test drifted distribution
    actual_drifted = np.random.normal(2, 1, 1000)
    psi_drifted = engine.calculate_psi(expected, actual_drifted)
    
    assert psi_drifted > 0.2 # Significant drift

def test_calculate_ks(db):
    engine = DriftEngine(db)
    
    expected = np.random.normal(0, 1, 1000)
    actual = np.random.normal(0, 1, 1000)
    ks = engine.calculate_ks(expected, actual)
    
    assert ks < 0.1
    
    actual_drifted = np.random.normal(2, 1, 1000)
    ks_drifted = engine.calculate_ks(expected, actual_drifted)
    
    assert ks_drifted > 0.3

def test_evaluate_feature_drift(db):
    engine = DriftEngine(db)
    
    expected = np.random.normal(0, 1, 1000)
    actual = np.random.normal(3, 1, 1000) # Force huge drift
    
    now = datetime.utcnow()
    
    metric = engine.evaluate_feature_drift(
        feature_name="test_feature",
        feature_version="1.0",
        expected=expected,
        actual=actual,
        ref_start=now - timedelta(days=30),
        ref_end=now - timedelta(days=1),
        curr_start=now - timedelta(hours=24),
        curr_end=now,
        method="KS",
        threshold=0.2
    )
    
    assert metric.status == "DRIFTED"
    assert metric.value > 0.2
    
    # Verify alert was generated
    alert = db.query(SystemAlert).filter(SystemAlert.metric == "drift_test_feature").first()
    assert alert is not None
    assert alert.status == "ACTIVE"
    assert alert.severity.name in ["WARNING", "CRITICAL"]
