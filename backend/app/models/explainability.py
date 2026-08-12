import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class LocalExplanation(Base):
    """
    Stores SHAP local explanations for individual predictions.
    """
    __tablename__ = "local_explanations"
    
    explanation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("model_predictions.prediction_id"), nullable=False, index=True)
    
    model_version = Column(String, nullable=False, index=True)
    feature_version = Column(String, nullable=False)
    
    base_value = Column(Float, nullable=False)
    prediction_value = Column(Float, nullable=False)
    
    # Store all features and their SHAP values as a JSON dict: {"feature_A": 0.05, "feature_B": -0.01}
    # This prevents storing millions of rows if flattened.
    shap_values = Column(JSON, nullable=False)
    
    calculation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class GlobalImportance(Base):
    """
    Stores aggregated global feature importances for a model.
    """
    __tablename__ = "global_importances"
    
    importance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String, nullable=False, index=True)
    
    methodology = Column(String, nullable=False) # 'SHAP_MEAN_ABS', 'PERMUTATION', 'MODEL_NATIVE'
    feature_name = Column(String, nullable=False, index=True)
    
    importance_value = Column(Float, nullable=False)
    importance_std = Column(Float, nullable=True) # Used for Permutation importance
    
    dataset_period = Column(String, nullable=False) # e.g. 'VALIDATION', 'TEST', 'FOLD_1'
    calculation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class TemporalStability(Base):
    """
    Stores evaluations of a feature's importance stability across time (walk-forward folds).
    """
    __tablename__ = "temporal_stability"
    
    stability_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String, nullable=False, index=True)
    
    feature_name = Column(String, nullable=False, index=True)
    
    stability_score = Column(Float, nullable=False) # Metric of variance across folds
    is_regime_dependent = Column(Boolean, nullable=False) # True if importance fluctuates wildly but predictably
    stability_classification = Column(String, nullable=False) # 'STABLE', 'UNSTABLE', 'REGIME_DEPENDENT'
    
    calculation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
