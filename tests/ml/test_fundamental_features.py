import pytest
import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.features.fundamental.engine import FundamentalFeatureEngine

def test_point_in_time_enforcement():
    # Construct a scenario where Q1 ends Mar 31, but is filed May 10.
    df = pd.DataFrame({
        "concept": ["SalesRevenueNet", "NetIncomeLoss"],
        "value": [1000.0, 100.0],
        "end_date": [pd.to_datetime("2023-03-31"), pd.to_datetime("2023-03-31")],
        "filing_date": [pd.to_datetime("2023-05-10"), pd.to_datetime("2023-05-10")]
    })
    
    engine = FundamentalFeatureEngine()
    features = engine.calculate_features(df)
    
    # The resulting feature timestamp MUST be May 10, NOT March 31
    assert len(features) == 1
    assert features.iloc[0]["original_timestamp"] == pd.to_datetime("2023-05-10")

def test_concept_mapping_and_margins():
    # Construct a dataset with diverse raw tags
    df = pd.DataFrame({
        "concept": ["RevenuesNetOfInterestExpense", "OperatingIncomeLoss"],
        "value": [1000.0, 200.0],
        "end_date": [pd.to_datetime("2023-03-31"), pd.to_datetime("2023-03-31")],
        "filing_date": [pd.to_datetime("2023-05-10"), pd.to_datetime("2023-05-10")]
    })
    
    engine = FundamentalFeatureEngine()
    features = engine.calculate_features(df)
    
    # Operating margin should be 200 / 1000 = 0.2
    assert features.iloc[0]["operating_margin"] == 0.2

def test_division_by_zero_safety():
    # Construct a scenario where Revenue is exactly 0 (or missing)
    df = pd.DataFrame({
        "concept": ["SalesRevenueNet", "NetIncomeLoss"],
        "value": [0.0, -50.0], # 0 revenue, 50 loss
        "end_date": [pd.to_datetime("2023-03-31"), pd.to_datetime("2023-03-31")],
        "filing_date": [pd.to_datetime("2023-05-10"), pd.to_datetime("2023-05-10")]
    })
    
    engine = FundamentalFeatureEngine()
    features = engine.calculate_features(df)
    
    # Net Margin (Net Income / Revenue) should be NaN, not raise a ZeroDivisionError or return inf
    assert pd.isna(features.iloc[0]["net_margin"])

def test_valuation_is_skipped():
    df = pd.DataFrame({
        "concept": ["NetIncomeLoss"],
        "value": [100.0],
        "end_date": [pd.to_datetime("2023-03-31")],
        "filing_date": [pd.to_datetime("2023-05-10")]
    })
    
    engine = FundamentalFeatureEngine()
    features = engine.calculate_features(df)
    
    # pe_ratio is marked Unavailable, so it should not exist in the output
    assert "pe_ratio" not in features.columns
