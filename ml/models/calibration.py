import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Tuple
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

class CalibrationEngine:
    """
    Evaluates probability calibration and applies Platt/Isotonic scaling.
    Crucially, if a model is calibrated, the calibration MUST be fitted on data
    independent of the model's training set to prevent severe overfitting of the probabilities.
    """
    
    @staticmethod
    def evaluate_calibration(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict[str, Any]:
        """Calculates Brier score and calibration curve coordinates."""
        if len(y_true) == 0 or y_prob is None:
            return {}
            
        brier = brier_score_loss(y_true, y_prob)
        
        # Calculate reliability diagram coordinates
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
        
        return {
            "Brier_Score": brier,
            "Calibration_Curve_True": prob_true.tolist(),
            "Calibration_Curve_Pred": prob_pred.tolist()
        }

    @staticmethod
    def calibrate_pipeline(pipeline: Pipeline, X_calib, y_calib, method: str = "isotonic") -> CalibratedClassifierCV:
        """
        Wraps a pre-fitted Pipeline in a CalibratedClassifierCV.
        
        Args:
            pipeline: A fitted sklearn Pipeline.
            X_calib: Calibration features (MUST BE INDEPENDENT FROM TRAINING DATA).
            y_calib: Calibration targets.
            method: 'isotonic' or 'sigmoid'
            
        Returns:
            A fitted CalibratedClassifierCV ready for production probability scoring.
        """
        if not hasattr(pipeline, "predict_proba"):
            raise ValueError("Pipeline does not support probability predictions. Cannot calibrate.")
            
        # We use cv='prefit' because the pipeline is already fitted on the training set.
        # We now fit ONLY the calibrator on the independent X_calib, y_calib set.
        calibrated_clf = CalibratedClassifierCV(estimator=pipeline, method=method, cv="prefit")
        
        logger.info(f"Fitting {method} calibrator on {len(y_calib)} independent samples...")
        calibrated_clf.fit(X_calib, y_calib)
        
        return calibrated_clf
