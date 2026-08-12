from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class AnalyticalContractBase(BaseModel):
    source: str = Field(..., description="The original data provider (e.g. 'alpha_vantage')")
    transformation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    dataset_version: str = Field(default="v1.0")

class MarketContract(AnalyticalContractBase):
    symbol: str
    original_timestamp: datetime
    
    close: float
    volume: int
    
    daily_return: Optional[float] = None
    log_return: Optional[float] = None
    rolling_7d_volume: Optional[float] = None
    rolling_30d_volume: Optional[float] = None
    drawdown: Optional[float] = None

class SECContract(AnalyticalContractBase):
    cik: str
    original_timestamp: date
    
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    operating_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    
    fiscal_period: Optional[str] = None
    is_annual: bool

class FREDContract(AnalyticalContractBase):
    original_timestamp: date
    
    fedfunds: Optional[float] = None
    cpiaucsl: Optional[float] = None
    unrate: Optional[float] = None
    gdp: Optional[float] = None
    gs10: Optional[float] = None
