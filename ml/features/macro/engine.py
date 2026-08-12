import pandas as pd
import numpy as np
import logging
from typing import Dict, List
from ml.features.macro.definitions import MACRO_FEATURES

logger = logging.getLogger(__name__)

class MacroFeatureEngine:
    """
    Computes macroeconomic features while strictly enforcing
    ALFRED (ArchivaL FRED) vintage semantics to prevent look-ahead bias.
    """
    def __init__(self):
        self.definitions = {d.feature_name: d for d in MACRO_FEATURES}

    def _align_pit_vintage(self, market_dates: pd.DatetimeIndex, macro_df: pd.DataFrame, value_col: str) -> pd.Series:
        """
        Takes a calendar of market trading dates and a macro dataframe with 'realtime_start'.
        Uses merge_asof to guarantee that for any market date T, we ONLY use the macro value
        where realtime_start <= T. This mathematically prevents future revisions from leaking.
        """
        # Ensure macro_df is sorted by realtime_start for merge_asof
        macro_df = macro_df.sort_values("realtime_start").dropna(subset=["realtime_start", value_col])
        
        target = pd.DataFrame({"prediction_date": market_dates}).sort_values("prediction_date")
        
        # merge_asof finds the exact or closest prior realtime_start for each prediction_date
        aligned = pd.merge_asof(
            target, 
            macro_df[["realtime_start", value_col]],
            left_on="prediction_date",
            right_on="realtime_start",
            direction="backward"
        )
        
        return aligned[value_col].values

    def calculate_features(self, market_df: pd.DataFrame, macro_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Receives the target market dataframe (providing the daily prediction calendar)
        and a dictionary of macro dataframes (keyed by series, e.g., 'FEDFUNDS').
        
        Each macro_df MUST contain: 'observation_date', 'realtime_start', 'value'.
        """
        if market_df.empty or "original_timestamp" not in market_df.columns:
            logger.warning("Empty market dataframe. Cannot build prediction calendar.")
            return pd.DataFrame()
            
        market_dates = pd.to_datetime(market_df["original_timestamp"]).sort_values().reset_index(drop=True)
        res = pd.DataFrame({"original_timestamp": market_dates})
        
        # 1. Align all raw macro series to the daily market calendar FIRST
        aligned_raw = {}
        for series_id, m_df in macro_dfs.items():
            if m_df.empty:
                logger.warning(f"Macro series {series_id} is empty.")
                continue
            # Note: A true ALFRED implementation groups by observation_date and takes the max realtime_start <= T.
            # However, merge_asof natively handles grabbing the latest known vintage if we sort correctly.
            # To be absolutely strict, we sort by observation_date then realtime_start.
            # Actually, to predict today, we want the most recently *released* data, regardless of what month it describes.
            # So sorting by realtime_start is correct for standard daily ML alignment.
            aligned_raw[series_id] = self._align_pit_vintage(market_dates, m_df, "value")
            
        # --- LEVELS ---
        # Map the series names to the expected feature definitions
        series_map = {
            "FEDFUNDS": "fedfunds",
            "CPIAUCSL": "cpiaucsl",
            "UNRATE": "unrate",
            "GS10": "gs10"
        }
        
        for raw_id, clean_id in series_map.items():
            if raw_id in aligned_raw:
                feature_name = f"{clean_id}_level"
                if feature_name in self.definitions and self.definitions[feature_name].status == "Active":
                    res[feature_name] = aligned_raw[raw_id]
                    
        # --- CHANGES ---
        if "CPIAUCSL" in aligned_raw:
            cpi = pd.Series(aligned_raw["CPIAUCSL"])
            # Assuming ~21 trading days per month for daily shifted lookbacks
            # A more robust method would calculate this on the monthly grid then merge_asof.
            # For this engine, we'll proxy monthly shifts using ~21 days.
            if self.definitions["cpi_change_1m"].status == "Active":
                res["cpi_change_1m"] = (cpi / cpi.shift(21)) - 1
            if self.definitions["cpi_change_12m"].status == "Active":
                res["cpi_change_12m"] = (cpi / cpi.shift(252)) - 1
                
        if "UNRATE" in aligned_raw:
            unr = pd.Series(aligned_raw["UNRATE"])
            if self.definitions["unrate_change_3m"].status == "Active":
                res["unrate_change_3m"] = unr - unr.shift(63)
                
        # --- SPREADS ---
        if "GS10" in aligned_raw and "FEDFUNDS" in aligned_raw:
            if self.definitions["spread_10y_ff"].status == "Active":
                res["spread_10y_ff"] = aligned_raw["GS10"] - aligned_raw["FEDFUNDS"]
                
        # --- MOMENTUM / VOLATILITY ---
        if "cpi_change_1m" in res.columns:
            if self.definitions["cpi_volatility_12m"].status == "Active":
                # Rolling std of the 1m changes over 252 days
                res["cpi_volatility_12m"] = res["cpi_change_1m"].rolling(window=252, min_periods=252).std()
                
        return res

    def get_feature_quality(self, features_df: pd.DataFrame) -> Dict[str, float]:
        if features_df.empty: return {}
        quality = {}
        total = len(features_df)
        cols = [c for c in features_df.columns if c != "original_timestamp"]
        for col in cols:
            quality[col] = (features_df[col].isna().sum() / total) * 100
        return quality
