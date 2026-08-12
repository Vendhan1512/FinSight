import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.models.calibration import CalibrationEngine
from ml.models.final_evaluator import FinalEvaluator

def test_calibration_brier_score():
    y_true = np.array([0, 1, 1, 0])
    
    # Perfect probabilities
    y_prob_perfect = np.array([0.0, 1.0, 1.0, 0.0])
    calib_perfect = CalibrationEngine.evaluate_calibration(y_true, y_prob_perfect)
    assert calib_perfect["Brier_Score"] == 0.0
    
    # Terrible probabilities
    y_prob_bad = np.array([1.0, 0.0, 0.0, 1.0])
    calib_bad = CalibrationEngine.evaluate_calibration(y_true, y_prob_bad)
    assert calib_bad["Brier_Score"] == 1.0

def test_final_evaluator_blocks_unauthorized_access():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 1.9, 3.2])
    
    # Should raise an error if flag is false
    with pytest.raises(PermissionError):
        FinalEvaluator.evaluate_holdout(
            y_true, y_pred, 
            is_classification=False, 
            i_certify_this_is_the_final_holdout=False
        )
        
def test_final_evaluator_allows_authorized_access():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    
    # Should succeed
    report = FinalEvaluator.evaluate_holdout(
        y_true, y_pred, 
        is_classification=False, 
        i_certify_this_is_the_final_holdout=True
    )
    
    assert report["_WARNING_"] == "FINAL HOLDOUT - NOT USED FOR MODEL SELECTION"
    assert report["metrics"]["RMSE"] == 0.0
    assert report["metrics"]["Residual_Mean_Bias"] == 0.0
