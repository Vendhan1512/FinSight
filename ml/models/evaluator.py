import numpy as np
from typing import Dict, Any
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score, median_absolute_error,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, log_loss, confusion_matrix
)
import logging

logger = logging.getLogger(__name__)

class EvaluationEngine:
    """Computes rigorous out-of-sample metrics for financial ML models."""
    
    @staticmethod
    def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        if len(y_true) == 0 or len(y_pred) == 0:
            return {}
            
        metrics = {
            "MAE": mean_absolute_error(y_true, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            "R2": r2_score(y_true, y_pred),
            "MedAE": median_absolute_error(y_true, y_pred)
        }
        
        # Directional Accuracy (Did the model correctly guess the sign of the return?)
        # 1 if signs match, 0 otherwise
        sign_match = np.sign(y_true) == np.sign(y_pred)
        # Exclude exact zeros to avoid bias
        valid_signs = (y_true != 0) & (y_pred != 0)
        
        if valid_signs.sum() > 0:
            metrics["Directional_Accuracy"] = sign_match[valid_signs].mean()
        else:
            metrics["Directional_Accuracy"] = np.nan
            
        return metrics
        
    @staticmethod
    def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, float]:
        if len(y_true) == 0 or len(y_pred) == 0:
            return {}
            
        metrics = {
            "Accuracy": accuracy_score(y_true, y_pred),
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1": f1_score(y_true, y_pred, zero_division=0)
        }
        
        # Probabilistic metrics
        if y_prob is not None:
            try:
                # Assuming binary classification for these specific metrics
                metrics["ROC_AUC"] = roc_auc_score(y_true, y_prob)
                metrics["PR_AUC"] = average_precision_score(y_true, y_prob)
                metrics["LogLoss"] = log_loss(y_true, y_prob)
            except ValueError as e:
                logger.warning(f"Could not compute probabilistic metric (usually due to single class in true labels): {e}")
                
        # We don't save Confusion Matrix as a float metric in the DB easily, 
        # but we could log it or serialize it. For this assignment, we compute it.
        cm = confusion_matrix(y_true, y_pred)
        # Flattened for simple storage if needed
        metrics["TN"] = float(cm[0, 0]) if cm.shape == (2,2) else np.nan
        metrics["FP"] = float(cm[0, 1]) if cm.shape == (2,2) else np.nan
        metrics["FN"] = float(cm[1, 0]) if cm.shape == (2,2) else np.nan
        metrics["TP"] = float(cm[1, 1]) if cm.shape == (2,2) else np.nan
        
        return metrics
