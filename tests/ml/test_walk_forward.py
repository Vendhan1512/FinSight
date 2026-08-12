import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.validation.walk_forward import WalkForwardEngine

def test_walk_forward_expanding_bounds():
    # 100 days of data
    dates = pd.date_range("2023-01-01", periods=100)
    df = pd.DataFrame({
        "prediction_time": dates,
        "feature_1": np.ones(100),
        "target": np.ones(100)
    })
    
    # Train 10 days, Step 10 days, Gap 2 days
    engine = WalkForwardEngine(
        model_name="baseline_historical_mean", # Very fast for testing
        mode="expanding",
        train_window_days=10,
        step_size_days=10,
        gap_days=2
    )
    
    result = engine.evaluate(df, ["feature_1"], "target")
    
    # We started on Jan 1st
    # Train 1: Jan 1 -> Jan 11 (10 days)
    # Gap 2: Jan 11 -> Jan 13
    # Test 1: Jan 13 -> Jan 23 (10 days)
    
    fold_1 = result["fold_details"][0]
    
    assert fold_1["train_start"] == pd.to_datetime("2023-01-01")
    assert fold_1["train_end"] == pd.to_datetime("2023-01-11")
    assert fold_1["test_start"] == pd.to_datetime("2023-01-13")
    assert fold_1["test_end"] == pd.to_datetime("2023-01-23")
    
    # Fold 2 (Expanding)
    # Train 2: Jan 1 -> Jan 21 (train_end increases by step_size 10)
    # Gap 2: Jan 21 -> Jan 23
    # Test 2: Jan 23 -> Feb 02
    
    fold_2 = result["fold_details"][1]
    assert fold_2["train_start"] == pd.to_datetime("2023-01-01") # Still starts at Jan 1
    assert fold_2["train_end"] == pd.to_datetime("2023-01-21")
    assert fold_2["test_start"] == pd.to_datetime("2023-01-23")
    assert fold_2["test_end"] == pd.to_datetime("2023-02-02")
    
def test_walk_forward_rolling_bounds():
    dates = pd.date_range("2023-01-01", periods=100)
    df = pd.DataFrame({
        "prediction_time": dates,
        "feature_1": np.ones(100),
        "target": np.ones(100)
    })
    
    # Train 10 days, Step 10 days, Gap 2 days
    engine = WalkForwardEngine(
        model_name="baseline_historical_mean",
        mode="rolling",
        train_window_days=10,
        step_size_days=10,
        gap_days=2
    )
    
    result = engine.evaluate(df, ["feature_1"], "target")
    
    # Fold 1 is the same as expanding
    fold_1 = result["fold_details"][0]
    assert fold_1["train_start"] == pd.to_datetime("2023-01-01")
    
    # Fold 2 (Rolling)
    # Train 2: Jan 11 -> Jan 21 (train_start shifted forward by step_size)
    fold_2 = result["fold_details"][1]
    assert fold_2["train_start"] == pd.to_datetime("2023-01-11") # Shifted!
    assert fold_2["train_end"] == pd.to_datetime("2023-01-21")
