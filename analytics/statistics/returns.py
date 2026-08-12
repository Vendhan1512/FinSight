import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ReturnsAndVolatilityEngine:
    """
    Mathematically rigorous engine for computing returns, volatility, 
    drawdowns, and identifying volatility regimes.
    """
    
    def __init__(self, trading_days_per_year: int = 252):
        self.trading_days_per_year = trading_days_per_year

    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("Time-series is empty.")
            
        if "timestamp" not in df.columns or "close" not in df.columns:
            raise ValueError("DataFrame must contain 'timestamp' and 'close' columns.")
            
        # 1. Date Ordering
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # 2. Duplicate Detection
        if df["timestamp"].duplicated().any():
            raise ValueError("Duplicate timestamps found in the dataset.")
            
        # 3. Missing/Zero/Negative Prices
        if df["close"].isnull().any():
            raise ValueError("Missing 'close' prices detected.")
        if (df["close"] <= 0).any():
            raise ValueError("Zero or negative 'close' prices detected (invalid for log calculations).")
            
        return df

    def compute_all_statistics(self, df: pd.DataFrame, rolling_windows: List[int] = [20, 60, 252]) -> Dict[str, Any]:
        """
        Computes the complete profile of returns, volatility, and drawdowns.
        """
        df = self._validate_data(df.copy())
        
        if len(df) < 2:
            raise ValueError("Insufficient observations to compute returns.")

        # --- RETURNS ---
        # Simple Returns (R_t) = (P_t - P_{t-1}) / P_{t-1}
        df["simple_return"] = df["close"].pct_change()
        
        # Log Returns (r_t) = ln(P_t / P_{t-1})
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        
        # Cumulative Returns = exp(sum(r_t)) - 1
        # Dropping NA for the sum to work properly from day 1
        cum_log_returns = df["log_return"].dropna().cumsum()
        cumulative_return = np.exp(cum_log_returns.iloc[-1]) - 1 if not cum_log_returns.empty else 0.0

        # --- VOLATILITY ---
        # Daily Volatility (stdev of log returns)
        daily_volatility = df["log_return"].std()
        
        # Annualized Volatility
        annualized_volatility = daily_volatility * np.sqrt(self.trading_days_per_year)
        
        # Downside Volatility
        negative_returns = df.loc[df["log_return"] < 0, "log_return"]
        downside_volatility = negative_returns.std() * np.sqrt(self.trading_days_per_year) if len(negative_returns) > 1 else 0.0
        
        # Rolling Volatility
        for w in rolling_windows:
            df[f"volatility_{w}d"] = df["log_return"].rolling(window=w).std() * np.sqrt(self.trading_days_per_year)
            
        # --- DRAWDOWNS ---
        cumulative_max = df["close"].cummax()
        drawdowns = (df["close"] - cumulative_max) / cumulative_max
        max_drawdown = drawdowns.min()
        
        # Identify duration of the max drawdown
        # The trough is the index of the minimum drawdown
        trough_idx = drawdowns.idxmin()
        # The peak is the maximum close price before the trough
        peak_idx = df["close"].iloc[:trough_idx + 1].idxmax() if pd.notna(trough_idx) else None
        
        # Calculate duration in trading observations from peak to trough
        drawdown_duration = (trough_idx - peak_idx) if pd.notna(trough_idx) and pd.notna(peak_idx) else 0

        # --- VOLATILITY REGIMES (using 60d window as default) ---
        regime_stats = {}
        if "volatility_60d" in df.columns and df["volatility_60d"].notna().sum() > 60:
            vol = df["volatility_60d"].dropna()
            p25 = np.percentile(vol, 25)
            p75 = np.percentile(vol, 75)
            
            # Get latest regime
            latest_vol = vol.iloc[-1]
            if latest_vol < p25:
                regime = "Low"
            elif latest_vol > p75:
                regime = "High"
            else:
                regime = "Normal"
                
            regime_stats = {
                "latest_60d_volatility": latest_vol,
                "current_regime": regime,
                "threshold_25th": p25,
                "threshold_75th": p75
            }

        return {
            "total_observations": len(df),
            "start_date": df["timestamp"].iloc[0].strftime("%Y-%m-%d"),
            "end_date": df["timestamp"].iloc[-1].strftime("%Y-%m-%d"),
            "cumulative_return": cumulative_return,
            "annualized_volatility": annualized_volatility,
            "downside_volatility": downside_volatility,
            "max_drawdown": max_drawdown,
            "max_drawdown_duration_obs": drawdown_duration,
            "volatility_regime": regime_stats
        }
