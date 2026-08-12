import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from risk.engine.assessment import RiskAssessmentEngine

def test_critical_classification():
    metrics = {
        "max_drawdown": 0.45,
        "cvar_99": 0.05,
        "annualized_volatility": 0.20
    }
    
    res = RiskAssessmentEngine.evaluate_risk(metrics)
    assert res["classification"] == "CRITICAL"
    assert "exceeds 40%" in res["drivers"][0]

def test_high_classification():
    metrics = {
        "max_drawdown": 0.25, # Triggers HIGH
        "cvar_99": 0.05,
        "annualized_volatility": 0.20
    }
    
    res = RiskAssessmentEngine.evaluate_risk(metrics)
    assert res["classification"] == "HIGH"
    assert "exceeds 20%" in res["drivers"][0]
    
def test_moderate_classification():
    metrics = {
        "max_drawdown": 0.10,
        "cvar_99": 0.01,
        "historical_cvar": 0.01,
        "annualized_volatility": 0.18 # Triggers MODERATE
    }
    
    res = RiskAssessmentEngine.evaluate_risk(metrics)
    assert res["classification"] == "MODERATE"
    assert "exceeds 15%" in res["drivers"][0]

def test_low_classification():
    metrics = {
        "max_drawdown": 0.05,
        "cvar_99": 0.01,
        "historical_cvar": 0.01,
        "annualized_volatility": 0.10 # All safe
    }
    
    res = RiskAssessmentEngine.evaluate_risk(metrics)
    assert res["classification"] == "LOW"
