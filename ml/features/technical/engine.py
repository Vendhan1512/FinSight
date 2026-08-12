import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from ml.features.technical.definitions import TECHNICAL_FEATURES

logger = logging.getLogger(__name__)

class TechnicalFeatureEngine:
    """
    Computes mathematical technical indicators (Returns, Moving Averages, Momentum)
    strictly following Pydantic contracts and enforcing strict missing-value rules
    (no forward-filling initial rolling windows).
    """
    def __init__(self):
        self.definitions = {d.feature_name: d for d in TECHNICAL_FEATURES}

    def _verify_source_data(self, df: pd.DataFrame, feature_name: str) -> bool:
        contract = self.definitions[feature_name]
        for col in contract.source_columns:
            if col not in df.columns:
                logger.error(f"Missing required source column '{col}' for feature '{feature_name}'.")
                return False
        return True

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Receives a DataFrame sorted by time for a single symbol.
        Returns a new DataFrame containing only the calculated features and timestamps.
        """
        if df.empty or "adjusted_close" not in df.columns or "original_timestamp" not in df.columns:
            logger.warning("Empty dataframe or missing 'adjusted_close'/'original_timestamp'. Returning empty.")
            return pd.DataFrame()
            
        # Ensure chronological order for rolling windows
        df = df.sort_values(by="original_timestamp").copy()
        
        # The result dataframe
        res = pd.DataFrame({"original_timestamp": df["original_timestamp"]})
        
        # We use adjusted close for all technical math to prevent split/dividend artifacts
        price = df["adjusted_close"]
        
        # --- SIMPLE RETURNS ---
        for n in [1, 5, 20, 60, 120, 252]:
            name = f"ret_{n}d"
            if self._verify_source_data(df, name):
                res[name] = price.pct_change(periods=n)
                
        # --- LOG RETURNS ---
        for n in [1, 5, 20]:
            name = f"log_ret_{n}d"
            if self._verify_source_data(df, name):
                res[name] = np.log(price / price.shift(n))
                
        # --- SMAs ---
        for n in [20, 50, 100, 200]:
            name = f"sma_{n}d"
            if self._verify_source_data(df, name):
                res[name] = price.rolling(window=n, min_periods=n).mean() # min_periods=n explicitly forces NaNs for initial windows
                
        # --- EMAs ---
        for n in [20, 50]:
            name = f"ema_{n}d"
            if self._verify_source_data(df, name):
                # We use adjust=False for standard financial EMA, min_periods ensures initial NaNs
                res[name] = price.ewm(span=n, adjust=False, min_periods=n).mean() 
                
        # --- PRICE RELATIONSHIPS ---
        for n in [20, 50, 200]:
            name = f"price_to_sma_{n}d"
            sma_col = f"sma_{n}d"
            if self._verify_source_data(df, name) and sma_col in res.columns:
                res[name] = price / res[sma_col]
                
        if self._verify_source_data(df, "dist_from_rolling_high_252d"):
            roll_max = price.rolling(window=252, min_periods=252).max()
            res["dist_from_rolling_high_252d"] = (price / roll_max) - 1
            
        if self._verify_source_data(df, "dist_from_rolling_low_252d"):
            roll_min = price.rolling(window=252, min_periods=252).min()
            res["dist_from_rolling_low_252d"] = (price / roll_min) - 1
            
        # --- MOMENTUM ---
        for n in [20, 60, 120]:
            name = f"mom_{n}d"
            if self._verify_source_data(df, name):
                res[name] = price - price.shift(n)
                
        return res

    def get_feature_quality(self, features_df: pd.DataFrame) -> Dict[str, float]:
        """Calculates the missingness percentage for every calculated feature."""
        if features_df.empty:
            return {}
            
        quality = {}
        total_rows = len(features_df)
        cols_to_check = [c for c in features_df.columns if c != "original_timestamp"]
        
        for col in cols_to_check:
            missing = features_df[col].isna().sum()
            quality[col] = (missing / total_rows) * 100
            
        return quality
