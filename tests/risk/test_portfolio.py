import pytest
import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from risk.engine.portfolio import PortfolioRiskEngine
from risk.engine.attribution import RiskAttributionEngine

def test_portfolio_volatility_and_euler_theorem():
    # Deterministic mock returns
    np.random.seed(42)
    # Asset A is low vol, Asset B is high vol
    ret_a = np.random.randn(100) * 0.01
    ret_b = np.random.randn(100) * 0.05
    
    df = pd.DataFrame({"A": ret_a, "B": ret_b})
    weights = {"A": 0.5, "B": 0.5}
    
    # Calculate cov
    cov_matrix = PortfolioRiskEngine.calculate_covariance_matrix(df, ["A", "B"])
    
    # Total Vol
    port_vol = PortfolioRiskEngine.calculate_portfolio_volatility(cov_matrix, weights)
    
    # Run Attribution
    attr_df = RiskAttributionEngine.calculate_risk_attribution(cov_matrix, weights)
    
    # Euler's Theorem: Sum of CCRs must exactly equal Total Volatility
    sum_ccr = attr_df["CCR"].sum()
    assert np.isclose(sum_ccr, port_vol, atol=1e-6)
    
    # Verify PCR sums to 1.0 (100%)
    sum_pcr = attr_df["PCR"].sum()
    assert np.isclose(sum_pcr, 1.0, atol=1e-6)

def test_risk_outlier_detection():
    # Asset A is 90% weight, Asset B is 10% weight but massive vol
    np.random.seed(42)
    ret_a = np.random.randn(100) * 0.001
    ret_b = np.random.randn(100) * 0.10
    
    df = pd.DataFrame({"A": ret_a, "B": ret_b})
    weights = {"A": 0.9, "B": 0.1}
    
    cov_matrix = PortfolioRiskEngine.calculate_covariance_matrix(df, ["A", "B"])
    attr_df = RiskAttributionEngine.calculate_risk_attribution(cov_matrix, weights)
    
    concentration = RiskAttributionEngine.analyze_concentration(attr_df)
    
    # B should be identified as a risk outlier because its PCR is much larger than 10%
    outliers = list(concentration["risk_outliers"].keys())
    assert "B" in outliers
    assert "A" not in outliers
