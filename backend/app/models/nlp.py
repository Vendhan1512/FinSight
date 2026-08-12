import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class NLPProcessingRun(Base):
    __tablename__ = "nlp_processing_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String, nullable=False, index=True)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    articles_processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    duration = Column(Float, nullable=True) # in seconds
    
class NewsArticleSentiment(Base):
    __tablename__ = "news_article_sentiment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.article_id"), nullable=False, index=True)
    
    sentiment_model = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    
    sentiment_label = Column(String, nullable=False) # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NewsArticleEntity(Base):
    __tablename__ = "news_article_entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.article_id"), nullable=False, index=True)
    
    canonical_entity_id = Column(String, nullable=True, index=True) # None if unresolved
    entity_type = Column(String, nullable=False) # ORG, PERSON, LOC, PRODUCT
    canonical_name = Column(String, nullable=False)
    
    aliases = Column(JSON, nullable=True) # List of exact text matches found
    ticker = Column(String, nullable=True, index=True)
    
    resolution_method = Column(String, nullable=False)
    resolution_confidence = Column(Float, nullable=True)
    
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NewsArticleTopic(Base):
    __tablename__ = "news_article_topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.article_id"), nullable=False, index=True)
    
    topic_name = Column(String, nullable=False, index=True)
    topic_score = Column(Float, nullable=True)
    
    model_version = Column(String, nullable=False)
    is_generated = Column(Boolean, default=False, nullable=False) # True if LLM-generated
    
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
