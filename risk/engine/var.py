import numpy as np
import logging
from typing import Dict, Any, Tuple
from scipy.stats import norm, kurtosis

logger = logging.getLogger(__name__)

class RiskEngine:
    """
    Core calculation engine for downside risk metrics.
    Strictly enforced rule: NO Monte Carlo simulation or synthetic tail fabrication.
    All calculations are derived purely from empirical historical observations.
    """
    
    @staticmethod
    def calculate_historical_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculates Historical Value at Risk.
        Returns the empirical quantile corresponding to the tail threshold.
        """
        if len(returns) == 0:
            raise ValueError("Insufficient data to calculate VaR.")
            
        alpha = 1.0 - confidence_level
        # np.percentile takes [0, 100]
        var_value = np.percentile(returns, alpha * 100)
        return var_value

    @staticmethod
    def calculate_historical_cvar(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculates Historical Conditional Value at Risk (Expected Shortfall).
        Calculates the arithmetic mean of all returns that are strictly worse than 
        or equal to the VaR threshold.
        """
        var_threshold = RiskEngine.calculate_historical_var(returns, confidence_level)
        
        tail_losses = returns[returns <= var_threshold]
        
        if len(tail_losses) == 0:
            # Fallback if somehow the threshold leaves an empty array (extremely small sample)
            return var_threshold
            
        return float(np.mean(tail_losses))

    @staticmethod
    def calculate_parametric_var(returns: np.ndarray, confidence_level: float = 0.95) -> Tuple[float, list]:
        """
        Calculates Parametric (Normal) Value at Risk.
        WARNING: Financial returns almost never follow a normal distribution.
        This method will dynamically flag high kurtosis (fat tails).
        """
        if len(returns) < 30:
            raise ValueError("Insufficient data for parametric assumptions (N < 30).")
            
        warnings = []
        
        # Scipy kurtosis is excess kurtosis (Fisher). Normal = 0. 
        # But standard Pearson kurtosis is 3. We use Fisher, so > 1 or 2 is fat-tailed.
        excess_k = kurtosis(returns, fisher=True)
        if excess_k > 1.0:
            msg = f"Fat Tail Warning: Excess Kurtosis is {excess_k:.2f}. The Normal distribution assumption severely underestimates tail risk."
            logger.warning(msg)
            warnings.append(msg)
            
        mean = np.mean(returns)
        std = np.std(returns)
        
        alpha = 1.0 - confidence_level
        z_score = norm.ppf(alpha)
        
        var_value = mean + (z_score * std)
        
        return var_value, warnings

    @staticmethod
    def calculate_risk_metrics(returns: np.ndarray, confidence_level: float = 0.95, method: str = "historical") -> Dict[str, Any]:
        """Orchestrator for risk calculations."""
        
        if method == "historical":
            var = RiskEngine.calculate_historical_var(returns, confidence_level)
            cvar = RiskEngine.calculate_historical_cvar(returns, confidence_level)
            warnings = []
        elif method == "parametric_normal":
            var, warnings = RiskEngine.calculate_parametric_var(returns, confidence_level)
            cvar = None # We strictly refuse to calculate Parametric CVaR as it is mathematically indefensible for financial data
            warnings.append("CVaR is undefined for Parametric Normal in this engine due to extreme model risk.")
        else:
            raise ValueError(f"Unknown risk method: {method}")
            
        return {
            "method": method,
            "confidence_level": confidence_level,
            "sample_size": len(returns),
            "VaR": var,
            "CVaR": cvar,
            "warnings": warnings
        }
