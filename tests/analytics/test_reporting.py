import pytest
import pandas as pd
import numpy as np
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.reporting.eda_report import EDAReportEngine

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2023-01-01", periods=100, freq='D')
    np.random.seed(42)
    # Generate random returns, but seed ensures determinism
    returns = np.random.normal(0, 0.02, 100)
    
    # Needs rolling vol for hypothesis testing
    df = pd.DataFrame({
        "original_timestamp": dates,
        "log_return": returns,
        "close": np.exp(np.cumsum(returns)) * 100
    })
    
    # Calculate simple rolling vol manually for the mock
    df["rolling_vol_annualized"] = df["log_return"].rolling(20).std() * np.sqrt(252)
    return df

def test_report_reproducibility(mock_market_data):
    engine = EDAReportEngine(output_dir="tmp_test_reports")
    
    # Generate Payload 1
    payload1 = engine.generate_report_payload("TEST", mock_market_data)
    
    # Generate Payload 2 on exact same data
    payload2 = engine.generate_report_payload("TEST", mock_market_data)
    
    # The 'generated_at' timestamp will be different.
    # To test pure analytical reproducibility, we remove the timestamp and compare.
    del payload1["metadata"]["generated_at"]
    del payload2["metadata"]["generated_at"]
    
    # Serialize to JSON strings to ensure all nested floats are exact
    json1 = json.dumps(payload1, sort_keys=True)
    json2 = json.dumps(payload2, sort_keys=True)
    
    assert json1 == json2

def test_missing_data_handling(mock_market_data):
    engine = EDAReportEngine(output_dir="tmp_test_reports")
    
    # Pass empty macro and benchmark
    payload = engine.generate_report_payload("TEST", mock_market_data, None, None, None)
    
    # Should safely record that benchmark/macro is missing without crashing
    assert payload["correlation"]["note"] == "No benchmark"
    assert payload["macro_relationships"]["note"] == "No macro data provided"
