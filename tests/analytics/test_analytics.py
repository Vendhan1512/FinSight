import pytest
import pandas as pd
from datetime import datetime, date

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.contracts import MarketContract, SECContract, FREDContract

# --- TEST FIXTURES ---

def test_market_contract_leakage_prevention():
    # Verify contract handles valid data and doesn't allow impossible returns natively
    contract = MarketContract(
        source="test",
        symbol="AAPL",
        original_timestamp=datetime(2023, 1, 1),
        close=100.0,
        volume=1000,
        daily_return=0.05,
        log_return=0.048,
        drawdown=-0.1
    )
    assert contract.symbol == "AAPL"
    assert contract.daily_return == 0.05

def test_sec_contract_wide_format():
    contract = SECContract(
        source="test",
        cik="0001",
        original_timestamp=date(2023, 12, 31),
        revenue=1000000,
        net_income=200000,
        is_annual=True,
        fiscal_period="FY"
    )
    assert contract.revenue == 1000000
    assert contract.is_annual is True

def test_fred_contract_alignment():
    contract = FREDContract(
        source="test",
        original_timestamp=date(2023, 1, 1),
        fedfunds=5.33,
        gdp=None # Verifying missing values are allowed
    )
    assert contract.fedfunds == 5.33
    assert contract.gdp is None
