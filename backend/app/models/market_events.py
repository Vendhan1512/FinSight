import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class NewsMarketEvent(Base):
    """
    Stores aligned events joining news publications with subsequent market behavior.
    """
    __tablename__ = "news_market_events"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.article_id"), nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True) # Usually the ticker
    
    published_at = Column(DateTime, nullable=False)
    market_session_relation = Column(String, nullable=False) # PRE_MARKET, INTRADAY, POST_MARKET, WEEKEND_HOLIDAY
    
    sentiment = Column(String, nullable=True) # Inherited from NewsArticleSentiment
    topic = Column(String, nullable=True)     # Inherited from NewsArticleTopic
    
    # Timing of the market observations
    market_observation_start = Column(DateTime, nullable=False)
    market_observation_end = Column(DateTime, nullable=False)
    
    # Horizon e.g. "1d", "5d", "20d"
    horizon = Column(String, nullable=False)
    
    # Market Metrics
    future_return = Column(Float, nullable=True)
    future_volatility = Column(Float, nullable=True)
    
    # Abnormal Return specifics
    benchmark_id = Column(String, nullable=True)
    benchmark_return = Column(Float, nullable=True)
    abnormal_return = Column(Float, nullable=True)
    
    # Storage of methodology metadata
    methodology_version = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class StatisticalRelationship(Base):
    """
    Stores the results of statistical tests between news features and market returns.
    """
    __tablename__ = "statistical_relationships"
    
    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    test_type = Column(String, nullable=False) # e.g. "sentiment_vs_return", "topic_vs_return"
    horizon = Column(String, nullable=False)
    
    sample_size = Column(Integer, nullable=False)
    
    # Stats
    coefficient = Column(Float, nullable=True) # Correlation or regression beta
    p_value = Column(Float, nullable=True)
    adjusted_p_value = Column(Float, nullable=True) # After multiple testing correction
    
    # Confidence Interval
    ci_lower = Column(Float, nullable=True)
    ci_upper = Column(Float, nullable=True)
    
    effect_size = Column(Float, nullable=True)
    
    # Metadata
    methodology = Column(String, nullable=False) # e.g. "pearson", "spearman"
    multiple_testing_correction = Column(String, nullable=True) # e.g. "bh_fdr"
    
    # Descriptive language
    finding_description = Column(String, nullable=False) # Enforced non-causal language
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
