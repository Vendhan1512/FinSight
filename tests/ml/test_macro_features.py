import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.macro.engine import MacroFeatureEngine

def test_alfred_vintage_alignment():
    # 1. Market Calendar (Daily)
    # We want to predict on Jan 15th and Jan 25th
    market_df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-15"), pd.to_datetime("2023-01-25")]
    })
    
    # 2. Macro Data (ALFRED format)
    # Observation is for "December CPI".
    # Advance estimate is released Jan 10.
    # Revised estimate is released Jan 20.
    cpi_df = pd.DataFrame({
        "observation_date": [pd.to_datetime("2022-12-01"), pd.to_datetime("2022-12-01")],
        "realtime_start": [pd.to_datetime("2023-01-10"), pd.to_datetime("2023-01-20")],
        "value": [290.0, 295.0] # Advance is 290, Revised is 295
    })
    
    macro_dfs = {"CPIAUCSL": cpi_df}
    
    engine = MacroFeatureEngine()
    features = engine.calculate_features(market_df, macro_dfs)
    
    # Assertions:
    # On Jan 15, the model must ONLY see the Advance Estimate (290), because the Revision (295) wasn't out yet.
    assert features.iloc[0]["cpi_level"] == 290.0
    
    # On Jan 25, the model should see the Revised Estimate (295).
    assert features.iloc[1]["cpi_level"] == 295.0

def test_spread_calculation():
    market_df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-01")]
    })
    
    gs10_df = pd.DataFrame({
        "observation_date": [pd.to_datetime("2023-01-01")],
        "realtime_start": [pd.to_datetime("2023-01-01")],
        "value": [4.5]
    })
    
    ff_df = pd.DataFrame({
        "observation_date": [pd.to_datetime("2023-01-01")],
        "realtime_start": [pd.to_datetime("2023-01-01")],
        "value": [3.0]
    })
    
    macro_dfs = {"GS10": gs10_df, "FEDFUNDS": ff_df}
    
    engine = MacroFeatureEngine()
    features = engine.calculate_features(market_df, macro_dfs)
    
    # Spread should be 4.5 - 3.0 = 1.5
    assert features.iloc[0]["spread_10y_ff"] == 1.5
