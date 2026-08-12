import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List

from risk.engine.var import RiskEngine

logger = logging.getLogger(__name__)

class PortfolioRiskEngine:
    """
    Core calculation engine for Portfolio-level Risk Metrics.
    Aggregates individual asset returns using explicit historical weights.
    """
    
    @staticmethod
    def calculate_portfolio_returns(returns_df: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
        """
        Calculates the aggregate portfolio return stream.
        returns_df should have asset symbols as columns and dates as index.
        """
        # Validate weights sum to 1.0 (with slight float tolerance)
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError(f"Portfolio weights must sum to 1.0. Current sum: {total_weight}")
            
        # Ensure all required assets are present in the dataframe
        missing = [asset for asset in weights.keys() if asset not in returns_df.columns]
        if missing:
            raise ValueError(f"Missing return data for configured assets: {missing}")
            
        # Calculate R_p = sum(w_i * R_i)
        portfolio_returns = pd.Series(0.0, index=returns_df.index)
        for asset, weight in weights.items():
            portfolio_returns += returns_df[asset] * weight
            
        return portfolio_returns

    @staticmethod
    def calculate_covariance_matrix(returns_df: pd.DataFrame, assets: List[str]) -> pd.DataFrame:
        """Calculates empirical covariance matrix."""
        return returns_df[assets].cov()
        
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame, assets: List[str]) -> pd.DataFrame:
        """Calculates empirical correlation matrix."""
        return returns_df[assets].corr()

    @staticmethod
    def calculate_portfolio_volatility(cov_matrix: pd.DataFrame, weights: Dict[str, float]) -> float:
        """
        Calculates portfolio volatility using the matrix equation: sqrt(w^T * Cov * w).
        Returns the volatility in the same frequency as the covariance matrix (usually daily).
        """
        assets = list(cov_matrix.columns)
        weight_array = np.array([weights[asset] for asset in assets])
        
        # w^T * Cov * w
        portfolio_variance = np.dot(weight_array.T, np.dot(cov_matrix.values, weight_array))
        
        # Guard against tiny negative floats from precision errors
        if portfolio_variance < 0:
            portfolio_variance = 0.0
            
        return np.sqrt(portfolio_variance)
        
    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """Calculates the maximum drawdown of the return stream."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdowns = (cumulative - running_max) / running_max
        return float(drawdowns.min())

    @staticmethod
    def calculate_portfolio_metrics(returns_df: pd.DataFrame, weights: Dict[str, float], var_confidence: float = 0.95) -> Dict[str, Any]:
        """
        Orchestrator for all portfolio metrics.
        """
        assets = list(weights.keys())
        
        # 1. Aggregate Returns
        port_returns = PortfolioRiskEngine.calculate_portfolio_returns(returns_df, weights)
        
        # 2. Matrices
        cov_matrix = PortfolioRiskEngine.calculate_covariance_matrix(returns_df, assets)
        corr_matrix = PortfolioRiskEngine.calculate_correlation_matrix(returns_df, assets)
        
        # 3. Volatility
        daily_volatility = PortfolioRiskEngine.calculate_portfolio_volatility(cov_matrix, weights)
        
        # 4. Drawdown
        max_dd = PortfolioRiskEngine.calculate_max_drawdown(port_returns)
        
        # 5. Downside Risk (Pass to Sprint 5.2 Engine)
        risk_metrics = RiskEngine.calculate_risk_metrics(port_returns.values, confidence_level=var_confidence, method="historical")
        
        return {
            "daily_volatility": daily_volatility,
            "annualized_volatility": daily_volatility * np.sqrt(252), # Assuming daily input
            "max_drawdown": max_dd,
            "historical_var": risk_metrics["VaR"],
            "historical_cvar": risk_metrics["CVaR"],
            "covariance_matrix": cov_matrix,
            "correlation_matrix": corr_matrix,
            "portfolio_returns": port_returns
        }
