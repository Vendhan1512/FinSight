import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import logging
from typing import Dict, Any, List, Optional

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

logger = logging.getLogger(__name__)

class MacroeconomicEngine:
    """
    Computes rigorous relationships between market returns and macroeconomic indicators,
    strictly enforcing Point-in-Time (PIT) availability and multiple-comparison correction.
    """
    def __init__(self, output_dir: str = "output/eda"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.lags_to_test = [0, 1, 3, 6, 12] # Months
        self.alpha = 0.05

    def align_point_in_time(self, market_df: pd.DataFrame, fred_raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aligns market data strictly to when macroeconomic data was PUBLISHED (realtime_start).
        """
        if market_df.empty or fred_raw_df.empty:
            return pd.DataFrame()
            
        # We need the raw fred data to have 'realtime_start', 'series_id', 'value'.
        # Assuming fred_raw_df is the RAW EconomicObservation table (not AnalyticalFRED which lost realtime_start for simplicity).
        # We pivot it based on realtime_start.
        
        # Sort by realtime_start
        fred_raw_df = fred_raw_df.sort_values("realtime_start")
        
        # Keep the latest observation for a specific series available on a specific publication date
        fred_raw_df = fred_raw_df.drop_duplicates(subset=["realtime_start", "series_id"], keep="last")
        
        # Pivot so columns are series_ids and index is realtime_start
        macro = fred_raw_df.pivot(index="realtime_start", columns="series_id", values="value")
        
        # Resample macro to end of month based on publication date
        macro = macro.resample('ME').last()
        
        # Resample market log_returns to monthly sums
        market_df = market_df.copy()
        market_df.set_index("original_timestamp", inplace=True)
        market = market_df[["log_return"]].resample('ME').sum()
        
        # Join on the month end
        # This guarantees we only compare a month's market return to macro data that was PUBLISHED on or before that month end.
        aligned = market.join(macro, how="inner")
        aligned.replace([np.inf, -np.inf], np.nan, inplace=True)
        return aligned

    def compute_lagged_correlations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes contemporaneous and lagged correlations, applying Bonferroni correction.
        """
        results = []
        macro_cols = [c for c in df.columns if c != "log_return"]
        
        # Bonferroni correction: Divide alpha by total number of statistical tests
        total_tests = len(macro_cols) * len(self.lags_to_test)
        adjusted_alpha = self.alpha / total_tests if total_tests > 0 else self.alpha
        
        for col in macro_cols:
            for lag in self.lags_to_test:
                # To test if Macro leads the Market by 'lag' months, we shift the Market Returns BACKWARDS.
                # E.g. lag=1 means we compare Jan Macro to Feb Market (Market shifted back 1 row to align with Jan Macro)
                shifted_market = df["log_return"].shift(-lag)
                
                valid = pd.DataFrame({"macro": df[col], "market": shifted_market}).dropna()
                n = len(valid)
                
                if n < 30:
                    continue
                    
                r, p = stats.pearsonr(valid["macro"], valid["market"])
                rho, p_rho = stats.spearmanr(valid["macro"], valid["market"])
                
                is_significant = p < adjusted_alpha
                
                results.append({
                    "Indicator": col,
                    "Lag_Months": lag,
                    "N": n,
                    "Pearson_r": r,
                    "P_Value": p,
                    "Bonferroni_Alpha": adjusted_alpha,
                    "Significant": is_significant,
                    "Spearman_rho": rho
                })
                
        return pd.DataFrame(results)

    def generate_correlogram(self, df: pd.DataFrame, symbol: str) -> Optional[str]:
        if not HAS_PLOT or df.empty:
            return None
            
        # Filter to just Pearson_r
        plot_df = df.pivot(index="Indicator", columns="Lag_Months", values="Pearson_r")
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(plot_df, annot=True, cmap="coolwarm", center=0, vmin=-1, vmax=1, fmt=".2f")
        plt.title(f"Macroeconomic Lagged Correlogram: {symbol} Returns\n(Lag N = Macro leads Market by N months)")
        plt.xlabel("Lag (Months)")
        plt.ylabel("Economic Indicator")
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, f"{symbol}_macro_correlogram.png")
        plt.savefig(filepath)
        plt.close()
        
        return filepath

    def run_analysis(self, market_df: pd.DataFrame, fred_raw_df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        
        aligned_df = self.align_point_in_time(market_df, fred_raw_df)
        
        if aligned_df.empty:
            raise ValueError("No overlapping data found between market and macro publication dates.")
            
        lag_report = self.compute_lagged_correlations(aligned_df)
        
        if lag_report.empty:
            raise ValueError("Insufficient data to compute lag correlations.")
            
        csv_path = os.path.join(self.output_dir, f"{symbol}_macro_lags.csv")
        lag_report.to_csv(csv_path, index=False)
        
        plot_path = self.generate_correlogram(lag_report, symbol)
        
        return {
            "observations_used": len(aligned_df),
            "report_path": csv_path,
            "plot_path": plot_path,
            "lag_data": lag_report
        }
