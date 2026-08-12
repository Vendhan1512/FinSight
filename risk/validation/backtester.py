import numpy as np
import pandas as pd
import logging
from typing import Dict, Any

from risk.engine.var import RiskEngine

logger = logging.getLogger(__name__)

class VarBacktester:
    """
    Performs historical backtesting of Value at Risk models.
    Strict Point-in-Time adherence: The VaR threshold for Day T is calculated
    exclusively using data from [T - Window, T - 1].
    """
    
    @staticmethod
    def backtest(df: pd.DataFrame, time_col: str, return_col: str, window: int = 252, confidence_level: float = 0.95, method: str = "historical") -> Dict[str, Any]:
        """
        Runs the chronological backtest over the provided dataframe.
        """
        df = df.sort_values(time_col).reset_index(drop=True)
        
        if len(df) <= window:
            raise ValueError(f"Insufficient data for backtesting. N={len(df)}, Window={window}")
            
        exceedances = 0
        total_predictions = 0
        
        # We need arrays for fast sliding window
        times = df[time_col].values
        returns = df[return_col].values
        
        results = []
        
        # Start at index = window (e.g., day 252). Predict for day 252 using [0 : 251]
        for t in range(window, len(df)):
            window_returns = returns[t - window : t]
            actual_return = returns[t]
            current_time = times[t]
            
            try:
                metrics = RiskEngine.calculate_risk_metrics(window_returns, confidence_level, method)
                var_threshold = metrics["VaR"]
                
                # Check for exceedance (loss worse than the VaR threshold)
                is_exceedance = actual_return < var_threshold
                if is_exceedance:
                    exceedances += 1
                    
                total_predictions += 1
                
                results.append({
                    "time": current_time,
                    "var_threshold": var_threshold,
                    "actual_return": actual_return,
                    "is_exceedance": is_exceedance
                })
                
            except ValueError as e:
                logger.warning(f"Failed to calculate VaR at index {t}: {e}")
                continue
                
        if total_predictions == 0:
            raise ValueError("Backtest generated 0 valid predictions.")
            
        empirical_exceedance_rate = exceedances / total_predictions
        expected_exceedance_rate = 1.0 - confidence_level
        
        # Evaluate validity
        # Simple heuristic: If actual exceedances are way higher than expected, model is bad.
        # (A real Kupiec POF test would be better, but this satisfies the sprint requirements)
        
        ratio = empirical_exceedance_rate / expected_exceedance_rate if expected_exceedance_rate > 0 else 0
        
        is_valid = True
        warnings = []
        
        if ratio > 1.5:
            msg = f"Model Underestimating Risk: Empirical Exceedance ({empirical_exceedance_rate:.3%}) is >1.5x Expected ({expected_exceedance_rate:.3%})"
            warnings.append(msg)
            is_valid = False
            
        if ratio < 0.5:
            msg = f"Model Overestimating Risk: Empirical Exceedance ({empirical_exceedance_rate:.3%}) is <0.5x Expected ({expected_exceedance_rate:.3%})"
            warnings.append(msg)
            is_valid = False # Too conservative is also a bad model
            
        return {
            "method": method,
            "confidence_level": confidence_level,
            "window": window,
            "total_predictions": total_predictions,
            "exceedances": exceedances,
            "expected_exceedances": total_predictions * expected_exceedance_rate,
            "empirical_exceedance_rate": empirical_exceedance_rate,
            "expected_exceedance_rate": expected_exceedance_rate,
            "is_valid": is_valid,
            "warnings": warnings,
            "details": results
        }
