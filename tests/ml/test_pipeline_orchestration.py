import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.orchestrator import FeaturePipelineOrchestrator
from ml.features.registry import FeatureRegistry

def test_registry_contains_default_sets():
    registry = FeatureRegistry()
    sets = registry.list_feature_sets()
    assert "technical_v1" in sets
    assert "macro_v1" in sets
    
def test_lineage_extraction():
    registry = FeatureRegistry()
    lineage = registry.get_lineage("return_1m_percentile")
    
    assert lineage["feature_name"] == "return_1m_percentile"
    assert lineage["feature_set"] == "cross_sectional_v1"
    assert "Must be <= Prediction Time" in lineage["availability_rule"]

def test_pipeline_orchestrator_success():
    # Provide valid data to the technical engine
    df = pd.DataFrame({
        "original_timestamp": pd.date_range("2023-01-01", periods=100),
        "symbol": "AAPL",
        "close": np.random.randn(100).cumsum() + 100,
        "high": np.random.randn(100).cumsum() + 105,
        "low": np.random.randn(100).cumsum() + 95,
        "volume": np.random.randint(1000, 10000, 100)
    })
    
    orchestrator = FeaturePipelineOrchestrator()
    result = orchestrator.execute_pipeline("technical_v1", df)
    
    run = result["run"]
    assert run["status"] == "SUCCESS"
    assert run["leakage_status"] == "PASSED"
    assert run["quality_status"] == "PASSED"
    
    # Assert data was actually created
    assert run["rows_created"] > 0
    assert not result["data"].empty
    
def test_pipeline_orchestrator_detects_leakage():
    # Provide intentionally leaking data (prediction in past, availability in future)
    df = pd.DataFrame({
        "original_timestamp": pd.date_range("2023-01-01", periods=10),
        "prediction_timestamp": pd.date_range("2023-01-01", periods=10),
        "availability_timestamp": pd.date_range("2023-02-01", periods=10), # Future!
        "symbol": "AAPL",
        "close": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "volume": [1000] * 10
    })
    
    orchestrator = FeaturePipelineOrchestrator()
    result = orchestrator.execute_pipeline("technical_v1", df)
    
    # The pipeline should completely abort
    run = result["run"]
    assert run["status"] == "FAILED_LEAKAGE"
    assert run["leakage_status"] == "FAILED"
    
    # Data should be empty because it aborted
    assert result["data"].empty
