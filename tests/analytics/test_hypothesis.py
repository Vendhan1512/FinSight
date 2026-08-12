import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from analytics.statistics.hypothesis import HypothesisTestingEngine

def test_dynamic_test_selection_students_t():
    # Normal data, equal variance
    np.random.seed(42)
    sample_a = pd.Series(np.random.normal(0, 1, 100))
    sample_b = pd.Series(np.random.normal(0.5, 1, 100))
    
    engine = HypothesisTestingEngine()
    result = engine.run_two_sample_test(sample_a, sample_b)
    
    assert "Student's t-test" in result["test_used"]
    assert result["effect_size_metric"] == "Cohen's d"

def test_dynamic_test_selection_welchs_t():
    # Normal data, vastly unequal variance
    np.random.seed(42)
    sample_a = pd.Series(np.random.normal(0, 1, 100))
    sample_b = pd.Series(np.random.normal(0.5, 5, 100)) # 5x std dev
    
    engine = HypothesisTestingEngine()
    result = engine.run_two_sample_test(sample_a, sample_b)
    
    assert "Welch's t-test" in result["test_used"]
    assert result["effect_size_metric"] == "Cohen's d"

def test_dynamic_test_selection_mann_whitney():
    # Highly skewed/non-normal data
    np.random.seed(42)
    sample_a = pd.Series(np.random.exponential(1, 100))
    sample_b = pd.Series(np.random.exponential(1.5, 100))
    
    engine = HypothesisTestingEngine()
    result = engine.run_two_sample_test(sample_a, sample_b)
    
    assert "Mann-Whitney U" in result["test_used"]
    assert result["effect_size_metric"] == "Cliff's Delta"

def test_insufficient_data():
    engine = HypothesisTestingEngine()
    
    sample_a = pd.Series([1, 2, 3])
    sample_b = pd.Series([4, 5, 6])
    
    with pytest.raises(ValueError, match="Minimum 30 required"):
        engine.run_two_sample_test(sample_a, sample_b)
