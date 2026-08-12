import numpy as np
import pandas as pd
import logging
from typing import Dict, Any

from ml.models.evaluator import EvaluationEngine
from ml.models.calibration import CalibrationEngine

logger = logging.getLogger(__name__)

class FinalEvaluator:
    """
    Executes the true out-of-sample holdout test.
    This engine is mathematically blocked from returning any metrics unless a flag
    explicitly acknowledging the test set lockdown is passed.
    """
    
    @staticmethod
    def evaluate_holdout(
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        y_prob: np.ndarray = None, 
        is_classification: bool = False,
        i_certify_this_is_the_final_holdout: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the FINAL HOLDOUT evaluation.
        """
        if not i_certify_this_is_the_final_holdout:
            raise PermissionError(
                "BLOCKED: You cannot evaluate the final holdout set without explicitly certifying "
                "that model selection is frozen and this data will not be used for tuning."
            )
            
        logger.warning("==========================================================")
        logger.warning("FINAL HOLDOUT EVALUATION TRIGGERED.")
        logger.warning("THESE METRICS MUST NOT BE USED FOR MODEL SELECTION OR TUNING.")
        logger.warning("==========================================================")
        
        report = {
            "_WARNING_": "FINAL HOLDOUT - NOT USED FOR MODEL SELECTION",
            "metrics": {}
        }
        
        if is_classification:
            metrics = EvaluationEngine.evaluate_classification(y_true, y_pred, y_prob)
            
            # Add calibration metrics if probability exists
            if y_prob is not None:
                calib = CalibrationEngine.evaluate_calibration(y_true, y_prob)
                metrics["Brier_Score"] = calib.get("Brier_Score", np.nan)
                
            report["metrics"] = metrics
        else:
            metrics = EvaluationEngine.evaluate_regression(y_true, y_pred)
            
            # Residual Analysis for Regression
            residuals = y_true - y_pred
            
            # Systematic Bias: Mean of residuals (should be close to 0)
            metrics["Residual_Mean_Bias"] = np.mean(residuals)
            # Residual Variance
            metrics["Residual_Variance"] = np.var(residuals)
            
            report["metrics"] = metrics
            
        return report
