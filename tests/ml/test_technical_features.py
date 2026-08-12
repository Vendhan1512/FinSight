import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.technical.engine import TechnicalFeatureEngine

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2023-01-01", periods=260, freq='D')
    
    # Create deterministic prices starting at 100, rising by 1 every day
    prices = np.linspace(100, 359, 260)
    
    df = pd.DataFrame({
        "original_timestamp": dates,
        "adjusted_close": prices,
        "close": prices # Not used by engine, but usually present
    })
    return df

def test_engine_missing_lookback(mock_market_data):
    engine = TechnicalFeatureEngine()
    features = engine.calculate_features(mock_market_data)
    
    # 200d SMA should explicitly be NaN for the first 199 rows
    assert pd.isna(features.loc[0, "sma_200d"])
    assert pd.isna(features.loc[198, "sma_200d"])
    
    # The 200th row (index 199) should be the first valid observation
    assert not pd.isna(features.loc[199, "sma_200d"])
    
def test_engine_momentum_calculation(mock_market_data):
    engine = TechnicalFeatureEngine()
    features = engine.calculate_features(mock_market_data)
    
    # Price rises by exactly 1 every day.
    # Therefore, 20-day momentum (Price_t - Price_t-20) must equal exactly 20.
    mom_20 = features.loc[20, "mom_20d"]
    assert np.isclose(mom_20, 20.0)

def test_engine_return_calculation(mock_market_data):
    engine = TechnicalFeatureEngine()
    features = engine.calculate_features(mock_market_data)
    
    # Day 0: Price = 100
    # Day 1: Price = 101
    # 1-day return = (101/100) - 1 = 0.01
    ret_1d = features.loc[1, "ret_1d"]
    assert np.isclose(ret_1d, 0.01)
    
    # Log Return = ln(101/100) = 0.00995033
    log_ret_1d = features.loc[1, "log_ret_1d"]
    assert np.isclose(log_ret_1d, np.log(101/100))
