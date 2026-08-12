import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from risk.engine.var import RiskEngine

def test_historical_var():
    # Array of 100 deterministic returns from -0.05 to +0.049
    returns = np.linspace(-0.05, 0.049, 100)
    
    # 95% Confidence -> 5th percentile
    var_95 = RiskEngine.calculate_historical_var(returns, 0.95)
    
    # The 5th percentile of this uniform distribution is roughly -0.045
    assert np.isclose(var_95, -0.045, atol=0.001)

def test_historical_cvar():
    # 10 returns
    returns = np.array([-0.05, -0.04, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, 0.04])
    
    # 90% Confidence -> 10th percentile = -0.041
    # Returns <= -0.041 is just [-0.05]
    cvar_90 = RiskEngine.calculate_historical_cvar(returns, 0.90)
    
    assert np.isclose(cvar_90, -0.05, atol=0.001)

def test_parametric_var_fat_tail_warning():
    # Generate a leptokurtic (fat-tailed) distribution
    np.random.seed(42)
    # T-distribution with low degrees of freedom has fat tails
    from scipy.stats import t
    returns = t.rvs(df=3, size=1000)
    
    var_value, warnings = RiskEngine.calculate_parametric_var(returns, 0.95)
    
    assert len(warnings) > 0
    assert "Fat Tail Warning" in warnings[0]
