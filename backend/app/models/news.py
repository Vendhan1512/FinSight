import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class NewsSource(Base):
    __tablename__ = "news_sources"
    
    source_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    article_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False, index=True) # e.g., 'newsapi'
    provider_article_id = Column(String, nullable=True, unique=True)
    
    source_id = Column(String, nullable=True)
    source_name = Column(String, nullable=True)
    author = Column(String, nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    content = Column(String, nullable=True) # Will store truncated indicator if truncated
    url = Column(String, nullable=False, index=True) # Canonical URL
    
    published_at = Column(DateTime, nullable=False, index=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    language = Column(String, nullable=True)
    query_used = Column(String, nullable=True)
    
    content_hash = Column(String, nullable=False, index=True) # SHA256 of (title, url, source)
    
    raw_response_reference = Column(String, nullable=True) # e.g. path to S3 raw json

class NewsArticleDuplicate(Base):
    __tablename__ = "news_article_duplicates"
    
    id = Column(Integer, primary_key=True, index=True)
    canonical_article_id = Column(UUID(as_uuid=True), ForeignKey("news_articles.article_id"), nullable=False)
    duplicate_article_id = Column(String, nullable=False) # e.g. the URL or raw ID of the rejected duplicate
    decision_reason = Column(String, nullable=False) # e.g. "Identical content_hash"
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NewsIngestionRun(Base):
    __tablename__ = "news_ingestion_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    query = Column(String, nullable=False)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    records_requested = Column(Integer, default=0)
    records_received = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    status = Column(String, nullable=False, default="RUNNING") # RUNNING, COMPLETED, FAILED
    error_message = Column(String, nullable=True)
