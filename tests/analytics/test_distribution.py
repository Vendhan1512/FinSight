import pytest
import pandas as pd
import numpy as np
import scipy.stats as stats
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.statistics.distribution import DistributionAndOutlierEngine

@pytest.fixture
def mock_distribution_data():
    # 50 normal observations (N > 30 required by the engine)
    np.random.seed(42)
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(50)]
    returns = np.random.normal(0, 0.01, 50)
    
    # Inject 1 extreme outlier
    returns[25] = 0.50 # 50% single day return (massive outlier)
    
    df = pd.DataFrame({
        "timestamp": dates,
        "log_return": returns
    })
    return df

def test_descriptive_statistics(mock_distribution_data):
    engine = DistributionAndOutlierEngine()
    df = engine._validate_data(mock_distribution_data)
    
    desc = engine.compute_descriptive_stats(df["log_return"])
    
    # Check that skewness is heavily positive due to the 50% outlier
    assert desc["skewness"] > 2.0
    
    # Check that max is exactly the outlier
    assert desc["max"] == 0.50

def test_normality_tests(mock_distribution_data):
    engine = DistributionAndOutlierEngine()
    df = engine._validate_data(mock_distribution_data)
    
    norm = engine.compute_normality_tests(df["log_return"])
    
    # With a 50% outlier in a normal distribution, Jarque-Bera should strongly reject normality (p < 0.05)
    jb_p = norm["jarque_bera"]["p_value"]
    assert jb_p < 0.01
    
    # N = 50, so Shapiro-Wilk should have run and also rejected normality
    sw_p = norm["shapiro_wilk"]["p_value"]
    assert sw_p < 0.01

def test_outlier_classification(mock_distribution_data):
    engine = DistributionAndOutlierEngine()
    df = engine._validate_data(mock_distribution_data)
    
    df_classified = engine.classify_outliers(df)
    
    # The 50% return at index 25 should unequivocally be classified as "extreme"
    assert df_classified.loc[25, "outlier_class"] == "extreme"
    assert df_classified.loc[25, "robust_z_score"] > 3.0

def test_insufficient_data():
    engine = DistributionAndOutlierEngine()
    
    # Only 5 rows
    df = pd.DataFrame({
        "timestamp": [datetime(2023, 1, 1)] * 5,
        "log_return": [0.01] * 5
    })
    
    with pytest.raises(ValueError, match="Insufficient observations"):
        engine._validate_data(df)
