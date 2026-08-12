import pytest
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

def test_valid_feature_contract():
    # A perfectly defined feature should pass validation
    feature = FeatureDefinitionContract(
        feature_name="rsi_14_daily",
        description="Relative Strength Index over 14 days",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["close"],
        formula="100 - (100 / (1 + RS)) where RS is Smoothed Avg Gain / Smoothed Avg Loss",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=14,
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    )
    assert feature.feature_name == "rsi_14_daily"
    assert feature.lookback_periods == 14

def test_invalid_feature_name_rejected():
    # Names with spaces or uppercase should be explicitly rejected
    with pytest.raises(ValidationError, match="lowercase and use underscores"):
        FeatureDefinitionContract(
            feature_name="RSI 14 Daily", # BAD
            description="Relative Strength Index",
            feature_category="technical",
            source_dataset="analytical_market",
            source_columns=["close"],
            formula="Math goes here",
            frequency=FeatureFrequency.DAILY,
            lookback_periods=14,
            missing_value_policy=MissingValuePolicy.DROP,
            version_tag="1.0.0"
        )

def test_empty_formula_rejected():
    # A feature without a formula is just a black box and must be rejected
    with pytest.raises(ValidationError, match="Formula description is too short"):
        FeatureDefinitionContract(
            feature_name="secret_alpha_signal",
            description="Trust me it works",
            feature_category="cross_sectional",
            source_dataset="analytical_market",
            source_columns=["close"],
            formula="X", # BAD
            frequency=FeatureFrequency.DAILY,
            lookback_periods=1,
            missing_value_policy=MissingValuePolicy.DROP,
            version_tag="1.0.0"
        )

def test_missing_source_rejected():
    # A feature must define exactly which columns it needs
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        FeatureDefinitionContract(
            feature_name="bad_feature",
            description="No sources",
            feature_category="technical",
            source_dataset="analytical_market",
            source_columns=[], # BAD
            formula="Some formula",
            frequency=FeatureFrequency.DAILY,
            lookback_periods=1,
            missing_value_policy=MissingValuePolicy.DROP,
            version_tag="1.0.0"
        )
