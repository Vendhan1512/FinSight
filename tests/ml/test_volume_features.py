import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.volume.engine import VolumeFeatureEngine

def test_negative_volume_aborts():
    dates = pd.date_range(start="2023-01-01", periods=3, freq='D')
    df = pd.DataFrame({
        "original_timestamp": dates,
        "volume": [1000, -500, 1000], # Negative volume is physically impossible
        "close": [10, 11, 12],
        "high": [10, 11, 12],
        "low": [9, 10, 11]
    })
    
    engine = VolumeFeatureEngine()
    
    with pytest.raises(ValueError, match="Data integrity validation failed"):
        engine.calculate_features(df)

def test_invalid_ohlc_aborts():
    dates = pd.date_range(start="2023-01-01", periods=3, freq='D')
    df = pd.DataFrame({
        "original_timestamp": dates,
        "volume": [1000, 500, 1000],
        "close": [10, 11, 12],
        "high": [10, 10, 12], # High is LESS than low on row 1
        "low": [9, 11, 11]
    })
    
    engine = VolumeFeatureEngine()
    
    with pytest.raises(ValueError, match="Data integrity validation failed"):
        engine.calculate_features(df)

def test_obv_calculation():
    dates = pd.date_range(start="2023-01-01", periods=4, freq='D')
    df = pd.DataFrame({
        "original_timestamp": dates,
        "volume": [100, 200, 150, 300],
        "close": [10, 11, 10, 12], # Up, Down, Up
        "high": [10, 12, 11, 13],
        "low": [9, 10, 9, 11]
    })
    
    engine = VolumeFeatureEngine()
    features = engine.calculate_features(df)
    
    # OBV Logic:
    # Row 0: NaN (no prior close) -> filled with 0 * vol = 0
    # Row 1: Close (11) > Prior (10) -> +200. Total = 200
    # Row 2: Close (10) < Prior (11) -> -150. Total = 50
    # Row 3: Close (12) > Prior (10) -> +300. Total = 350
    
    assert features.loc[1, "obv"] == 200
    assert features.loc[2, "obv"] == 50
    assert features.loc[3, "obv"] == 350

def test_vwap_is_skipped():
    dates = pd.date_range(start="2023-01-01", periods=3, freq='D')
    df = pd.DataFrame({
        "original_timestamp": dates,
        "volume": [1000, 500, 1000],
        "close": [10, 11, 12],
        "high": [11, 12, 13],
        "low": [9, 10, 11]
    })
    
    engine = VolumeFeatureEngine()
    features = engine.calculate_features(df)
    
    # The dataframe should NOT contain vwap_intraday because it is marked Unavailable
    assert "vwap_intraday" not in features.columns
    assert "obv" in features.columns
