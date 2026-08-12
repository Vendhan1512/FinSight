import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.cross_sectional.engine import CrossSectionalFeatureEngine

def test_cross_sectional_ranking():
    # Construct a deterministic panel for one date
    df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-01")] * 4,
        "symbol": ["A", "B", "C", "D"],
        "ret_1m": [0.05, 0.10, -0.05, 0.02]
    })
    
    # Sort order by return: C(-0.05), D(0.02), A(0.05), B(0.10)
    # Ranks (1-based): C=1, D=2, A=3, B=4
    # Percentiles (pct=True): C=0.25, D=0.50, A=0.75, B=1.00
    
    engine = CrossSectionalFeatureEngine(min_universe_size=3)
    features = engine.calculate_features(df)
    
    assert features.loc[features["symbol"] == "C", "return_1m_percentile"].values[0] == 0.25
    assert features.loc[features["symbol"] == "D", "return_1m_percentile"].values[0] == 0.50
    assert features.loc[features["symbol"] == "A", "return_1m_percentile"].values[0] == 0.75
    assert features.loc[features["symbol"] == "B", "return_1m_percentile"].values[0] == 1.00

def test_cross_sectional_ties():
    df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-01")] * 3,
        "symbol": ["A", "B", "C"],
        "ret_1m": [0.05, 0.05, -0.05]
    })
    
    # Sort order: C(-0.05), A(0.05), B(0.05)
    # Ranks: C=1. A and B tie for 2nd and 3rd. Average rank = 2.5
    # Percentiles: C = 1/3 (0.333), A and B = 2.5/3 (0.833)
    
    engine = CrossSectionalFeatureEngine(min_universe_size=3)
    features = engine.calculate_features(df)
    
    assert np.isclose(features.loc[features["symbol"] == "C", "return_1m_percentile"].values[0], 0.333333)
    assert np.isclose(features.loc[features["symbol"] == "A", "return_1m_percentile"].values[0], 0.833333)
    assert np.isclose(features.loc[features["symbol"] == "B", "return_1m_percentile"].values[0], 0.833333)

def test_minimum_universe_threshold():
    # Only 2 assets, but minimum threshold is 3
    df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-01")] * 2,
        "symbol": ["A", "B"],
        "ret_1m": [0.05, 0.10]
    })
    
    engine = CrossSectionalFeatureEngine(min_universe_size=3)
    features = engine.calculate_features(df)
    
    # Ranks should be NaN because threshold was not met
    assert pd.isna(features.loc[features["symbol"] == "A", "return_1m_percentile"].values[0])
    assert pd.isna(features.loc[features["symbol"] == "B", "return_1m_percentile"].values[0])

def test_point_in_time_isolation():
    # Construct a panel across two dates. Ensure math on Date 1 is isolated from Date 2.
    df = pd.DataFrame({
        "original_timestamp": [pd.to_datetime("2023-01-01")] * 3 + [pd.to_datetime("2023-01-02")] * 3,
        "symbol": ["A", "B", "C", "A", "B", "C"],
        "ret_1m": [0.10, 0.05, 0.01,   0.01, 0.05, 0.10] # A is best on day 1, worst on day 2
    })
    
    engine = CrossSectionalFeatureEngine(min_universe_size=3)
    features = engine.calculate_features(df)
    
    day1_A = features[(features["original_timestamp"] == "2023-01-01") & (features["symbol"] == "A")]
    day2_A = features[(features["original_timestamp"] == "2023-01-02") & (features["symbol"] == "A")]
    
    # On day 1, A is the highest return (0.10) so it should be 1.0 (100th percentile)
    assert day1_A["return_1m_percentile"].values[0] == 1.0
    
    # On day 2, A is the lowest return (0.01) so it should be ~0.33 (33rd percentile for N=3)
    assert np.isclose(day2_A["return_1m_percentile"].values[0], 0.333333)
