import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from ml.features.validation.contracts import FeatureDefinitionContract
from sklearn.feature_selection import mutual_info_regression

logger = logging.getLogger(__name__)

class FeatureSelectionEngine:
    """
    Selects final features for ML training based on Redundancy Clustering
    and Temporal Stability. Only evaluates on training data.
    """
    def __init__(self, correlation_threshold: float = 0.85):
        self.correlation_threshold = correlation_threshold

    def select_features(
        self, 
        train_df: pd.DataFrame, 
        target_col: str,
        contracts: Dict[str, FeatureDefinitionContract]
    ) -> Dict[str, FeatureDefinitionContract]:
        """
        Executes redundancy analysis and temporal stability checks.
        Promotes VALIDATED features to SELECTED or REJECTED.
        """
        if train_df.empty or target_col not in train_df.columns:
            logger.warning("Empty training dataframe or missing target column.")
            return contracts
            
        # Get only VALIDATED features
        valid_features = [f for f, c in contracts.items() if c.status == "VALIDATED" and f in train_df.columns]
        if not valid_features:
            logger.info("No VALIDATED features available for selection.")
            return contracts
            
        # 1. Calculate Mutual Information (MI) for all valid features on the entire train set
        logger.info("Calculating baseline Mutual Information for feature ranking...")
        
        # Drop rows where target is missing
        clean_train = train_df.dropna(subset=[target_col] + valid_features)
        if clean_train.empty:
            logger.error("Dataset is empty after dropping missing target/features.")
            return contracts
            
        mi_scores = mutual_info_regression(clean_train[valid_features], clean_train[target_col])
        mi_series = pd.Series(mi_scores, index=valid_features)
        
        # 2. Redundancy Clustering (Correlation)
        logger.info(f"Running redundancy clustering (Threshold: {self.correlation_threshold})...")
        corr_matrix = clean_train[valid_features].corr().abs()
        
        # Find highly correlated pairs
        redundant_pairs = set()
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                if corr_matrix.iloc[i, j] > self.correlation_threshold:
                    feat_i = corr_matrix.columns[i]
                    feat_j = corr_matrix.columns[j]
                    
                    # Tie-breaker: Keep the one with higher Mutual Information
                    if mi_series[feat_i] > mi_series[feat_j]:
                        loser = feat_j
                        winner = feat_i
                    else:
                        loser = feat_i
                        winner = feat_j
                        
                    redundant_pairs.add((loser, winner))
                    
        # Reject the redundant features
        rejected_redundant = set()
        for loser, winner in redundant_pairs:
            if loser not in rejected_redundant:
                self._reject(contracts[loser], f"Redundant: High correlation with [{winner}]. Lower MI score.")
                rejected_redundant.add(loser)
                
        # 3. Temporal Stability Check
        # Split train set chronologically into 3 folds. Feature must have >0 MI in at least 2 folds.
        # This is a simplified proxy for stability.
        logger.info("Evaluating Temporal Stability...")
        remaining_features = [f for f in valid_features if f not in rejected_redundant]
        
        if len(remaining_features) > 0 and len(clean_train) > 100:
            folds = np.array_split(clean_train, 3)
            
            for feat in remaining_features:
                stable_folds = 0
                for fold in folds:
                    if len(fold) > 10:
                        fold_mi = mutual_info_regression(fold[[feat]], fold[target_col])[0]
                        if fold_mi > 1e-4: # greater than near-zero
                            stable_folds += 1
                            
                if stable_folds < 2:
                    self._reject(contracts[feat], f"Unstable: Failed temporal stability check. Predictive power vanishes in sub-periods.")
                else:
                    contracts[feat].status = "SELECTED"
                    contracts[feat].rejection_reason = None
                    logger.info(f"SELECTED Feature '{feat}' (MI: {mi_series[feat]:.4f})")
                    
        return contracts

    def _reject(self, contract: FeatureDefinitionContract, reason: str):
        contract.status = "REJECTED"
        contract.rejection_reason = reason
        logger.info(f"REJECTED Feature '{contract.feature_name}': {reason}")
