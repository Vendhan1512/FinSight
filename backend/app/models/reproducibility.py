from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ReproducibilityManifest(Base):
    __tablename__ = "reproducibility_manifest"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True, unique=True)
    experiment_type = Column(String) # 'MODEL_TRAIN', 'RISK_CALC', 'NEWS_ANALYSIS'
    
    # Environment
    git_commit = Column(String)
    python_version = Column(String)
    os_info = Column(String)
    dependency_lockfile = Column(JSON)
    random_seed = Column(Integer, nullable=True)
    
    # Data & Configuration
    dataset_version = Column(String)
    feature_version = Column(String)
    model_version = Column(String)
    configuration_hash = Column(String)
    
    # Temporal Scope
    training_start = Column(DateTime)
    training_end = Column(DateTime)
    validation_start = Column(DateTime, nullable=True)
    validation_end = Column(DateTime, nullable=True)
    test_start = Column(DateTime, nullable=True)
    test_end = Column(DateTime, nullable=True)
    
    # Results for verification
    baseline_metrics = Column(JSON) # e.g. {"accuracy": 0.58, "dataset_rows": 150000}
    
    # Metadata
    execution_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ReproducibilityRun(Base):
    __tablename__ = "reproducibility_runs"

    id = Column(Integer, primary_key=True, index=True)
    manifest_id = Column(String, index=True) # Links to ReproducibilityManifest.experiment_id
    run_type = Column(String) # 'ORIGINAL', 'CLEAN_ENV'
    status = Column(String) # 'PASSED', 'FAILED', 'TOLERANCE_WARNING'
    
    # Execution Environment
    execution_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    environment_diff = Column(JSON)
    
    # Results
    generated_metrics = Column(JSON)
    absolute_differences = Column(JSON)
