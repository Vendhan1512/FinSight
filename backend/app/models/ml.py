import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class SupervisedDataset(Base):
    """Configuration and metadata for a specific machine learning dataset build."""
    __tablename__ = "supervised_datasets"
    
    dataset_version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_name = Column(String, nullable=False, index=True) # e.g. "baseline_classification_v1"
    
    target_type = Column(String, nullable=False) # 'regression_return', 'classification_direction'
    target_horizon = Column(String, nullable=False) # '5d', '20d'
    
    # Chronological Boundaries
    train_start = Column(DateTime, nullable=True)
    train_end = Column(DateTime, nullable=False)
    val_start = Column(DateTime, nullable=False)
    val_end = Column(DateTime, nullable=False)
    test_start = Column(DateTime, nullable=False)
    test_end = Column(DateTime, nullable=True)
    
    # Lineage back to the Phase 3 Feature Run
    feature_run_id = Column(UUID(as_uuid=True), ForeignKey("feature_runs.run_id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    observations = relationship("DatasetObservation", back_populates="dataset", cascade="all, delete-orphan")


class DatasetObservation(Base):
    """The physical training/validation/test rows for the ML model."""
    __tablename__ = "dataset_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("supervised_datasets.dataset_version_id"), nullable=False)
    
    entity_id = Column(String, nullable=False, index=True)
    partition = Column(String, nullable=False, index=True) # 'TRAIN', 'VALIDATION', 'TEST'
    
    # Temporal anchors (Strict separation required by prompt)
    prediction_time = Column(DateTime, nullable=False, index=True) # Timestamp of the features (T)
    target_end_time = Column(DateTime, nullable=False) # Timestamp the target was realized (T + h)
    
    # Target label
    target_value = Column(Float, nullable=False) 
    
    dataset = relationship("SupervisedDataset", back_populates="observations")


class ExperimentRun(Base):
    """Tracks every machine learning model trained against a specific dataset."""
    __tablename__ = "experiment_runs"
    
    experiment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False, index=True) # e.g., 'RidgeRegression', 'RandomForestClassifier'
    
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("supervised_datasets.dataset_version_id"), nullable=False)
    feature_set_version = Column(String, nullable=False)
    
    hyperparameters = Column(JSON, nullable=False)
    
    training_period = Column(String, nullable=False)
    validation_period = Column(String, nullable=False)
    
    execution_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, nullable=False) # 'COMPLETED', 'FAILED'
    git_version = Column(String, nullable=True)
    
    metrics = relationship("ModelMetrics", back_populates="experiment", cascade="all, delete-orphan")


class ModelMetrics(Base):
    """Stores detailed evaluation metrics for a specific experiment and partition."""
    __tablename__ = "model_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.experiment_id"), nullable=False)
    
    partition = Column(String, nullable=False, index=True) # 'VALIDATION', 'TEST'
    
    metric_name = Column(String, nullable=False) # e.g., 'RMSE', 'F1', 'ROC_AUC'
    metric_value = Column(Float, nullable=False)
    beats_baseline = Column(Boolean, nullable=True) # Explicitly flag if it beat the baseline model
    
    experiment = relationship("ExperimentRun", back_populates="metrics")


class OptimizationRun(Base):
    """Tracks a full Hyperparameter Optimization Study (e.g. Optuna)."""
    __tablename__ = "optimization_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False, index=True)
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("supervised_datasets.dataset_version_id"), nullable=False)
    
    objective_metric = Column(String, nullable=False) # e.g., 'RMSE', 'PR_AUC'
    target_direction = Column(String, nullable=False) # 'minimize', 'maximize'
    
    n_trials = Column(Integer, nullable=False)
    cv_folds = Column(Integer, nullable=False)
    cv_gap = Column(Integer, nullable=False) # Embargo days
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    trials = relationship("OptimizationTrial", back_populates="run", cascade="all, delete-orphan")


class OptimizationTrial(Base):
    """Tracks a single configuration iteration within an OptimizationRun."""
    __tablename__ = "optimization_trials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("optimization_runs.id"), nullable=False)
    
    trial_number = Column(Integer, nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    
    validation_metric_value = Column(Float, nullable=False) # The average CV score for the objective
    fold_results = Column(JSON, nullable=True) # E.g., [0.85, 0.82, 0.88]
    
    execution_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    run = relationship("OptimizationRun", back_populates="trials")


class WalkForwardRun(Base):
    """Tracks a complete walk-forward evaluation (rolling or expanding)."""
    __tablename__ = "walk_forward_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False, index=True)
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("supervised_datasets.dataset_version_id"), nullable=False)
    
    mode = Column(String, nullable=False) # 'rolling', 'expanding'
    gap = Column(Integer, nullable=False)
    step_size = Column(Integer, nullable=False)
    
    overall_metrics = Column(JSON, nullable=True) # Aggregated metrics across all folds
    status = Column(String, nullable=False) # 'COMPLETED', 'FAILED'
    execution_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    folds = relationship("WalkForwardFold", back_populates="run", cascade="all, delete-orphan")


class WalkForwardFold(Base):
    """Tracks an individual evaluation fold within a walk-forward run."""
    __tablename__ = "walk_forward_folds"
    
    fold_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("walk_forward_runs.run_id"), nullable=False)
    fold_index = Column(Integer, nullable=False)
    
    train_start = Column(DateTime, nullable=False)
    train_end = Column(DateTime, nullable=False)
    test_start = Column(DateTime, nullable=False)
    test_end = Column(DateTime, nullable=False)
    
    fold_metrics = Column(JSON, nullable=False) # The out-of-sample metrics for this specific fold
    
    run = relationship("WalkForwardRun", back_populates="folds")
    predictions = relationship("ModelPrediction", back_populates="fold", cascade="all, delete-orphan")


class ModelPrediction(Base):
    """The physical ledger of every single out-of-sample prediction generated by the engine."""
    __tablename__ = "model_predictions"
    
    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, nullable=False, index=True) # Symbol
    prediction_time = Column(DateTime, nullable=False, index=True) # T
    
    model_name = Column(String, nullable=False, index=True)
    fold_id = Column(UUID(as_uuid=True), ForeignKey("walk_forward_folds.fold_id"), nullable=False)
    
    prediction = Column(Float, nullable=False)
    prediction_prob = Column(Float, nullable=True) # If classification
    actual_outcome = Column(Float, nullable=False)
    
    fold = relationship("WalkForwardFold", back_populates="predictions")


class RegisteredModel(Base):
    """The formal Model Registry."""
    __tablename__ = "registered_models"
    
    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False, index=True)
    
    experiment_run_id = Column(UUID(as_uuid=True), ForeignKey("experiment_runs.experiment_id"), nullable=False)
    
    # Strictly enforced statuses: EXPERIMENTAL -> VALIDATED -> CANDIDATE -> PRODUCTION
    status = Column(String, nullable=False, default="EXPERIMENTAL")
    
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    experiment = relationship("ExperimentRun")
    model_card = relationship("ModelCard", back_populates="model", uselist=False, cascade="all, delete-orphan")


class ModelCard(Base):
    """The exhaustive metadata payload for a RegisteredModel."""
    __tablename__ = "model_cards"
    
    card_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("registered_models.model_id"), nullable=False, unique=True)
    
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    model = relationship("RegisteredModel", back_populates="model_card")
