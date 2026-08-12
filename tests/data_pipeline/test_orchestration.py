import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.models.orchestration import PipelineRun, PipelineJob
from analytics.orchestration.engine import OrchestrationEngine

@pytest.fixture
def mock_db_session():
    # In-memory SQLite for strict temporal testing
    engine = create_engine("sqlite:///:memory:")
    # We must import all models so Base knows about them
    from app.models import ml, intelligence, explainability, nlp, news, warehouse, market_events, orchestration
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_dag_resolution(mock_db_session):
    engine = OrchestrationEngine(mock_db_session)
    order = engine.resolve_dag()
    
    # IntelligenceJob depends on NLP, Pred, Risk.
    assert "IntelligenceJob" in order
    idx_intel = order.index("IntelligenceJob")
    
    # Ensure dependencies are executed BEFORE the dependent job
    for dep in ["NLPJob", "PredictionJob", "RiskJob"]:
        assert order.index(dep) < idx_intel, f"{dep} must run before IntelligenceJob"

def test_pipeline_execution_success(mock_db_session):
    engine = OrchestrationEngine(mock_db_session)
    run_id = engine.start_pipeline()
    engine.execute_pipeline(run_id)
    
    run = mock_db_session.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
    assert run.status == "SUCCESS"
    
    jobs = mock_db_session.query(PipelineJob).filter(PipelineJob.run_id == run_id).all()
    for job in jobs:
        assert job.status == "SUCCESS"

def test_dependency_failure_cascades(mock_db_session):
    from analytics.orchestration.jobs import MarketDataJob
    engine = OrchestrationEngine(mock_db_session)
    
    # Mock MarketDataJob to FAIL
    original_execute = MarketDataJob.execute
    MarketDataJob.execute = lambda self: "FAILED"
    
    run_id = engine.start_pipeline()
    engine.execute_pipeline(run_id)
    
    # Restore mock
    MarketDataJob.execute = original_execute
    
    run = mock_db_session.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
    assert run.status == "FAILED"
    
    jobs = {j.job_name: j.status for j in mock_db_session.query(PipelineJob).filter(PipelineJob.run_id == run_id).all()}
    
    assert jobs["MarketDataJob"] == "FAILED"
    # Dependent jobs should be SKIPPED
    assert jobs["FeatureJob"] == "SKIPPED"
    assert jobs["PredictionJob"] == "SKIPPED"
    assert jobs["RiskJob"] == "SKIPPED"
    
def test_pipeline_idempotency(mock_db_session):
    # Idempotency is usually at the data-upsert layer.
    # In the orchestration layer, calling execute_pipeline twice on the same run_id
    # might re-run jobs if they aren't protected.
    pass
