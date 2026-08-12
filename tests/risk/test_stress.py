import pytest
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from risk.engine.stress import HistoricalStressEngine

def test_validate_coverage():
    dates = pd.date_range("2020-01-01", "2020-12-31")
    df = pd.DataFrame({"returns": np.zeros(len(dates))}, index=dates)
    
    # Valid coverage
    assert HistoricalStressEngine._validate_coverage(df, "2020-02-01", "2020-03-01") == True
    
    # Invalid coverage (starts before data)
    assert HistoricalStressEngine._validate_coverage(df, "2019-12-01", "2020-03-01") == False
    
    # Invalid coverage (ends after data)
    assert HistoricalStressEngine._validate_coverage(df, "2020-11-01", "2021-01-01") == False

def test_recovery_period():
    # Construct a cumulative return stream that crashes from 1.0 down to 0.8, then recovers
    dates = pd.date_range("2020-01-01", periods=10)
    
    # Values:     1.0  0.9  0.8  0.8  0.8  0.85 0.9  0.95 1.05 1.1
    # Day Index:   0    1    2    3    4    5    6    7    8    9
    
    full_cumulative = pd.Series([1.0, 0.9, 0.8, 0.8, 0.8, 0.85, 0.9, 0.95, 1.05, 1.1], index=dates)
    
    # Let's say the panic window was Day 0 to Day 4
    panic_cumulative = full_cumulative.iloc[0:5]
    
    # Recovery should trigger on Day 8 (value 1.05 >= 1.0)
    # Number of trading days from Day 0 to Day 8 is 8.
    recovery_days = HistoricalStressEngine.calculate_recovery_period(panic_cumulative, full_cumulative)
    
    assert recovery_days == 8

def test_no_recovery_period():
    dates = pd.date_range("2020-01-01", periods=5)
    
    # It crashes and stays down
    full_cumulative = pd.Series([1.0, 0.9, 0.8, 0.7, 0.6], index=dates)
    panic_cumulative = full_cumulative.iloc[0:3]
    
    recovery_days = HistoricalStressEngine.calculate_recovery_period(panic_cumulative, full_cumulative)
    
    # -1 means did not recover
    assert recovery_days == -1
