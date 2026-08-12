import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List

from risk.engine.portfolio import PortfolioRiskEngine

logger = logging.getLogger(__name__)

class RiskAttributionEngine:
    """
    Decomposes portfolio volatility to identify exactly which assets are driving risk.
    Guarantees Euler's theorem: sum of component contributions strictly equals total portfolio volatility.
    """
    
    @staticmethod
    def calculate_risk_attribution(cov_matrix: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """
        Calculates MCR, CCR, and PCR for all assets in the portfolio.
        Returns a DataFrame indexed by asset.
        """
        assets = list(cov_matrix.columns)
        w = np.array([weights[asset] for asset in assets])
        cov = cov_matrix.values
        
        # 1. Total Portfolio Volatility
        port_vol = PortfolioRiskEngine.calculate_portfolio_volatility(cov_matrix, weights)
        
        if port_vol == 0:
            raise ValueError("Portfolio volatility is 0. Cannot calculate risk attribution.")
            
        # 2. Marginal Contribution to Risk (MCR)
        # Derivative of portfolio vol with respect to weight i.
        # MCR = (Covariance Matrix * Weights) / Portfolio Volatility
        mcr = np.dot(cov, w) / port_vol
        
        # 3. Component Contribution to Risk (CCR)
        # How much actual volatility is attributed to asset i
        # CCR_i = w_i * MCR_i
        ccr = w * mcr
        
        # Verify Euler's theorem (sum of CCR = total volatility)
        assert np.isclose(np.sum(ccr), port_vol, atol=1e-5), f"Euler's theorem failed: sum(CCR)={np.sum(ccr)}, PortVol={port_vol}"
        
        # 4. Percentage Contribution to Risk (PCR)
        # PCR_i = CCR_i / Portfolio Volatility
        pcr = ccr / port_vol
        
        attribution_df = pd.DataFrame({
            "Weight": w,
            "MCR": mcr,
            "CCR": ccr,
            "PCR": pcr
        }, index=assets)
        
        return attribution_df

    @staticmethod
    def analyze_concentration(attribution_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes the concentration of weights vs the concentration of risk.
        Identifies scenarios where a small weight drives massive risk.
        """
        
        # Find top 3 by weight
        top_weights = attribution_df.sort_values(by="Weight", ascending=False).head(3)
        weight_concentration = top_weights["Weight"].sum()
        
        # Find top 3 by risk contribution
        top_risks = attribution_df.sort_values(by="PCR", ascending=False).head(3)
        risk_concentration = top_risks["PCR"].sum()
        
        # Identify "Risk Outliers" - assets where PCR is vastly larger than their Weight
        attribution_df["Risk_to_Weight_Ratio"] = attribution_df["PCR"] / attribution_df["Weight"].replace(0, np.nan)
        
        # An asset generating >2x risk relative to its weight is highly volatile and highly correlated
        risk_outliers = attribution_df[attribution_df["Risk_to_Weight_Ratio"] > 2.0]
        
        return {
            "top_3_weight_concentration": weight_concentration,
            "top_3_risk_concentration": risk_concentration,
            "top_weight_assets": list(top_weights.index),
            "top_risk_assets": list(top_risks.index),
            "risk_outliers": risk_outliers.to_dict(orient="index")
        }
