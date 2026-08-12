import pandas as pd
import numpy as np
import logging
from typing import Dict
from ml.features.fundamental.definitions import FUNDAMENTAL_FEATURES

logger = logging.getLogger(__name__)

class ConceptMapper:
    """
    Maps diverse SEC XBRL tags into standardized internal concepts.
    """
    MAPPING = {
        "revenue": ["Revenues", "SalesRevenueNet", "RevenuesNetOfInterestExpense", "SalesRevenueServicesNet"],
        "net_income": ["NetIncomeLoss", "ProfitLoss"],
        "operating_income": ["OperatingIncomeLoss"],
        "assets": ["Assets"],
        "liabilities": ["Liabilities", "LiabilitiesCurrent"], # Simplified for demonstration
        "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
    }

    @classmethod
    def map_concept(cls, raw_tag: str) -> str:
        for standard_concept, raw_tags in cls.MAPPING.items():
            if raw_tag in raw_tags:
                return standard_concept
        return "unknown"


class FundamentalFeatureEngine:
    """
    Computes fundamental financial ratios and growth metrics.
    STRICTLY enforces Point-In-Time (PIT) integrity by only using filing_date.
    """
    def __init__(self):
        self.definitions = {d.feature_name: d for d in FUNDAMENTAL_FEATURES}

    def _safe_divide(self, numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        """Safely divides two series, returning NaN where denominator is 0 or NaN."""
        return numerator.where(denominator != 0, np.nan) / denominator.replace(0, np.nan)

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Receives a DataFrame containing raw SEC facts joined with filings.
        Must contain: 'filing_date', 'concept', 'value', 'end_date'
        """
        if df.empty or "filing_date" not in df.columns or "concept" not in df.columns:
            logger.warning("Empty dataframe or missing required SEC columns.")
            return pd.DataFrame()
            
        # 1. Concept Mapping
        df["standard_concept"] = df["concept"].apply(ConceptMapper.map_concept)
        
        # 2. Point-in-Time Enforcement
        # We must group by filing_date. If a company filed an amendment later, 
        # that fact becomes available ONLY on that later filing_date.
        # We pivot the data so each row is a unique filing_date with the concepts as columns.
        
        # Sort by end_date and filing_date to ensure we get the most recently filed version of a fact
        # for a given period if there are duplicates on the same filing date.
        df = df.sort_values(by=["end_date", "filing_date"])
        
        # Pivot
        pivot_df = df.pivot_table(
            index="filing_date",
            columns="standard_concept",
            values="value",
            aggfunc="last" # Take the latest fact if multiple exist on same day
        ).reset_index()
        
        # Ensure it's chronological by availability
        pivot_df = pivot_df.sort_values(by="filing_date").copy()
        
        # The result dataframe (using filing_date as the timestamp to guarantee PIT)
        res = pd.DataFrame({"original_timestamp": pivot_df["filing_date"]})
        
        # Ensure standard concepts exist as columns (fill missing with NaN)
        for concept in ConceptMapper.MAPPING.keys():
            if concept not in pivot_df.columns:
                pivot_df[concept] = np.nan
                
        # --- GROWTH (YoY assumes 4 quarters lookback) ---
        for feat in ["revenue_growth_yoy", "net_income_growth_yoy", "asset_growth_yoy"]:
            if self.definitions[feat].status == "Active":
                base_col = feat.split("_growth")[0]
                res[feat] = (pivot_df[base_col] / pivot_df[base_col].shift(4)) - 1
                
        # --- MARGINS ---
        if self.definitions["operating_margin"].status == "Active":
            res["operating_margin"] = self._safe_divide(pivot_df["operating_income"], pivot_df["revenue"])
            
        if self.definitions["net_margin"].status == "Active":
            res["net_margin"] = self._safe_divide(pivot_df["net_income"], pivot_df["revenue"])
            
        # --- PROFITABILITY ---
        if self.definitions["roa"].status == "Active":
            res["roa"] = self._safe_divide(pivot_df["net_income"], pivot_df["assets"])
            
        if self.definitions["roe"].status == "Active":
            res["roe"] = self._safe_divide(pivot_df["net_income"], pivot_df["equity"])
            
        if self.definitions["asset_turnover"].status == "Active":
            res["asset_turnover"] = self._safe_divide(pivot_df["revenue"], pivot_df["assets"])
            
        # --- LEVERAGE ---
        if self.definitions["debt_to_equity"].status == "Active":
            res["debt_to_equity"] = self._safe_divide(pivot_df["liabilities"], pivot_df["equity"])
            
        if self.definitions["debt_to_assets"].status == "Active":
            res["debt_to_assets"] = self._safe_divide(pivot_df["liabilities"], pivot_df["assets"])
            
        # Explicit check to prove we skip Valuation
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
