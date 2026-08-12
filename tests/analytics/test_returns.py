import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.statistics.returns import ReturnsAndVolatilityEngine

# --- DETERMINISTIC MATHEMATICAL FIXTURES ---

@pytest.fixture
def mock_price_data():
    """
    Creates a deterministic time-series where:
    Day 1: 100
    Day 2: 110 (10% return)
    Day 3: 99  (-10% return from 110)
    Day 4: 99  (0% return)
    """
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(4)]
    prices = [100.0, 110.0, 99.0, 99.0]
    return pd.DataFrame({"timestamp": dates, "close": prices})

def test_mathematical_returns(mock_price_data):
    engine = ReturnsAndVolatilityEngine(trading_days_per_year=252)
    stats = engine.compute_all_statistics(mock_price_data, rolling_windows=[2])
    
    # Cumulative Return from 100 to 99 is exactly -1% (-0.01)
    assert np.isclose(stats["cumulative_return"], -0.01)

def test_maximum_drawdown(mock_price_data):
    # Peak is 110. Trough is 99.
    # MDD = (99 - 110) / 110 = -11 / 110 = -0.1
    engine = ReturnsAndVolatilityEngine()
    stats = engine.compute_all_statistics(mock_price_data, rolling_windows=[2])
    
    assert np.isclose(stats["max_drawdown"], -0.1)
    
    # Duration: peak at index 1 (Day 2), trough at index 2 (Day 3). Duration = 1 observation.
    assert stats["max_drawdown_duration_obs"] == 1

def test_data_integrity_validation():
    engine = ReturnsAndVolatilityEngine()
    
    # Test Negative Price Rejection
    bad_df = pd.DataFrame({
        "timestamp": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        "close": [100.0, -50.0]
    })
    
    with pytest.raises(ValueError, match="Zero or negative 'close' prices detected"):
        engine.compute_all_statistics(bad_df)
        
    # Test Duplicate Dates
    dup_df = pd.DataFrame({
        "timestamp": [datetime(2023, 1, 1), datetime(2023, 1, 1)],
        "close": [100.0, 105.0]
    })
    
    with pytest.raises(ValueError, match="Duplicate timestamps"):
        engine.compute_all_statistics(dup_df)
