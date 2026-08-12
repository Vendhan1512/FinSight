import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy
from ml.features.validation.quality_engine import FeatureQualityEngine
from ml.features.selection.selector import FeatureSelectionEngine

def _mock_contract(name: str) -> FeatureDefinitionContract:
    return FeatureDefinitionContract(
        feature_name=name,
        formula="x",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0"
    )

def test_quality_engine_rejects_flaws():
    contracts = {
        "good": _mock_contract("good"),
        "constant": _mock_contract("constant"),
        "extreme": _mock_contract("extreme"),
        "missing": _mock_contract("missing")
    }
    
    df = pd.DataFrame({
        "good": np.random.randn(100),
        "constant": [5.0] * 100,
        "extreme": np.append(np.random.randn(99), [9999999.0]),
        "missing": [np.nan] * 50 + list(np.random.randn(50))
    })
    
    engine = FeatureQualityEngine(missingness_threshold=0.30)
    updated = engine.audit_features(df, contracts)
    
    assert updated["good"].status == "VALIDATED"
    assert updated["constant"].status == "REJECTED"
    assert "Constant Variance" in updated["constant"].rejection_reason
    
    assert updated["extreme"].status == "REJECTED"
    assert "Extreme Outliers" in updated["extreme"].rejection_reason
    
    assert updated["missing"].status == "REJECTED"
    assert "Missingness rate" in updated["missing"].rejection_reason

def test_selection_engine_redundancy_and_stability():
    contracts = {
        "feat_a": _mock_contract("feat_a"),
        "feat_b_redundant": _mock_contract("feat_b_redundant"),
        "feat_c_unstable": _mock_contract("feat_c_unstable")
    }
    
    # Pre-validate them
    for c in contracts.values(): c.status = "VALIDATED"
    
    np.random.seed(42)
    target = np.random.randn(300)
    
    # feat_a is highly predictive of target
    feat_a = target + np.random.randn(300) * 0.1
    
    # feat_b is perfectly correlated with feat_a, making it redundant
    feat_b = feat_a + np.random.randn(300) * 0.001 
    
    # feat_c is predictive in fold 1 (0-100), but noise in folds 2 and 3
    feat_c = np.concatenate([target[:100] + np.random.randn(100)*0.1, np.random.randn(200)*10])
    
    df = pd.DataFrame({
        "target": target,
        "feat_a": feat_a,
        "feat_b_redundant": feat_b,
        "feat_c_unstable": feat_c
    })
    
    engine = FeatureSelectionEngine(correlation_threshold=0.85)
    updated = engine.select_features(df, "target", contracts)
    
    # Feat A should be selected
    assert updated["feat_a"].status == "SELECTED"
    
    # Feat B should be rejected for redundancy
    assert updated["feat_b_redundant"].status == "REJECTED"
    assert "Redundant" in updated["feat_b_redundant"].rejection_reason
    
    # Feat C should be rejected for instability
    assert updated["feat_c_unstable"].status == "REJECTED"
    assert "Unstable" in updated["feat_c_unstable"].rejection_reason
