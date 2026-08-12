import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.statistics.macro import MacroeconomicEngine

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2023-01-01", periods=120, freq='D')
    # Generate daily market returns
    return pd.DataFrame({
        "original_timestamp": dates,
        "log_return": [0.01] * 120  # Constant 1% daily return
    })

@pytest.fixture
def mock_fred_raw():
    # Observation is Jan 1st.
    # But realtime_start (publication) is March 15th.
    return pd.DataFrame({
        "series_id": ["GDP"] * 2,
        "observation_date": [datetime(2023, 1, 1), datetime(2023, 2, 1)],
        "realtime_start": [datetime(2023, 3, 15), datetime(2023, 4, 15)],
        "value": [20000, 21000]
    })

def test_point_in_time_alignment(mock_market_data, mock_fred_raw):
    engine = MacroeconomicEngine()
    
    aligned = engine.align_point_in_time(mock_market_data, mock_fred_raw)
    
    # The first FRED publication is March 15. The resampler aggregates market to month-end (March 31).
    # The aligned DataFrame should start at March 31, NOT Jan 31.
    assert len(aligned) == 2
    
    first_index = aligned.index[0]
    assert first_index.month == 3 # Aligned to March, not January!
    
    # Market return for March should be the sum of daily returns in March.
    # March has 31 days. 31 * 0.01 = 0.31
    assert np.isclose(aligned["log_return"].iloc[0], 0.31)
    
    # The GDP value aligned to March should be 20000 (published in March)
    assert aligned["GDP"].iloc[0] == 20000

def test_lagged_correlations():
    engine = MacroeconomicEngine()
    # Mock aligned data where Market perfectly follows Macro exactly 1 month later
    # Macro: 1, 2, 3, 4, 5...
    # Market: 0, 1, 2, 3, 4... (Lag 1)
    aligned = pd.DataFrame({
        "macro": np.arange(1, 50),
        "log_return": np.arange(0, 49)
    })
    
    # Set to 1 lag only for test
    engine.lags_to_test = [1]
    
    report = engine.compute_lagged_correlations(aligned)
    
    assert not report.empty
    
    row = report.iloc[0]
    assert row["Lag_Months"] == 1
    # Perfect linear relationship at lag 1
    assert np.isclose(row["Pearson_r"], 1.0)
    
    # Check Bonferroni
    # 1 series * 1 lag = 1 test. alpha should be 0.05
    assert np.isclose(row["Bonferroni_Alpha"], 0.05)
