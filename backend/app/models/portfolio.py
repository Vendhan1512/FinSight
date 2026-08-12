import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

# Import the Base from the existing schema to attach to the same metadata
from app.models.base import Base

class Portfolio(Base):
    """
    Configuration for a tracked portfolio.
    """
    __tablename__ = "portfolios"
    
    portfolio_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    
    benchmark_id = Column(String, nullable=True) # e.g., 'SPY'
    currency = Column(String, nullable=False, default="USD")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    compositions = relationship("PortfolioComposition", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioComposition(Base):
    """
    Tracks the historical weights of a portfolio.
    Using effective_date allows the portfolio to be historically rebalanced 
    without assuming constant weights.
    """
    __tablename__ = "portfolio_compositions"
    
    composition_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.portfolio_id"), nullable=False)
    
    entity_id = Column(String, nullable=False, index=True) # e.g., 'AAPL'
    weight = Column(Float, nullable=False)
    
    effective_date = Column(DateTime, nullable=False, index=True)
    
    portfolio = relationship("Portfolio", back_populates="compositions")
