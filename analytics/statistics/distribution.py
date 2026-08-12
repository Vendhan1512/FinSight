import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import logging
from typing import Dict, Any, Optional

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

logger = logging.getLogger(__name__)

class DistributionAndOutlierEngine:
    def __init__(self, output_dir: str = "output/eda"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "log_return" not in df.columns:
            raise ValueError("DataFrame must contain 'log_return' column.")
            
        # Drop missing values solely for the distribution calculations
        df = df.dropna(subset=["log_return"]).copy()
        
        if len(df) < 30:
            raise ValueError("Insufficient observations (N < 30) for reliable distribution analysis.")
            
        return df

    def compute_descriptive_stats(self, returns: pd.Series) -> Dict[str, float]:
        q25 = returns.quantile(0.25)
        q75 = returns.quantile(0.75)
        
        return {
            "mean": returns.mean(),
            "median": returns.median(),
            "variance": returns.var(),
            "std_dev": returns.std(),
            "min": returns.min(),
            "max": returns.max(),
            "q25": q25,
            "q75": q75,
            "iqr": q75 - q25,
            "skewness": returns.skew(),
            "kurtosis": returns.kurtosis() # Fisher's kurtosis (excess kurtosis, normal = 0)
        }

    def compute_normality_tests(self, returns: pd.Series) -> Dict[str, Any]:
        results = {}
        n = len(returns)
        
        # Jarque-Bera
        jb_stat, jb_p = stats.jarque_bera(returns)
        results["jarque_bera"] = {"stat": jb_stat, "p_value": jb_p}
        
        # Shapiro-Wilk (only run if N < 5000 due to extreme sensitivity)
        if n < 5000:
            sw_stat, sw_p = stats.shapiro(returns)
            results["shapiro_wilk"] = {"stat": sw_stat, "p_value": sw_p}
        else:
            results["shapiro_wilk"] = {"stat": None, "p_value": None, "note": "N >= 5000 (Omitted due to oversensitivity)"}
            
        return results

    def classify_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        returns = df["log_return"]
        
        # 1. Standard Z-Score
        mean = returns.mean()
        std = returns.std()
        df["z_score"] = (returns - mean) / std
        
        # 2. Robust Modified Z-Score (using Median Absolute Deviation)
        median = returns.median()
        mad = stats.median_abs_deviation(returns)
        # 0.6745 is the constant for normal distribution consistency
        df["robust_z_score"] = 0.6745 * (returns - median) / mad if mad > 0 else 0
        
        # Classification
        conditions = [
            (df["robust_z_score"].abs() >= 3),
            (df["robust_z_score"].abs() >= 2) & (df["robust_z_score"].abs() < 3)
        ]
        choices = ["extreme", "unusual"]
        df["outlier_class"] = np.select(conditions, choices, default="normal")
        
        return df

    def generate_visualizations(self, df: pd.DataFrame, symbol: str) -> Optional[str]:
        if not HAS_PLOT:
            logger.warning("matplotlib/seaborn not installed. Skipping visualizations.")
            return None
            
        returns = df["log_return"]
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(f"Return Distribution Analysis: {symbol}", fontsize=16)
        
        # 1. Histogram & KDE vs Normal
        sns.histplot(returns, stat="density", bins=50, kde=True, ax=axes[0], color="blue", label="Actual")
        
        # Plot theoretical normal
        xmin, xmax = axes[0].get_xlim()
        x = np.linspace(xmin, xmax, 100)
        p = stats.norm.pdf(x, returns.mean(), returns.std())
        axes[0].plot(x, p, 'k', linewidth=2, label="Normal Dist")
        
        axes[0].set_title("Distribution vs Normal")
        axes[0].legend()
        
        # 2. Q-Q Plot
        stats.probplot(returns, dist="norm", plot=axes[1])
        axes[1].set_title("Q-Q Plot (Fat Tail Check)")
        
        # 3. Outlier Scatter
        colors = {"normal": "gray", "unusual": "orange", "extreme": "red"}
        axes[2].scatter(df["timestamp"], df["log_return"], c=df["outlier_class"].map(colors), alpha=0.6, s=10)
        axes[2].set_title("Time Series Outliers (Robust Z)")
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, f"{symbol}_distribution.png")
        plt.savefig(filepath)
        plt.close()
        
        return filepath

    def run_analysis(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Runs the full pipeline, saves reports to disk, and returns the stats.
        """
        df = self._validate_data(df)
        
        # Compute Stats
        desc_stats = self.compute_descriptive_stats(df["log_return"])
        norm_tests = self.compute_normality_tests(df["log_return"])
        
        # Classify Outliers
        df = self.classify_outliers(df)
        
        outlier_counts = df["outlier_class"].value_counts().to_dict()
        
        # Save Outlier Report
        report_path = os.path.join(self.output_dir, f"{symbol}_outliers.csv")
        # Save all unusual and extreme
        outliers_only = df[df["outlier_class"] != "normal"].sort_values(by="robust_z_score", key=abs, ascending=False)
        outliers_only[["timestamp", "symbol", "log_return", "z_score", "robust_z_score", "outlier_class"]].to_csv(report_path, index=False)
        
        # Visualizations
        plot_path = self.generate_visualizations(df, symbol)
        
        return {
            "n_obs": len(df),
            "descriptive": desc_stats,
            "normality": norm_tests,
            "outliers": outlier_counts,
            "report_path": report_path,
            "plot_path": plot_path
        }
