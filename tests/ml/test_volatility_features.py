import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.volatility.engine import VolatilityAndRiskEngine

@pytest.fixture
def mock_risk_data():
    dates = pd.date_range(start="2023-01-01", periods=260, freq='D')
    
    # Asset A returns a perfectly constant 1% every day
    asset_returns = np.full(260, 0.01)
    # Benchmark returns a perfectly constant 0.5% every day
    bench_returns = np.full(260, 0.005)
    
    asset_df = pd.DataFrame({
        "original_timestamp": dates,
        "log_return": asset_returns,
        "adjusted_close": np.exp(np.cumsum(asset_returns)) * 100
    })
    
    bench_df = pd.DataFrame({
        "original_timestamp": dates,
        "log_return": bench_returns
    })
    
    # RFR is a constant 0.25% daily
    rfr_df = pd.DataFrame({
        "original_timestamp": dates,
        "rfr_daily": np.full(260, 0.0025)
    })
    
    return asset_df, bench_df, rfr_df

def test_engine_missing_lookback(mock_risk_data):
    asset_df, _, _ = mock_risk_data
    engine = VolatilityAndRiskEngine()
    features = engine.calculate_features(asset_df)
    
    # 252d volatility should explicitly be NaN for the first 251 rows
    assert pd.isna(features.loc[0, "vol_252d"])
    assert pd.isna(features.loc[250, "vol_252d"])
    
    # The 252nd row (index 251) should be the first valid observation
    assert not pd.isna(features.loc[251, "vol_252d"])

def test_sharpe_ratio_calculation(mock_risk_data):
    asset_df, bench_df, rfr_df = mock_risk_data
    engine = VolatilityAndRiskEngine()
    
    # Inject some noise so std is not 0 (Sharpe requires division by std)
    np.random.seed(42)
    asset_df["log_return"] = asset_df["log_return"] + np.random.normal(0, 0.001, 260)
    
    features = engine.calculate_features(asset_df, bench_df, rfr_df)
    
    # Extract the last row which has full lookback
    row = features.iloc[-1]
    
    assert not pd.isna(row["sharpe_252d"])
    assert row["sharpe_252d"] > 0 # Asset returned ~1%, RFR is 0.25%, Sharpe should be positive

def test_var_calculation(mock_risk_data):
    asset_df, _, _ = mock_risk_data
    engine = VolatilityAndRiskEngine()
    
    # Inject a known distribution
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, 260)
    asset_df["log_return"] = returns
    
    features = engine.calculate_features(asset_df)
    row = features.iloc[-1]
    
    # 95% VaR should be negative and approximately around the 5th percentile of the normal distribution
    assert not pd.isna(row["var_95_252d"])
    assert row["var_95_252d"] < 0
    
    # CVaR (Expected Shortfall) should be strictly more negative than VaR
    assert row["cvar_95_252d"] < row["var_95_252d"]
