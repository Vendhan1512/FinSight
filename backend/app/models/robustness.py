from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RobustnessAssetMetrics(Base):
    __tablename__ = "robustness_asset_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True)
    entity_id = Column(String, index=True)
    sector = Column(String)
    sample_size = Column(Integer)
    prediction_count = Column(Integer)
    accuracy = Column(Float)
    f1_score = Column(Float)
    missingness_pct = Column(Float)
    status = Column(String) # "STABLE", "UNSTABLE"

    __table_args__ = (
        Index("ix_rob_asset_exp_ent", "experiment_id", "entity_id"),
    )

class RobustnessTimeMetrics(Base):
    __tablename__ = "robustness_time_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    accuracy = Column(Float)
    f1_score = Column(Float)
    is_best_period = Column(Integer)  # 0 or 1
    is_worst_period = Column(Integer) # 0 or 1
    beats_baseline = Column(Integer)  # 0 or 1

class RobustnessRegimeMetrics(Base):
    __tablename__ = "robustness_regime_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True)
    regime_label = Column(String, index=True) # e.g. "Regime_LowVol_PosRet"
    methodology_version = Column(String)
    sample_size = Column(Integer)
    accuracy = Column(Float)
    f1_score = Column(Float)
    beats_baseline = Column(Integer)  # 0 or 1

class RobustnessAblationMetrics(Base):
    __tablename__ = "robustness_ablation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True)
    group_name = Column(String) # Group A, B, C, D, E
    feature_count = Column(Integer)
    mean_accuracy = Column(Float)
    mean_f1 = Column(Float)
    incremental_accuracy = Column(Float) # Compared to previous group
    is_stable = Column(Integer) # 1 if all folds beat baseline

class RobustnessAblationFoldMetrics(Base):
    __tablename__ = "robustness_ablation_fold_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True)
    group_name = Column(String)
    fold_index = Column(Integer)
    accuracy = Column(Float)
    baseline_accuracy = Column(Float)
    incremental_improvement = Column(Float) # Accuracy over previous group for this fold
