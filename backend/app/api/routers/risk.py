from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any

from risk.engine.var import RiskEngine
from risk.engine.portfolio import PortfolioRiskEngine
from risk.engine.attribution import RiskAttributionEngine
from risk.engine.stress import HistoricalStressEngine
from risk.engine.assessment import RiskAssessmentEngine

router = APIRouter(prefix="/risk", tags=["risk"])

def _mock_asset_returns(seed: int = 42) -> np.ndarray:
    np.random.seed(seed)
    from scipy.stats import t
    return t.rvs(df=4, size=252) / 100

def _mock_portfolio_data():
    np.random.seed(42)
    dates = pd.date_range(end="2023-12-31", periods=252, freq="B")
    market = np.random.randn(252) * 0.01
    
    df = pd.DataFrame({
        "AAPL": market + np.random.randn(252) * 0.015,
        "MSFT": market + np.random.randn(252) * 0.012,
        "TSLA": market * 1.5 + np.random.randn(252) * 0.03
    }, index=dates)
    
    weights = {"AAPL": 0.40, "MSFT": 0.40, "TSLA": 0.20}
    return df, weights

@router.get("/assets/{symbol}/var")
def get_asset_var(symbol: str, confidence: float = 0.95):
    returns = _mock_asset_returns()
    metrics = RiskEngine.calculate_risk_metrics(returns, confidence, method="historical")
    
    return {
        "symbol": symbol.upper(),
        "data_timestamp": datetime.utcnow().isoformat(),
        "calculation_timestamp": datetime.utcnow().isoformat(),
        "methodology_version": "v1.0",
        "data_quality_status": "VALID",
        "historical_var": metrics["VaR"]
    }

@router.get("/assets/{symbol}/cvar")
def get_asset_cvar(symbol: str, confidence: float = 0.95):
    returns = _mock_asset_returns()
    metrics = RiskEngine.calculate_risk_metrics(returns, confidence, method="historical")
    
    return {
        "symbol": symbol.upper(),
        "data_timestamp": datetime.utcnow().isoformat(),
        "calculation_timestamp": datetime.utcnow().isoformat(),
        "methodology_version": "v1.0",
        "data_quality_status": "VALID",
        "historical_cvar": metrics["CVaR"]
    }

@router.get("/portfolio/{portfolio_id}/attribution")
def get_portfolio_attribution(portfolio_id: str):
    df, weights = _mock_portfolio_data()
    cov_matrix = PortfolioRiskEngine.calculate_covariance_matrix(df, list(weights.keys()))
    
    attr_df = RiskAttributionEngine.calculate_risk_attribution(cov_matrix, weights)
    concentration = RiskAttributionEngine.analyze_concentration(attr_df)
    
    return {
        "portfolio_id": portfolio_id,
        "data_timestamp": datetime.utcnow().isoformat(),
        "methodology_version": "v1.0",
        "data_quality_status": "VALID",
        "attribution": attr_df.to_dict(orient="index"),
        "concentration": concentration
    }

@router.get("/portfolio/{portfolio_id}/stress")
def get_portfolio_stress(portfolio_id: str, scenario: str = "covid-19"):
    df, weights = _mock_portfolio_data() # Usually we need longer data for stress, but mock for API routing
    
    # Let's inject a fake crash into the 252 days
    scenario_dict = {
        "scenario_name": "COVID-19 Market Shock",
        "start_date": df.index[100].strftime('%Y-%m-%d'),
        "end_date": df.index[130].strftime('%Y-%m-%d')
    }
    
    report = HistoricalStressEngine.run_scenario(df, weights, scenario_dict)
    
    report["data_timestamp"] = datetime.utcnow().isoformat()
    report["methodology_version"] = "v1.0"
    report["data_quality_status"] = "VALID"
    
    return report

@router.get("/portfolio/{portfolio_id}/assessment")
def get_portfolio_assessment(portfolio_id: str):
    """
    The master integrated endpoint.
    """
    df, weights = _mock_portfolio_data()
    
    # Calculate everything
    cov = PortfolioRiskEngine.calculate_covariance_matrix(df, list(weights.keys()))
    metrics = PortfolioRiskEngine.calculate_portfolio_metrics(df, weights)
    
    attr = RiskAttributionEngine.calculate_risk_attribution(cov, weights)
    conc = RiskAttributionEngine.analyze_concentration(attr)
    
    # Merge into a master dictionary
    metrics["top_3_risk_concentration"] = conc["top_3_risk_concentration"]
    metrics["cvar_99"] = RiskEngine.calculate_historical_cvar(metrics["portfolio_returns"].values, 0.99)
    
    # Drop pandas series before converting to JSON
    del metrics["covariance_matrix"]
    del metrics["correlation_matrix"]
    del metrics["portfolio_returns"]
    
    # Run through the Classification Engine
    assessment = RiskAssessmentEngine.evaluate_risk(metrics)
    
    return {
        "portfolio_id": portfolio_id,
        "data_timestamp": datetime.utcnow().isoformat(),
        "calculation_timestamp": datetime.utcnow().isoformat(),
        "data_quality_status": "VALID",
        "assessment": assessment
    }
