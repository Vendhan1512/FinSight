import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.statistics.correlation import CorrelationEngine

@pytest.fixture
def mock_market_dfs():
    dates = pd.date_range(start="2023-01-01", periods=60, freq='D')
    
    # AAPL: Perfectly linear returns
    aapl = pd.DataFrame({
        "original_timestamp": dates,
        "log_return": np.linspace(0.01, 0.60, 60)
    })
    
    # MSFT: Exactly opposite to AAPL
    msft = pd.DataFrame({
        "original_timestamp": dates,
        "log_return": np.linspace(-0.01, -0.60, 60)
    })
    
    return {"AAPL": aapl, "MSFT": msft}

@pytest.fixture
def mock_fred_df():
    # Two months of FRED data
    dates = [datetime(2023, 1, 1), datetime(2023, 2, 1)]
    return pd.DataFrame({
        "original_timestamp": dates,
        "FEDFUNDS": [4.0, 4.5]
    })

def test_pairwise_correlation(mock_market_dfs):
    engine = CorrelationEngine()
    engine.MIN_OBSERVATIONS = 10 # lower threshold for testing
    
    aligned = engine.align_market_data(mock_market_dfs)
    report = engine.compute_pairwise(aligned)
    
    # Extract the AAPL to MSFT correlation
    row = report[(report["Asset_A"] == "AAPL") & (report["Asset_B"] == "MSFT")].iloc[0]
    
    # Perfect negative linear correlation expected
    assert np.isclose(row["Pearson_r"], -1.0)
    assert np.isclose(row["Spearman_rho"], -1.0)
    assert row["Note"] == "Valid"

def test_missing_data_awareness(mock_market_dfs):
    # Only 5 observations overlapping
    engine = CorrelationEngine()
    engine.MIN_OBSERVATIONS = 30
    
    # Truncate MSFT to 5 days
    mock_market_dfs["MSFT"] = mock_market_dfs["MSFT"].head(5)
    
    aligned = engine.align_market_data(mock_market_dfs)
    report = engine.compute_pairwise(aligned)
    
    row = report[(report["Asset_A"] == "AAPL") & (report["Asset_B"] == "MSFT")].iloc[0]
    
    # Should flag Insufficient Data and set correlation to NaN
    assert row["Note"] == "Insufficient Data"
    assert pd.isna(row["Pearson_r"])

def test_multi_frequency_downsampling(mock_market_dfs, mock_fred_df):
    engine = CorrelationEngine()
    
    aligned_market = engine.align_market_data(mock_market_dfs)
    final_df = engine.align_market_with_fred(aligned_market, mock_fred_df)
    
    # Market data is daily (Jan and Feb). FRED is monthly (Jan 1, Feb 1).
    # final_df should have exactly 2 rows (End of Jan, End of Feb)
    assert len(final_df) == 2
    
    # The AAPL value for Jan should be the sum of daily log returns for January
    jan_returns = mock_market_dfs["AAPL"][mock_market_dfs["AAPL"]["original_timestamp"].dt.month == 1]["log_return"].sum()
    
    # Retrieve the joined AAPL value for Jan
    joined_jan_aapl = final_df["AAPL"].iloc[0]
    
    assert np.isclose(jan_returns, joined_jan_aapl)
    
    # The FRED value for Jan should exactly match the Jan 1 observation
    assert final_df["FEDFUNDS"].iloc[0] == 4.0
