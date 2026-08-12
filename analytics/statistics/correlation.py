import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """
    Computes rigorous statistical correlations, specifically handling 
    multi-frequency alignment and preventing leakage.
    """
    def __init__(self, output_dir: str = "output/eda"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.MIN_OBSERVATIONS = 30

    def align_market_data(self, market_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Aligns daily market returns for multiple symbols into a single wide DataFrame.
        """
        aligned_df = pd.DataFrame()
        
        for symbol, df in market_dfs.items():
            if df.empty or "log_return" not in df.columns:
                continue
                
            temp = df[["original_timestamp", "log_return"]].copy()
            temp.rename(columns={"log_return": symbol}, inplace=True)
            temp.set_index("original_timestamp", inplace=True)
            
            if aligned_df.empty:
                aligned_df = temp
            else:
                aligned_df = aligned_df.join(temp, how="outer")
                
        # Forward fill is DANGEROUS for correlation. We leave as NaN.
        return aligned_df

    def align_market_with_fred(self, market_df: pd.DataFrame, fred_df: pd.DataFrame) -> pd.DataFrame:
        """
        Strict alignment: Down-samples daily market log_returns to monthly sums
        before joining with monthly FRED data to prevent forward-fill leakage.
        """
        if market_df.empty or fred_df.empty:
            return pd.DataFrame()

        # Market is indexed by exact datetime. Resample to Month End, summing the log returns.
        monthly_market = market_df.resample('ME').sum()
        
        # FRED is indexed by date (often month start). Resample to Month End, using last observation.
        fred_df_indexed = fred_df.copy()
        if "original_timestamp" in fred_df_indexed.columns:
            fred_df_indexed.set_index("original_timestamp", inplace=True)
            
        monthly_fred = fred_df_indexed.resample('ME').last()
        
        # Join
        combined = monthly_market.join(monthly_fred, how="inner")
        
        # Drop rows where any of the core indicators are missing entirely
        combined.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        return combined

    def compute_pairwise(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes pairwise Pearson and Spearman correlations, tracking observation counts.
        Returns a detailed report.
        """
        cols = df.columns
        results = []
        
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col1 = cols[i]
                col2 = cols[j]
                
                # Filter to overlapping non-null pairs
                valid = df[[col1, col2]].dropna()
                n = len(valid)
                
                if n < self.MIN_OBSERVATIONS:
                    results.append({
                        "Asset_A": col1, "Asset_B": col2, "N": n,
                        "Pearson_r": np.nan, "Pearson_p": np.nan,
                        "Spearman_rho": np.nan, "Spearman_p": np.nan,
                        "Note": "Insufficient Data"
                    })
                    continue
                    
                p_r, p_p = stats.pearsonr(valid[col1], valid[col2])
                s_r, s_p = stats.spearmanr(valid[col1], valid[col2])
                
                results.append({
                    "Asset_A": col1, "Asset_B": col2, "N": n,
                    "Pearson_r": p_r, "Pearson_p": p_p,
                    "Spearman_rho": s_r, "Spearman_p": s_p,
                    "Note": "Valid"
                })
                
        return pd.DataFrame(results)

    def generate_heatmap(self, df: pd.DataFrame, prefix: str) -> Optional[str]:
        if not HAS_PLOT:
            return None
            
        corr = df.corr(method="pearson", min_periods=self.MIN_OBSERVATIONS)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, vmin=-1, vmax=1, fmt=".2f",
                    cbar_kws={'label': 'Pearson Correlation (r)'})
        
        plt.title(f"Correlation Matrix Heatmap\n(Note: Correlation != Causation)", pad=20)
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, f"{prefix}_correlation_matrix.png")
        plt.savefig(filepath)
        plt.close()
        
        return filepath

    def run_analysis(self, market_dfs: Dict[str, pd.DataFrame], fred_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Orchestrates alignment, correlation math, and visualization generation.
        """
        aligned_market = self.align_market_data(market_dfs)
        
        if fred_df is not None and not fred_df.empty:
            logger.info("Aligning multi-frequency data (Daily Market -> Monthly FRED)")
            final_df = self.align_market_with_fred(aligned_market, fred_df)
            prefix = "cross_asset_macro"
        else:
            final_df = aligned_market
            prefix = "cross_asset_market"
            
        if final_df.empty:
            raise ValueError("No overlapping data found for correlation analysis.")
            
        pairwise_report = self.compute_pairwise(final_df)
        
        # Save CSV
        csv_path = os.path.join(self.output_dir, f"{prefix}_pairwise_correlations.csv")
        pairwise_report.to_csv(csv_path, index=False)
        
        # Generate Plot
        plot_path = self.generate_heatmap(final_df, prefix)
        
        return {
            "observations_used": len(final_df),
            "report_path": csv_path,
            "plot_path": plot_path,
            "pairwise_data": pairwise_report
        }
