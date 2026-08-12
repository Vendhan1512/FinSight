import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.validation.pit_engine import LeakageValidator, LeakageDetectedError, PointInTimeJoiner

def test_leakage_validator_detects_future_sec_filing():
    # Construct a dataset where a Q1 filing (filed May 10) was accidentally
    # joined to a March 31st prediction row (massive leakage).
    df = pd.DataFrame({
        "prediction_timestamp": [pd.to_datetime("2023-03-31")],
        "sec_filing_date": [pd.to_datetime("2023-05-10")],
        "revenue": [1000]
    })
    
    with pytest.raises(LeakageDetectedError, match="FATAL: LeakageValidator detected"):
        LeakageValidator.validate_dataset(
            df=df,
            prediction_col="prediction_timestamp",
            availability_cols=["sec_filing_date"]
        )

def test_leakage_validator_detects_future_macro_revision():
    # Construct a dataset where a revised FRED value (published Jan 20)
    # was joined to a Jan 15th prediction row.
    df = pd.DataFrame({
        "prediction_timestamp": [pd.to_datetime("2023-01-15")],
        "fred_realtime_start": [pd.to_datetime("2023-01-20")],
        "cpi": [295]
    })
    
    with pytest.raises(LeakageDetectedError, match="FATAL: LeakageValidator detected"):
        LeakageValidator.validate_dataset(
            df=df,
            prediction_col="prediction_timestamp",
            availability_cols=["fred_realtime_start"]
        )

def test_leakage_validator_passes_valid_data():
    # Construct a valid PIT dataset.
    # Prediction: May 15.
    # SEC Filing: May 10.
    # Macro Value: May 14.
    # This is safe because Availability <= Prediction.
    df = pd.DataFrame({
        "prediction_timestamp": [pd.to_datetime("2023-05-15")],
        "sec_filing_date": [pd.to_datetime("2023-05-10")],
        "fred_realtime_start": [pd.to_datetime("2023-05-14")],
        "revenue": [1000],
        "cpi": [295]
    })
    
    # Should not raise any error
    result = LeakageValidator.validate_dataset(
        df=df,
        prediction_col="prediction_timestamp",
        availability_cols=["sec_filing_date", "fred_realtime_start"]
    )
    assert result is True

def test_point_in_time_joiner_prevents_leakage():
    # Target calendar
    target_df = pd.DataFrame({
        "prediction_time": [pd.to_datetime("2023-03-31"), pd.to_datetime("2023-05-15")]
    })
    
    # Feature data
    feature_df = pd.DataFrame({
        "filing_time": [pd.to_datetime("2023-05-10")],
        "revenue": [1000]
    })
    
    aligned = PointInTimeJoiner.join_asof(
        target_df=target_df,
        feature_df=feature_df,
        prediction_time_col="prediction_time",
        availability_time_col="filing_time",
        feature_cols=["revenue"]
    )
    
    # On March 31, revenue should be NaN (because it wasn't filed until May 10)
    assert pd.isna(aligned.iloc[0]["revenue"])
    
    # On May 15, revenue should be 1000 (because May 10 <= May 15)
    assert aligned.iloc[1]["revenue"] == 1000
