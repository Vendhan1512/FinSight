import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.targets.engine import TargetEngine
from ml.dataset.builder import DatasetBuilder, ChronologicalSplitter, LeakageAssertionError

def test_target_engine_regression():
    df = pd.DataFrame({
        "symbol": "AAPL",
        "original_timestamp": pd.date_range("2023-01-01", periods=5),
        "close": [100.0, 105.0, 110.0, 108.0, 112.0]
    })
    
    # Calculate 2-day return
    targets = TargetEngine.calculate_targets(df, horizon_days=2, target_type="regression_return")
    
    # Day 1 (100) -> Day 3 (110) = 10% return
    assert targets.iloc[0]["target_value"] == 0.10
    assert targets.iloc[0]["target_end_time"] == pd.to_datetime("2023-01-03")
    
    # Expect 3 rows because the last 2 don't have future observations
    assert len(targets) == 3

def test_target_engine_classification():
    df = pd.DataFrame({
        "symbol": "AAPL",
        "original_timestamp": pd.date_range("2023-01-01", periods=3),
        "close": [100.0, 105.0, 95.0]
    })
    
    # 1-day horizon
    targets = TargetEngine.calculate_targets(df, horizon_days=1, target_type="classification_direction")
    
    # Day 1 (100) -> Day 2 (105) = UP (1.0)
    assert targets.iloc[0]["target_value"] == 1.0
    
    # Day 2 (105) -> Day 3 (95) = DOWN (0.0)
    assert targets.iloc[1]["target_value"] == 0.0

def test_chronological_splitting():
    df = pd.DataFrame({
        "prediction_time": [
            pd.to_datetime("2018-01-01"), # Train
            pd.to_datetime("2020-12-31"), # Train
            pd.to_datetime("2021-01-01"), # Val
            pd.to_datetime("2022-06-01"), # Val
            pd.to_datetime("2023-01-01"), # Test
            pd.to_datetime("2023-12-31")  # Test
        ]
    })
    
    split_df = ChronologicalSplitter.assign_partitions(df)
    partitions = split_df["partition"].values
    
    assert partitions[0] == "TRAIN"
    assert partitions[1] == "TRAIN"
    assert partitions[2] == "VALIDATION"
    assert partitions[3] == "VALIDATION"
    assert partitions[4] == "TEST"
    assert partitions[5] == "TEST"

def test_dataset_builder_leakage_assertion():
    features_df = pd.DataFrame({
        "symbol": "AAPL",
        "prediction_time": [pd.to_datetime("2023-01-01")],
        "sec_filing_date": [pd.to_datetime("2023-01-05")] # FUTURE!
    })
    
    targets_df = pd.DataFrame({
        "symbol": "AAPL",
        "prediction_time": [pd.to_datetime("2023-01-01")],
        "target_end_time": [pd.to_datetime("2023-01-10")],
        "target_value": [0.05]
    })
    
    # Builder should crash
    with pytest.raises(LeakageAssertionError, match="FATAL LEAKAGE"):
        DatasetBuilder.build(features_df, targets_df, ["sec_filing_date"])
