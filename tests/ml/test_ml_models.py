import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.models.factory import ModelFactory
from ml.models.evaluator import EvaluationEngine
from sklearn.pipeline import Pipeline

def test_model_factory_returns_pipeline_with_preprocessing():
    # Linear Regression should include scaling and imputation inside the pipeline
    pipeline = ModelFactory.get_model("linear_regression")
    
    assert isinstance(pipeline, Pipeline)
    steps = [step[0] for step in pipeline.steps]
    
    assert "imputer" in steps
    assert "scaler" in steps
    assert "model" in steps

def test_baseline_factory():
    # Baselines should also return pipelines, but usually without the scaler
    pipeline = ModelFactory.get_model("baseline_zero_return")
    
    assert isinstance(pipeline, Pipeline)
    steps = [step[0] for step in pipeline.steps]
    assert "model" in steps

def test_evaluation_engine_regression():
    y_true = np.array([0.05, -0.02, 0.01, -0.10])
    y_pred = np.array([0.04, 0.01, 0.02, -0.05])
    
    metrics = EvaluationEngine.evaluate_regression(y_true, y_pred)
    
    assert "RMSE" in metrics
    assert "MAE" in metrics
    assert "Directional_Accuracy" in metrics
    
    # Directional Acc: 
    # (0.05, 0.04) -> Match
    # (-0.02, 0.01) -> Miss
    # (0.01, 0.02) -> Match
    # (-0.10, -0.05) -> Match
    # 3/4 = 0.75
    assert metrics["Directional_Accuracy"] == 0.75

def test_evaluation_engine_classification():
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1, 1, 1, 0])
    y_prob = np.array([0.9, 0.6, 0.8, 0.2])
    
    metrics = EvaluationEngine.evaluate_classification(y_true, y_pred, y_prob)
    
    assert "Accuracy" in metrics
    assert "F1" in metrics
    assert "ROC_AUC" in metrics
    assert "PR_AUC" in metrics
    
    # Confusion Matrix:
    # True Positives: 2
    # False Positives: 1
    # True Negatives: 1
    # False Negatives: 0
    assert metrics["TP"] == 2.0
    assert metrics["FP"] == 1.0
    assert metrics["TN"] == 1.0
    assert metrics["FN"] == 0.0
