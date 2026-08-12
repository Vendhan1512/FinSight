import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, BigInteger, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base_class import Base

class MarketDataRaw(Base):
    __tablename__ = "market_data_raw"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    raw_payload = Column(JSONB, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class MarketDataNormalized(Base):
    __tablename__ = "market_data_normalized"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    source_type = Column(String, nullable=False)  # e.g., 'historical', 'delayed'
    provider = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'provider', name='uix_symbol_timestamp_provider'),
    )
