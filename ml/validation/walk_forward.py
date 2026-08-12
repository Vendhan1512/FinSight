import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from datetime import timedelta

from ml.models.factory import ModelFactory
from ml.models.evaluator import EvaluationEngine

logger = logging.getLogger(__name__)

class WalkForwardEngine:
    """
    Executes a strict temporal walk-forward evaluation (rolling or expanding).
    Physically instantiates a fresh Sklearn Pipeline per fold to completely isolate
    preprocessing parameters from future test data.
    """
    def __init__(self, model_name: str, mode: str = "expanding", train_window_days: int = 365*2, step_size_days: int = 90, gap_days: int = 5):
        """
        Args:
            mode: 'expanding' (train starts from 0) or 'rolling' (train is fixed size).
            train_window_days: Initial train size (or fixed size if rolling).
            step_size_days: How many days to evaluate out-of-sample before stepping forward.
            gap_days: Embargo gap to prevent overlapping-label leakage.
        """
        self.model_name = model_name
        self.mode = mode
        self.train_window = timedelta(days=train_window_days)
        self.step_size = timedelta(days=step_size_days)
        self.gap = timedelta(days=gap_days)
        self.is_classification = "classifier" in model_name or "logistic" in model_name

    def evaluate(self, df: pd.DataFrame, feature_cols: List[str], target_col: str, time_col: str = "prediction_time") -> Dict[str, Any]:
        """Runs the walk-forward evaluation and returns detailed robustness metrics."""
        
        df = df.sort_values(time_col).reset_index(drop=True)
        min_time = df[time_col].min()
        max_time = df[time_col].max()
        
        fold_results = []
        all_predictions = []
        
        # Initialize loop bounds
        train_start = min_time
        train_end = train_start + self.train_window
        test_start = train_end + self.gap
        test_end = test_start + self.step_size
        
        fold_idx = 1
        
        logger.info(f"Starting Walk-Forward ({self.mode}). Target range: {min_time.date()} to {max_time.date()}")
        
        while test_start < max_time:
            # Enforce data limits
            if test_end > max_time:
                test_end = max_time
                
            # 1. Slice Data for this fold
            train_mask = (df[time_col] >= train_start) & (df[time_col] < train_end)
            test_mask = (df[time_col] >= test_start) & (df[time_col] < test_end)
            
            train_df = df[train_mask]
            test_df = df[test_mask]
            
            if len(train_df) == 0 or len(test_df) == 0:
                logger.warning(f"Fold {fold_idx} has insufficient data. Stepping forward.")
                self._step_forward(locals()) # Update bounds
                continue
                
            X_train, y_train = train_df[feature_cols], train_df[target_col]
            X_test, y_test = test_df[feature_cols], test_df[target_col]
            
            # 2. Instantiate FRESH Pipeline (Zero Preprocessing Leakage)
            pipeline = ModelFactory.get_model(self.model_name)
            
            # 3. Fit
            pipeline.fit(X_train, y_train)
            
            # 4. Predict
            y_pred = pipeline.predict(X_test)
            y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None
            
            # 5. Evaluate
            if self.is_classification:
                metrics = EvaluationEngine.evaluate_classification(y_test, y_pred, y_prob)
                primary_metric = metrics.get("PR_AUC", metrics.get("F1", 0))
            else:
                metrics = EvaluationEngine.evaluate_regression(y_test, y_pred)
                primary_metric = metrics.get("RMSE", 0) # Note: lower is better for RMSE
                
            logger.info(f"Fold {fold_idx} ({test_start.date()} to {test_end.date()}): {primary_metric:.4f}")
            
            fold_results.append({
                "fold_index": fold_idx,
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
                "metrics": metrics,
                "primary_metric": primary_metric
            })
            
            # 6. Store physical predictions
            preds = pd.DataFrame({
                "prediction_time": test_df[time_col].values,
                "prediction": y_pred,
                "actual_outcome": y_test.values,
                "fold_index": fold_idx
            })
            if y_prob is not None:
                preds["prediction_prob"] = y_prob
                
            all_predictions.append(preds)
            
            # 7. Step Forward
            if self.mode == "rolling":
                train_start += self.step_size
            # If expanding, train_start remains min_time
            
            train_end += self.step_size
            test_start = train_end + self.gap
            test_end = test_start + self.step_size
            fold_idx += 1
            
        # Compile final robustness report
        if not fold_results:
            raise ValueError("No valid folds completed.")
            
        # Determine best/worst fold (Handle minimization for RMSE vs maximization for AUC)
        is_minimization = not self.is_classification and "RMSE" in fold_results[0]["metrics"]
        
        if is_minimization:
            best_fold = min(fold_results, key=lambda x: x["primary_metric"])
            worst_fold = max(fold_results, key=lambda x: x["primary_metric"])
        else:
            best_fold = max(fold_results, key=lambda x: x["primary_metric"])
            worst_fold = min(fold_results, key=lambda x: x["primary_metric"])
            
        primary_scores = [f["primary_metric"] for f in fold_results]
        
        report = {
            "folds_completed": len(fold_results),
            "mean_primary_metric": np.nanmean(primary_scores),
            "std_primary_metric": np.nanstd(primary_scores), # Variability/Stability
            "best_fold_index": best_fold["fold_index"],
            "worst_fold_index": worst_fold["fold_index"],
            "fold_details": fold_results,
            "predictions_df": pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()
        }
        
        return report

    def _step_forward(self, bounds):
        """Helper to advance bounds if data is empty"""
        if self.mode == "rolling":
            bounds['train_start'] += self.step_size
        bounds['train_end'] += self.step_size
        bounds['test_start'] = bounds['train_end'] + self.gap
        bounds['test_end'] = bounds['test_start'] + self.step_size
