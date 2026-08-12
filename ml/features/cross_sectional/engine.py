import pandas as pd
import numpy as np
import logging
from typing import Dict, List
from ml.features.cross_sectional.definitions import CROSS_SECTIONAL_FEATURES

logger = logging.getLogger(__name__)

class CrossSectionalFeatureEngine:
    """
    Computes relative features by ranking assets against their peers at a specific Point-In-Time.
    Requires a panel dataframe (Date, Symbol, Features).
    """
    def __init__(self, min_universe_size: int = 10):
        self.definitions = {d.feature_name: d for d in CROSS_SECTIONAL_FEATURES}
        self.min_universe_size = min_universe_size
        
        # We explicitly document survivorship bias as per the prompt requirements.
        logger.warning(
            "SURVIVORSHIP BIAS WARNING: This cross-sectional engine operates only on the assets "
            "provided in the panel dataset. If the dataset does not include historical delistings, "
            "all historical rankings are biased toward survivors."
        )

    def _calc_zscore(self, series: pd.Series) -> pd.Series:
        """Calculates cross-sectional Z-Score, returning NaN if standard deviation is 0 or NaN."""
        if len(series.dropna()) < self.min_universe_size:
            return pd.Series(np.nan, index=series.index)
            
        std = series.std()
        if pd.isna(std) or std == 0:
            return pd.Series(np.nan, index=series.index)
            
        return (series - series.mean()) / std

    def _calc_percentile(self, series: pd.Series) -> pd.Series:
        """
        Calculates cross-sectional percentile rank (0.0 to 1.0).
        Uses 'average' method for ties (e.g. if two assets tie for 1st, they get rank 1.5).
        """
        if len(series.dropna()) < self.min_universe_size:
            return pd.Series(np.nan, index=series.index)
            
        return series.rank(method="average", pct=True)

    def calculate_features(self, panel_df: pd.DataFrame) -> pd.DataFrame:
        """
        Receives a panel DataFrame containing:
        'original_timestamp' (Prediction Date), 'symbol' (Asset), and base features.
        
        Group by timestamp to guarantee Point-In-Time cross-sectional isolation.
        """
        if panel_df.empty or "original_timestamp" not in panel_df.columns or "symbol" not in panel_df.columns:
            logger.warning("Invalid panel dataframe. Must contain 'original_timestamp' and 'symbol'.")
            return pd.DataFrame()
            
        # We create a copy to avoid SettingWithCopy warnings
        df = panel_df.copy()
        
        # 1. Ensure Chronological Sorting
        df = df.sort_values(by=["original_timestamp", "symbol"])
        
        # --- RELATIVE RETURNS ---
        if "ret_1m" in df.columns:
            if self.definitions["return_1m_percentile"].status == "Active":
                df["return_1m_percentile"] = df.groupby("original_timestamp")["ret_1m"].transform(self._calc_percentile)
                
            if self.definitions["return_1m_zscore"].status == "Active":
                df["return_1m_zscore"] = df.groupby("original_timestamp")["ret_1m"].transform(self._calc_zscore)
                
        # --- RELATIVE VOLATILITY ---
        if "vol_20d" in df.columns:
            if self.definitions["volatility_20d_percentile"].status == "Active":
                df["volatility_20d_percentile"] = df.groupby("original_timestamp")["vol_20d"].transform(self._calc_percentile)
                
        # --- RELATIVE FUNDAMENTALS ---
        if "operating_margin" in df.columns:
            if self.definitions["operating_margin_zscore"].status == "Active":
                df["operating_margin_zscore"] = df.groupby("original_timestamp")["operating_margin"].transform(self._calc_zscore)
                
        if "debt_to_equity" in df.columns:
            if self.definitions["debt_to_equity_percentile"].status == "Active":
                df["debt_to_equity_percentile"] = df.groupby("original_timestamp")["debt_to_equity"].transform(self._calc_percentile)
                
        # We drop the base features used for calculation to only return the cross-sectional ones
        # (along with the composite keys)
        cs_cols = ["original_timestamp", "symbol"] + [f for f in self.definitions.keys() if f in df.columns]
        
        return df[cs_cols]

    def get_feature_quality(self, features_df: pd.DataFrame) -> Dict[str, float]:
        if features_df.empty: return {}
        quality = {}
        total = len(features_df)
        cols = [c for c in features_df.columns if c not in ["original_timestamp", "symbol"]]
        for col in cols:
            quality[col] = (features_df[col].isna().sum() / total) * 100
        return quality
