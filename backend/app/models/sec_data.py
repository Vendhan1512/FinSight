import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, Numeric, Boolean, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class SECFiling(Base):
    __tablename__ = "sec_filings"

    accession_number = Column(String, primary_key=True)
    cik = Column(String, nullable=False, index=True)
    form_type = Column(String, nullable=False)
    filing_date = Column(Date, nullable=False, index=True)
    amended = Column(Boolean, default=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class SECFinancialFact(Base):
    __tablename__ = "sec_financial_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cik = Column(String, nullable=False, index=True)
    concept = Column(String, nullable=False, index=True)
    taxonomy = Column(String, nullable=False)
    metric = Column(String, nullable=False, index=True)
    unit = Column(String, nullable=False)
    value = Column(Numeric, nullable=False)
    
    start_date = Column(Date, nullable=True) # Null for point-in-time metrics
    end_date = Column(Date, nullable=False)
    
    fiscal_period = Column(String, nullable=True) # e.g. FY, Q1, Q2, Q3
    fiscal_year = Column(Integer, nullable=True)
    
    accession_number = Column(String, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('cik', 'concept', 'end_date', 'accession_number', name='uix_sec_fact'),
    )
