import os
import json
import logging
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional

from analytics.statistics.returns import ReturnsAndVolatilityEngine
from analytics.statistics.distribution import DistributionAndOutlierEngine
from analytics.statistics.correlation import CorrelationEngine
from analytics.statistics.macro import MacroeconomicEngine
from analytics.statistics.hypothesis import HypothesisTestingEngine

logger = logging.getLogger(__name__)

class EDAReportEngine:
    """
    Orchestrates the entire Phase 2 analytical suite to generate reproducible, 
    deterministic, hardcode-free statistical intelligence reports.
    """
    def __init__(self, output_dir: str = "output/reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.version = "1.0.0"

    def _generate_metadata(self, symbol: str, dataset_version: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "report_type": "EDA_Statistical_Intelligence",
            "symbol": symbol,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "analysis_version": self.version,
            "dataset_version": dataset_version,
            "parameters": params
        }

    def _run_returns_and_vol(self, df: pd.DataFrame) -> Dict[str, Any]:
        engine = ReturnsAndVolatilityEngine()
        try:
            return engine.compute_all_statistics(df)
        except Exception as e:
            logger.error(f"Returns engine failed: {e}")
            return {"error": str(e)}

    def _run_distribution(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        engine = DistributionAndOutlierEngine(output_dir=os.path.join(self.output_dir, "plots"))
        try:
            # Note: run_analysis returns plot paths which we can include in markdown
            res = engine.run_analysis(df, symbol)
            # We don't need to embed the plot paths in the pure JSON stats if we don't want, 
            # but it's good for the markdown renderer.
            return res
        except Exception as e:
            logger.error(f"Distribution engine failed: {e}")
            return {"error": str(e)}

    def _run_correlation(self, df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame], symbol: str, bench_sym: str) -> Dict[str, Any]:
        if benchmark_df is None or benchmark_df.empty:
            return {"note": "No benchmark provided"}
            
        engine = CorrelationEngine(output_dir=os.path.join(self.output_dir, "plots"))
        dfs = {symbol: df, bench_sym: benchmark_df}
        try:
            res = engine.run_analysis(dfs)
            # Convert pairwise dataframe to dict
            if "pairwise_data" in res:
                res["pairwise_data"] = res["pairwise_data"].to_dict(orient="records")
            return res
        except Exception as e:
            logger.error(f"Correlation engine failed: {e}")
            return {"error": str(e)}

    def _run_macro(self, df: pd.DataFrame, fred_raw_df: Optional[pd.DataFrame], symbol: str) -> Dict[str, Any]:
        if fred_raw_df is None or fred_raw_df.empty:
            return {"note": "No macro data provided"}
            
        engine = MacroeconomicEngine(output_dir=os.path.join(self.output_dir, "plots"))
        try:
            res = engine.run_analysis(df, fred_raw_df, symbol)
            if "lag_data" in res:
                res["lag_data"] = res["lag_data"].to_dict(orient="records")
            return res
        except Exception as e:
            logger.error(f"Macro engine failed: {e}")
            return {"error": str(e)}

    def _run_hypothesis(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "rolling_vol_annualized" not in df.columns:
            return {"note": "Volatility data missing; cannot run regime hypothesis."}
            
        vol = df["rolling_vol_annualized"].dropna()
        if vol.empty:
            return {"note": "Volatility data missing."}
            
        q25, q75 = vol.quantile(0.25), vol.quantile(0.75)
        high = df[df["rolling_vol_annualized"] > q75]["log_return"].dropna()
        low = df[df["rolling_vol_annualized"] < q25]["log_return"].dropna()
        
        engine = HypothesisTestingEngine()
        try:
            res = engine.run_two_sample_test(high, low)
            res["experiment_name"] = "volatility_regimes"
            return res
        except Exception as e:
            logger.error(f"Hypothesis engine failed: {e}")
            return {"error": str(e)}

    def generate_report_payload(self, 
                              symbol: str, 
                              market_df: pd.DataFrame, 
                              benchmark_df: Optional[pd.DataFrame] = None, 
                              benchmark_symbol: Optional[str] = None,
                              fred_raw_df: Optional[pd.DataFrame] = None,
                              params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes all analytical engines and bundles the results deterministically.
        """
        if params is None:
            params = {}
            
        dataset_version = f"{symbol}_analytical"
        
        report = {
            "metadata": self._generate_metadata(symbol, dataset_version, params),
            "data_coverage": {
                "observations": len(market_df),
                "start_date": market_df["original_timestamp"].min().isoformat() if not market_df.empty else None,
                "end_date": market_df["original_timestamp"].max().isoformat() if not market_df.empty else None,
            },
            "returns_and_volatility": self._run_returns_and_vol(market_df),
            "distribution_and_outliers": self._run_distribution(market_df, symbol),
            "correlation": self._run_correlation(market_df, benchmark_df, symbol, benchmark_symbol) if benchmark_symbol else {"note": "No benchmark"},
            "macro_relationships": self._run_macro(market_df, fred_raw_df, symbol),
            "hypothesis_testing": self._run_hypothesis(market_df),
            "limitations": [
                "Correlation does not imply causation.",
                "Volatility regimes are defined endogenously by historical distributions.",
                "Multiple comparisons in macro analysis use strict Bonferroni corrections, which may increase Type II errors."
            ],
            "methodology": "Phase 2 Automated EDA Engine (v1.0.0)"
        }
        
        return report

    def save_json(self, payload: Dict[str, Any], symbol: str) -> str:
        filepath = os.path.join(self.output_dir, f"{symbol}_eda_report.json")
        # Handle numpy floats for json serialization
        def default_serializer(obj):
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if pd.isna(obj): return None
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            
        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=4, default=default_serializer)
            
        return filepath

    def save_markdown(self, payload: Dict[str, Any], symbol: str) -> str:
        filepath = os.path.join(self.output_dir, f"{symbol}_eda_report.md")
        
        md = f"# Automated EDA & Statistical Intelligence Report: {symbol}\n\n"
        md += f"**Generated At:** {payload['metadata']['generated_at']}\n"
        md += f"**Analysis Version:** {payload['metadata']['analysis_version']}\n\n"
        
        md += "## 1. Executive Data Summary\n"
        md += f"- **Observations:** {payload['data_coverage']['observations']}\n"
        md += f"- **Date Range:** {payload['data_coverage']['start_date']} to {payload['data_coverage']['end_date']}\n\n"
        
        if "error" not in payload["returns_and_volatility"]:
            rv = payload["returns_and_volatility"]
            md += "## 2. Returns & Volatility\n"
            md += f"- **Cumulative Return:** {rv.get('cumulative_return', 'N/A'):.4f}\n"
            md += f"- **Max Drawdown:** {rv.get('max_drawdown', 'N/A'):.4f} (Duration: {rv.get('max_drawdown_duration_obs', 'N/A')} obs)\n"
            md += f"- **Volatility Regime:** {rv.get('volatility_regime', 'N/A')}\n\n"
            
        if "error" not in payload["distribution_and_outliers"]:
            dist = payload["distribution_and_outliers"]
            desc = dist.get("descriptive", {})
            norm = dist.get("normality", {}).get("jarque_bera", {})
            md += "## 3. Distribution & Outliers\n"
            md += f"- **Skewness:** {desc.get('skewness', 'N/A'):.4f}\n"
            md += f"- **Kurtosis:** {desc.get('kurtosis', 'N/A'):.4f}\n"
            md += f"- **Jarque-Bera p-value:** {norm.get('p_value', 'N/A')}\n"
            md += "- **Outliers (Robust MAD):**\n"
            outs = dist.get("outliers", {})
            md += f"  - Normal: {outs.get('normal', 0)}\n"
            md += f"  - Unusual: {outs.get('unusual', 0)}\n"
            md += f"  - Extreme: {outs.get('extreme', 0)}\n\n"
            if dist.get("plot_path"):
                md += f"![Distribution Plot]({os.path.abspath(dist['plot_path'])})\n\n"

        if "error" not in payload["hypothesis_testing"] and "note" not in payload["hypothesis_testing"]:
            hyp = payload["hypothesis_testing"]
            md += "## 4. Hypothesis Testing (Volatility Regimes)\n"
            md += f"- **Test Used:** {hyp['test_used']}\n"
            md += f"- **P-Value:** {hyp['p_value']:.4e} (Significant: {hyp['is_statistically_significant']})\n"
            md += f"- **Effect Size ({hyp['effect_size_metric']}):** {hyp['effect_size_value']:.4f}\n\n"
            
        md += "## 5. Methodology & Limitations\n"
        for lim in payload["limitations"]:
            md += f"- {lim}\n"
            
        with open(filepath, 'w') as f:
            f.write(md)
            
        return filepath
