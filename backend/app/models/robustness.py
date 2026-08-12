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
