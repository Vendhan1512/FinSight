import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TargetEngine:
    """
    Computes supervised learning targets while strictly preserving chronological boundaries.
    """
    
    @staticmethod
    def calculate_targets(
        price_df: pd.DataFrame, 
        horizon_days: int, 
        target_type: str = "regression_return"
    ) -> pd.DataFrame:
        """
        Takes a dataframe of (symbol, original_timestamp, close).
        Returns a dataframe mapping feature_timestamp (T) to target_end_timestamp (T+h)
        and the computed target_value.
        
        Args:
            price_df: DataFrame with ['symbol', 'original_timestamp', 'close']
            horizon_days: e.g., 5, 20
            target_type: 'regression_return' or 'classification_direction'
        """
        if price_df.empty or "close" not in price_df.columns:
            logger.error("Price dataframe is empty or missing 'close' column.")
            return pd.DataFrame()
            
        # Ensure chronological sorting per symbol
        df = price_df.sort_values(by=["symbol", "original_timestamp"]).copy()
        
        # We need the future price and the future timestamp (T+h)
        df["future_close"] = df.groupby("symbol")["close"].shift(-horizon_days)
        df["target_end_time"] = df.groupby("symbol")["original_timestamp"].shift(-horizon_days)
        
        # Calculate Regression Target: Price[T+h] / Price[T] - 1
        df["target_value"] = (df["future_close"] / df["close"]) - 1
        
        # If classification, map return to binary {0, 1}
        if target_type == "classification_direction":
            # 1 if return > 0, else 0. Note: we only map non-null returns.
            df["target_value"] = df["target_value"].apply(lambda x: 1.0 if x > 0 else (0.0 if not pd.isna(x) else np.nan))
            
        # Drop rows where we don't have a future observation (end of the timeseries)
        df = df.dropna(subset=["target_value", "target_end_time"])
        
        # Explicitly separate the timestamps
        df = df.rename(columns={"original_timestamp": "prediction_time"})
        
        return df[["symbol", "prediction_time", "target_end_time", "target_value"]]
