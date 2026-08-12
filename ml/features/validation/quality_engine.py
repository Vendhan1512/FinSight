import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from ml.features.validation.contracts import FeatureDefinitionContract

logger = logging.getLogger(__name__)

class FeatureQualityEngine:
    """
    Rigorously audits generated machine learning features for mathematical validity.
    Modifies the lifecycle status of FeatureDefinitionContracts.
    """
    def __init__(self, missingness_threshold: float = 0.30):
        self.missingness_threshold = missingness_threshold

    def audit_features(
        self, 
        features_df: pd.DataFrame, 
        contracts: Dict[str, FeatureDefinitionContract]
    ) -> Dict[str, FeatureDefinitionContract]:
        """
        Runs mathematical checks on all features. If a feature fails, its status 
        in the contract dictionary is changed to REJECTED with a reason.
        """
        if features_df.empty:
            logger.warning("Empty dataframe provided to Quality Engine.")
            return contracts
            
        total_rows = len(features_df)
        ignore_cols = ["original_timestamp", "symbol", "prediction_timestamp"]
        
        for feature_name, contract in contracts.items():
            if feature_name not in features_df.columns:
                continue
                
            # If already rejected/unavailable, skip
            if contract.status in ["REJECTED", "Unavailable"]:
                continue
                
            series = features_df[feature_name]
            
            # 1. Missingness Check
            missing_rate = series.isna().sum() / total_rows
            if missing_rate > self.missingness_threshold:
                self._reject(contract, f"Missingness rate ({missing_rate:.1%}) exceeds threshold ({self.missingness_threshold:.1%})")
                continue
                
            # Drop NAs for remaining mathematical checks
            clean_series = series.dropna()
            if len(clean_series) == 0:
                self._reject(contract, "All values are NaN after initial missingness pass.")
                continue
                
            # 2. Infinite Values Check
            if np.isinf(clean_series).any():
                self._reject(contract, "Contains infinite values (inf or -inf) that break model training.")
                continue
                
            # 3. Constant Variance Check (Zero Variance)
            std_dev = clean_series.std()
            if pd.isna(std_dev) or std_dev == 0:
                self._reject(contract, "Constant Variance (Standard Deviation is 0). Zero predictive power.")
                continue
                
            # 4. Near-Zero Variance (Over 99% of values are identical)
            most_common_freq = clean_series.value_counts(normalize=True).iloc[0]
            if most_common_freq > 0.99:
                self._reject(contract, f"Near-Zero Variance: {most_common_freq:.1%} of observations have the identical value.")
                continue
                
            # 5. Extreme Values (Simple heuristic: max > 100 * 99th percentile, excluding negative bounds for simplicity here)
            p99 = clean_series.quantile(0.99)
            # Only run extreme check if p99 is notably positive to avoid dividing by near-zero
            if p99 > 0.01 and clean_series.max() > (100 * p99):
                 self._reject(contract, f"Extreme Outliers Detected: Max value ({clean_series.max()}) is > 100x the 99th percentile ({p99}).")
                 continue
                 
            # If it passes all checks, promote to VALIDATED
            if contract.status == "CANDIDATE" or contract.status == "Active":
                contract.status = "VALIDATED"
                contract.rejection_reason = None
                
        return contracts

    def _reject(self, contract: FeatureDefinitionContract, reason: str):
        contract.status = "REJECTED"
        contract.rejection_reason = reason
        logger.info(f"REJECTED Feature '{contract.feature_name}': {reason}")
