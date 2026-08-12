import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from ml.features.volatility.definitions import RISK_FEATURES

logger = logging.getLogger(__name__)

class VolatilityAndRiskEngine:
    """
    Computes mathematical risk metrics (Volatility, Sharpe, Beta, VaR)
    strictly enforcing min_periods to prevent data hallucination.
    """
    def __init__(self):
        self.definitions = {d.feature_name: d for d in RISK_FEATURES}

    def _verify_source_data(self, df: pd.DataFrame, feature_name: str) -> bool:
        contract = self.definitions[feature_name]
        # We manually verify sources here because some might be in joined dfs
        for col in contract.source_columns:
            if col not in df.columns:
                logger.error(f"Missing required source column '{col}' for feature '{feature_name}'.")
                return False
        return True

    def calculate_features(self, asset_df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame] = None, rfr_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Receives three DataFrames:
        - asset_df: Must contain 'adjusted_close' and 'log_return'
        - benchmark_df: Optional, must contain 'log_return'. Used for Beta/Correlation.
        - rfr_df: Optional, must contain 'rfr_daily'. Used for Sharpe/Sortino.
        """
        if asset_df.empty or "log_return" not in asset_df.columns:
            logger.warning("Empty dataframe or missing 'log_return'.")
            return pd.DataFrame()
            
        df = asset_df.sort_values(by="original_timestamp").copy()
        df.set_index("original_timestamp", inplace=True)
        
        # Merge Benchmark if provided
        if benchmark_df is not None and not benchmark_df.empty:
            bench = benchmark_df.sort_values(by="original_timestamp").copy()
            bench.set_index("original_timestamp", inplace=True)
            df = df.join(bench[["log_return"]], rsuffix="_bench")
            
        # Merge RFR if provided
        if rfr_df is not None and not rfr_df.empty:
            rfr = rfr_df.sort_values(by="original_timestamp").copy()
            rfr.set_index("original_timestamp", inplace=True)
            # Forward fill macro data to match daily trading days
            df = df.join(rfr[["rfr_daily"]]).ffill()
            
        # The result dataframe
        res = pd.DataFrame(index=df.index)
        
        # --- VOLATILITY ---
        for n in [20, 60, 120, 252]:
            name = f"vol_{n}d"
            if self._verify_source_data(df, name):
                # Sample std dev * sqrt(252)
                res[name] = df["log_return"].rolling(window=n, min_periods=n).std() * np.sqrt(252)
                
        # --- DOWNSIDE VOLATILITY ---
        name = "downside_vol_252d"
        if self._verify_source_data(df, name):
            # std of min(return, 0)
            neg_ret = np.minimum(df["log_return"], 0)
            res[name] = neg_ret.rolling(window=252, min_periods=252).std() * np.sqrt(252)
            
        # --- DRAWDOWN ---
        name = "max_drawdown_252d"
        if "adjusted_close" in df.columns:
            price = df["adjusted_close"]
            roll_max = price.rolling(window=252, min_periods=252).max()
            drawdown = (price / roll_max) - 1
            res[name] = drawdown.rolling(window=252, min_periods=252).min()
            
        # --- RISK ADJUSTED (SHARPE & SORTINO) ---
        if "rfr_daily" in df.columns:
            excess_ret = df["log_return"] - df["rfr_daily"]
            
            # Sharpe
            if self._verify_source_data(df, "sharpe_252d"):
                roll_mean = excess_ret.rolling(window=252, min_periods=252).mean()
                roll_std = excess_ret.rolling(window=252, min_periods=252).std()
                # Annualized mean / Annualized vol = (mean*252) / (std*sqrt(252)) = sqrt(252) * mean / std
                res["sharpe_252d"] = np.sqrt(252) * roll_mean / roll_std
                
            # Sortino
            if self._verify_source_data(df, "sortino_252d"):
                neg_excess = np.minimum(excess_ret, 0)
                downside_std = neg_excess.rolling(window=252, min_periods=252).std()
                res["sortino_252d"] = np.sqrt(252) * roll_mean / downside_std
        else:
            logger.warning("No RFR data. Skipping Sharpe/Sortino.")
            
        # --- MARKET SENSITIVITY (BETA & CORRELATION) ---
        if "log_return_bench" in df.columns:
            ret_a = df["log_return"]
            ret_b = df["log_return_bench"]
            
            if self._verify_source_data(df, "correlation_252d"):
                res["correlation_252d"] = ret_a.rolling(window=252, min_periods=252).corr(ret_b)
                
            if self._verify_source_data(df, "beta_252d"):
                cov = ret_a.rolling(window=252, min_periods=252).cov(ret_b)
                var = ret_b.rolling(window=252, min_periods=252).var()
                res["beta_252d"] = cov / var
        else:
            logger.warning("No benchmark data. Skipping Beta/Correlation.")
            
        # --- EMPIRICAL RISK (VaR & CVaR) ---
        if self._verify_source_data(df, "var_95_252d"):
            # 5th percentile return
            res["var_95_252d"] = df["log_return"].rolling(window=252, min_periods=252).quantile(0.05)
            
        if self._verify_source_data(df, "cvar_95_252d"):
            # Mean of returns below the VaR threshold. 
            # Very slow in raw pandas apply, so we use a custom sliding window approach or apply
            def calc_cvar(x):
                var = np.percentile(x, 5)
                return x[x < var].mean()
                
            res["cvar_95_252d"] = df["log_return"].rolling(window=252, min_periods=252).apply(calc_cvar, raw=True)
            
        res.reset_index(inplace=True)
        return res

    def get_feature_quality(self, features_df: pd.DataFrame) -> Dict[str, float]:
        if features_df.empty: return {}
        quality = {}
        total = len(features_df)
        cols = [c for c in features_df.columns if c != "original_timestamp"]
        for col in cols:
            quality[col] = (features_df[col].isna().sum() / total) * 100
        return quality
