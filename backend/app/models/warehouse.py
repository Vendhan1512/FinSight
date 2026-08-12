import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, Numeric, Boolean, Integer, UniqueConstraint, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(String, primary_key=True) # e.g. "alpha_vantage", "sec_edgar"
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False) # e.g. "running", "completed", "failed"
    records_processed = Column(Integer, default=0)

class DataQualityResult(Base):
    __tablename__ = "data_quality_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False)
    check_type = Column(String, nullable=False)
    passed = Column(Boolean, nullable=False)
    details = Column(JSONB, nullable=True)

class SECCompany(Base):
    __tablename__ = "sec_companies"
    cik = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=True, index=True)

class MarketAsset(Base):
    __tablename__ = "market_assets"
    symbol = Column(String, primary_key=True)
    asset_type = Column(String, nullable=False) # e.g. "equity"
    name = Column(String, nullable=False)
    cik = Column(String, ForeignKey("sec_companies.cik"), nullable=True)

class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, ForeignKey("market_assets.symbol"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(BigInteger, nullable=False)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'source_id', name='uix_market_price'),
    )

class SECFiling(Base):
    __tablename__ = "sec_filings"
    accession_number = Column(String, primary_key=True)
    cik = Column(String, ForeignKey("sec_companies.cik"), nullable=False, index=True)
    form_type = Column(String, nullable=False)
    filing_date = Column(Date, nullable=False, index=True)
    amended = Column(Boolean, default=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FinancialFact(Base):
    __tablename__ = "financial_facts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    accession_number = Column(String, ForeignKey("sec_filings.accession_number"), nullable=False, index=True)
    metric = Column(String, nullable=False, index=True)
    concept = Column(String, nullable=False)
    value = Column(Numeric, nullable=False)
    unit = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=False, index=True)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('accession_number', 'concept', 'end_date', name='uix_financial_fact'),
    )

class EconomicSeries(Base):
    __tablename__ = "economic_series"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    frequency = Column(String, nullable=True)
    units = Column(String, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EconomicObservation(Base):
    __tablename__ = "economic_observations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(String, ForeignKey("economic_series.id"), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    value = Column(Numeric, nullable=True)
    realtime_start = Column(Date, nullable=False)
    realtime_end = Column(Date, nullable=False)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('series_id', 'observation_date', 'realtime_start', name='uix_economic_obs'),
    )

# --- ANALYTICAL DATA LAYER MODELS ---

class AnalyticalMarket(Base):
    __tablename__ = "analytical_market"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    original_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Core Data
    close = Column(Numeric, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Analytical Features
    daily_return = Column(Numeric, nullable=True)
    log_return = Column(Numeric, nullable=True)
    rolling_7d_volume = Column(Numeric, nullable=True)
    rolling_30d_volume = Column(Numeric, nullable=True)
    drawdown = Column(Numeric, nullable=True)
    
    # Provenance
    source = Column(String, nullable=False)
    transformation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    dataset_version = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('symbol', 'original_timestamp', 'dataset_version', name='uix_analytical_market'),
    )

class AnalyticalSEC(Base):
    __tablename__ = "analytical_sec"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cik = Column(String, nullable=False, index=True)
    original_timestamp = Column(Date, nullable=False, index=True) # Usually the end_date of the reporting period
    
    # Analytical Features (Wide Format)
    revenue = Column(Numeric, nullable=True)
    net_income = Column(Numeric, nullable=True)
    operating_income = Column(Numeric, nullable=True)
    total_assets = Column(Numeric, nullable=True)
    total_liabilities = Column(Numeric, nullable=True)
    cash_and_equivalents = Column(Numeric, nullable=True)
    long_term_debt = Column(Numeric, nullable=True)
    shareholders_equity = Column(Numeric, nullable=True)
    
    # Metadata
    fiscal_period = Column(String, nullable=True) # e.g. FY, Q1
    is_annual = Column(Boolean, nullable=False)
    
    # Provenance
    source = Column(String, nullable=False)
    transformation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    dataset_version = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('cik', 'original_timestamp', 'dataset_version', name='uix_analytical_sec'),
    )

class AnalyticalFRED(Base):
    __tablename__ = "analytical_fred"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_timestamp = Column(Date, nullable=False, index=True)
    
    # Aligned Features
    fedfunds = Column(Numeric, nullable=True)
    cpiaucsl = Column(Numeric, nullable=True)
    unrate = Column(Numeric, nullable=True)
    gdp = Column(Numeric, nullable=True)
    gs10 = Column(Numeric, nullable=True)
    
    # Provenance
    source = Column(String, nullable=False)
    transformation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    dataset_version = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('original_timestamp', 'dataset_version', name='uix_analytical_fred'),
    )

# --- STATISTICAL INTELLIGENCE MODELS ---

class StatisticalExperiment(Base):
    __tablename__ = "statistical_experiments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_name = Column(String, nullable=False, index=True)
    
    # Definition
    research_question = Column(String, nullable=False)
    hypothesis_h0 = Column(String, nullable=False)
    hypothesis_h1 = Column(String, nullable=False)
    
    # Data Details
    dataset_version = Column(String, nullable=False)
    sample_a_size = Column(Integer, nullable=False)
    sample_b_size = Column(Integer, nullable=False)
    
    # Testing
    test_used = Column(String, nullable=False)
    p_value = Column(Float, nullable=False)
    alpha = Column(Float, nullable=False, default=0.05)
    is_significant = Column(Boolean, nullable=False)
    
    # Effect Size & Economics
    effect_size_metric = Column(String, nullable=False)
    effect_size_value = Column(Float, nullable=False)
    is_economically_significant = Column(Boolean, nullable=False)
    
    # Provenance
    execution_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
