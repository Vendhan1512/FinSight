import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List

from ml.models.factory import ModelFactory
from ml.models.evaluator import EvaluationEngine
from ml.validation.cv import EmbargoTimeSeriesSplit

logger = logging.getLogger(__name__)

try:
    import optuna
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    logger.warning("optuna not installed. Hyperparameter optimization will be unavailable.")

class HyperparameterOptimizer:
    """
    Executes an Optuna hyperparameter study using Embargo Time-Series Cross Validation.
    """
    def __init__(self, model_name: str, cv_folds: int = 3, cv_gap: int = 5):
        if not HAS_OPTUNA:
            raise ImportError("Optuna is not installed.")
            
        self.model_name = model_name
        self.cv_folds = cv_folds
        self.cv_gap = cv_gap
        self.is_classification = "classifier" in model_name

    def _get_search_space(self, trial) -> Dict[str, Any]:
        """Defines the hyperparameter search space per model."""
        if "xgboost" in self.model_name:
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 2, 8),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0)
            }
        elif "lightgbm" in self.model_name:
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 2, 8),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 10, 50)
            }
        elif "ridge" in self.model_name or "lasso" in self.model_name:
            return {
                "alpha": trial.suggest_float("alpha", 1e-4, 1e2, log=True)
            }
        else:
            raise ValueError(f"No search space defined for {self.model_name}")

    def optimize(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 20, objective_metric: str = "PR_AUC") -> Dict[str, Any]:
        """Runs the optimization study."""
        
        cv = EmbargoTimeSeriesSplit(n_splits=self.cv_folds, gap=self.cv_gap)
        
        # We need to know if we are maximizing or minimizing
        # PR_AUC, R2, Accuracy -> Maximize
        # RMSE, MAE, LogLoss -> Minimize
        if objective_metric in ["RMSE", "MAE", "MedAE", "LogLoss"]:
            direction = "minimize"
        else:
            direction = "maximize"
            
        study = optuna.create_study(direction=direction)
        
        # We convert to numpy for faster indexing in CV
        X_arr = X.values
        y_arr = y.values
        
        def objective(trial):
            params = self._get_search_space(trial)
            
            fold_metrics = []
            
            # Cross Validation Loop
            for train_idx, val_idx in cv.split(X_arr):
                X_train, X_val = X_arr[train_idx], X_arr[val_idx]
                y_train, y_val = y_arr[train_idx], y_arr[val_idx]
                
                pipeline = ModelFactory.get_model(self.model_name, **params)
                
                pipeline.fit(X_train, y_train)
                y_pred = pipeline.predict(X_val)
                
                if self.is_classification:
                    y_prob = pipeline.predict_proba(X_val)[:, 1] if hasattr(pipeline, "predict_proba") else None
                    metrics = EvaluationEngine.evaluate_classification(y_val, y_pred, y_prob)
                else:
                    metrics = EvaluationEngine.evaluate_regression(y_val, y_pred)
                    
                metric_value = metrics.get(objective_metric, np.nan)
                fold_metrics.append(metric_value)
                
            return np.nanmean(fold_metrics)
            
        logger.info(f"Starting Optuna Study for {self.model_name}. Trials: {n_trials}, Metric: {objective_metric}")
        study.optimize(objective, n_trials=n_trials)
        
        return {
            "best_params": study.best_params,
            "best_value": study.best_value,
            "direction": direction,
            "n_trials": len(study.trials)
        }
