import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class FredSeries(Base):
    __tablename__ = "fred_series"

    id = Column(String, primary_key=True)  # e.g., 'FEDFUNDS'
    title = Column(String, nullable=False)
    frequency = Column(String, nullable=True)
    units = Column(String, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FredObservation(Base):
    __tablename__ = "fred_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(String, nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    value = Column(Numeric, nullable=True)  # Nullable because FRED returns '.' for missing
    
    realtime_start = Column(Date, nullable=False)
    realtime_end = Column(Date, nullable=False)
    
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('series_id', 'observation_date', 'realtime_start', name='uix_fred_obs'),
    )
