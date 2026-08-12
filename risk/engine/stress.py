import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Tuple

from risk.engine.portfolio import PortfolioRiskEngine
from risk.engine.attribution import RiskAttributionEngine
from risk.engine.var import RiskEngine

logger = logging.getLogger(__name__)

class HistoricalStressEngine:
    """
    Executes Institutional Historical Stress Testing.
    Strictly forbids hypothetical shock parameters (e.g. "Drop 20%").
    Evaluates the portfolio exclusively against actual market events.
    """
    
    @staticmethod
    def _validate_coverage(df: pd.DataFrame, start_date: str, end_date: str) -> bool:
        """Checks if the actual market data covers the scenario period."""
        if df.empty:
            return False
            
        first_available = df.index.min()
        last_available = df.index.max()
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        return (first_available <= start) and (last_available >= end)
        
    @staticmethod
    def calculate_recovery_period(cumulative_returns: pd.Series, full_cumulative_returns: pd.Series) -> int:
        """
        Calculates the number of trading days it took to recover the pre-crash high.
        If the data ends before recovery, returns -1.
        """
        if len(cumulative_returns) == 0:
            return -1
            
        pre_crash_high = 1.0 # Indexed to 1.0 at start of crash
        
        # Look at the returns AFTER the crash started
        post_crash_data = full_cumulative_returns.loc[cumulative_returns.index.min():]
        
        # Re-index to the start of the crash
        reindexed_post_crash = post_crash_data / post_crash_data.iloc[0]
        
        # Find when it crosses 1.0 again
        recovery_mask = reindexed_post_crash >= pre_crash_high
        
        if not recovery_mask.any():
            return -1 # Never recovered in available data
            
        recovery_date = recovery_mask.idxmax()
        
        # Count trading days from crash start to recovery date
        trading_days = len(reindexed_post_crash.loc[:recovery_date]) - 1
        
        return trading_days

    @staticmethod
    def run_scenario(df: pd.DataFrame, weights: Dict[str, float], scenario: Dict[str, str]) -> Dict[str, Any]:
        """
        Executes a specific historical scenario against the portfolio.
        """
        start_date = scenario["start_date"]
        end_date = scenario["end_date"]
        
        if not HistoricalStressEngine._validate_coverage(df, start_date, end_date):
            raise ValueError(
                f"UNAVAILABLE: Scenario '{scenario['scenario_name']}' requires data from "
                f"{start_date} to {end_date}. Available data: {df.index.min().date()} to {df.index.max().date()}."
            )
            
        # 1. Slice the Panic Window
        panic_df = df.loc[start_date:end_date]
        
        if len(panic_df) < 5:
            raise ValueError("Scenario window is too small (<5 days) to calculate meaningful risk.")
            
        # 2. Portfolio Returns & Matrix
        assets = list(weights.keys())
        panic_port_returns = PortfolioRiskEngine.calculate_portfolio_returns(panic_df, weights)
        panic_cov = PortfolioRiskEngine.calculate_covariance_matrix(panic_df, assets)
        
        # 3. Core Metrics
        total_panic_return = (1 + panic_port_returns).prod() - 1
        panic_volatility = PortfolioRiskEngine.calculate_portfolio_volatility(panic_cov, weights)
        panic_max_dd = PortfolioRiskEngine.calculate_max_drawdown(panic_port_returns)
        
        # 4. VaR behavior during the crash (Note: this is realized VaR, not predictive)
        panic_var = RiskEngine.calculate_historical_var(panic_port_returns.values, 0.95)
        
        # 5. Recovery Period
        # We need the full portfolio return stream to check if it recovered after the end_date
        full_port_returns = PortfolioRiskEngine.calculate_portfolio_returns(df, weights)
        full_cumulative = (1 + full_port_returns).cumprod()
        panic_cumulative = (1 + panic_port_returns).cumprod()
        
        recovery_days = HistoricalStressEngine.calculate_recovery_period(panic_cumulative, full_cumulative)
        
        # 6. Risk Attribution Shift
        # Calculate pre-crash attribution (e.g., 252 days before the crash)
        pre_crash_start = pd.to_datetime(start_date) - pd.Timedelta(days=365)
        pre_crash_df = df.loc[pre_crash_start:start_date]
        
        attribution_shift = {}
        if len(pre_crash_df) > 50:
            pre_cov = PortfolioRiskEngine.calculate_covariance_matrix(pre_crash_df, assets)
            pre_attr = RiskAttributionEngine.calculate_risk_attribution(pre_cov, weights)
            panic_attr = RiskAttributionEngine.calculate_risk_attribution(panic_cov, weights)
            
            # Compare PCR (Percentage Contribution to Risk)
            for asset in assets:
                attribution_shift[asset] = {
                    "Pre_Crash_PCR": float(pre_attr.loc[asset, "PCR"]),
                    "Crash_PCR": float(panic_attr.loc[asset, "PCR"]),
                    "Shift": float(panic_attr.loc[asset, "PCR"] - pre_attr.loc[asset, "PCR"])
                }
                
        return {
            "scenario_name": scenario["scenario_name"],
            "status": "VALID",
            "period": f"{start_date} to {end_date}",
            "trading_days": len(panic_df),
            "total_return": total_panic_return,
            "max_drawdown": panic_max_dd,
            "annualized_volatility": panic_volatility * np.sqrt(252),
            "realized_var_95": panic_var,
            "recovery_trading_days": recovery_days if recovery_days > 0 else "Did not recover in available data",
            "risk_attribution_shift": attribution_shift
        }
