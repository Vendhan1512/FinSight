import pandas as pd
import numpy as np
import logging
from typing import Dict
from ml.features.volume.definitions import VOLUME_FEATURES

logger = logging.getLogger(__name__)

class VolumeFeatureEngine:
    """
    Computes mathematical volume features (Change, Z-Score, OBV)
    while enforcing strict validation (e.g. aborting on negative volume).
    """
    def __init__(self):
        self.definitions = {d.feature_name: d for d in VOLUME_FEATURES}

    def _validate_data_integrity(self, df: pd.DataFrame) -> bool:
        """Pre-calculation validation to prevent garbage-in garbage-out."""
        if "volume" in df.columns and (df["volume"] < 0).any():
            logger.error("FATAL: Negative volume detected in dataset. Aborting.")
            return False
            
        if "high" in df.columns and "low" in df.columns:
            if (df["high"] < df["low"]).any():
                logger.error("FATAL: High price is strictly less than Low price. Aborting.")
                return False
                
        # Check for duplicated timestamps
        if df["original_timestamp"].duplicated().any():
            logger.error("FATAL: Duplicated timestamps detected in dataset. Aborting.")
            return False
            
        return True

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates volume features. Skips unavailable features like VWAP."""
        if df.empty or "volume" not in df.columns:
            logger.warning("Empty dataframe or missing 'volume'.")
            return pd.DataFrame()
            
        if not self._validate_data_integrity(df):
            raise ValueError("Data integrity validation failed.")
            
        df = df.sort_values(by="original_timestamp").copy()
        res = pd.DataFrame({"original_timestamp": df["original_timestamp"]})
        
        vol = df["volume"]
        
        # We will loop through the definitions. If they are Active, we compute them.
        
        # vol_change_1d
        if self.definitions["vol_change_1d"].status == "Active":
            res["vol_change_1d"] = (vol / vol.shift(1)) - 1
            
        # vol_sma_20d, vol_sma_50d
        for n in [20, 50]:
            name = f"vol_sma_{n}d"
            if self.definitions[name].status == "Active":
                res[name] = vol.rolling(window=n, min_periods=n).mean()
                
        # vol_std_20d
        name = "vol_std_20d"
        if self.definitions[name].status == "Active":
            res[name] = vol.rolling(window=20, min_periods=20).std()
            
        # vol_zscore_20d
        name = "vol_zscore_20d"
        if self.definitions[name].status == "Active" and "vol_sma_20d" in res.columns and "vol_std_20d" in res.columns:
            res[name] = (vol - res["vol_sma_20d"]) / res["vol_std_20d"]
            
        # vol_ratio_20d
        name = "vol_ratio_20d"
        if self.definitions[name].status == "Active" and "vol_sma_20d" in res.columns:
            res[name] = vol / res["vol_sma_20d"]
            
        # On-Balance Volume (OBV)
        name = "obv"
        if self.definitions[name].status == "Active" and "close" in df.columns:
            # OBV logic:
            # If close > prior close, direction = 1
            # If close < prior close, direction = -1
            # If close == prior close, direction = 0
            # OBV = Cumulative sum of (Volume * direction)
            price_diff = df["close"].diff()
            direction = np.sign(price_diff)
            # The first row will be NaN because of diff(). We can fill it with 0 or leave NaN.
            direction = direction.fillna(0)
            res[name] = (vol * direction).cumsum()
            
        # Explicit check to prove we skip VWAP
        for feat, contract in self.definitions.items():
            if contract.status == "Unavailable":
                logger.info(f"Skipping feature {feat}: Marked as Unavailable by Contract.")

        return res

    def get_feature_quality(self, features_df: pd.DataFrame) -> Dict[str, float]:
        if features_df.empty: return {}
        quality = {}
        total = len(features_df)
        cols = [c for c in features_df.columns if c != "original_timestamp"]
        for col in cols:
            quality[col] = (features_df[col].isna().sum() / total) * 100
        return quality
