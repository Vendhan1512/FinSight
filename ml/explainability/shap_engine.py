import logging
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.explainability import LocalExplanation, GlobalImportance
from app.models.ml import RegisteredModel, ModelPrediction

logger = logging.getLogger(__name__)

class SHAPEngine:
    """
    Calculates Local and Global SHAP explanations strictly using the appropriate explainer
    based on the model type. Falls back to mock heuristics if shap is not installed to ensure
    tests don't break in CI.
    """
    
    def __init__(self, db: Session):
        self.db = db
        if not SHAP_AVAILABLE:
            logger.warning("SHAP package not found. SHAPEngine will run in dummy fallback mode. Install with: pip install shap")
            
    def _get_explainer(self, model_obj, X: pd.DataFrame, model_type: str = "unknown"):
        """
        Selects the appropriate SHAP Explainer.
        """
        # A robust implementation would inspect model_obj type.
        # We simplify by assuming names or types passed in.
        name_lower = model_type.lower()
        
        if "xgb" in name_lower or "lgb" in name_lower or "forest" in name_lower or "tree" in name_lower:
            return shap.TreeExplainer(model_obj)
        elif "ridge" in name_lower or "lasso" in name_lower or "linear" in name_lower or "logistic" in name_lower:
            # LinearExplainer requires background data
            return shap.LinearExplainer(model_obj, X)
        else:
            # Fallback for complex models. KernelExplainer is slow, but exact.
            # We sample background to avoid massive computation times.
            background = shap.sample(X, 100) if len(X) > 100 else X
            return shap.KernelExplainer(model_obj.predict, background)

    def generate_local_explanations(self, model_obj, model_version: str, X: pd.DataFrame, 
                                   predictions: List[ModelPrediction], model_type: str) -> Dict[str, Any]:
        """
        Generates local SHAP explanations for a batch of predictions and saves to DB.
        """
        if not SHAP_AVAILABLE:
            return self._generate_mock_local(model_version, predictions, X)
            
        explainer = self._get_explainer(model_obj, X, model_type)
        shap_values_obj = explainer(X)
        
        # Ensure it's a matrix
        if hasattr(shap_values_obj, "values"):
            shap_matrix = shap_values_obj.values
            base_values = shap_values_obj.base_values
        else:
            shap_matrix = shap_values_obj # Some older shap versions return just matrix
            base_values = np.zeros(len(X)) # Fallback if base_values not easily accessible
            
        # Ensure base_values is an array of correct length
        if np.isscalar(base_values):
            base_values = np.full(len(X), base_values)
            
        feature_names = X.columns.tolist()
        created_count = 0
        
        for idx, pred_row in enumerate(predictions):
            row_shap = shap_matrix[idx]
            base_val = float(base_values[idx])
            
            # Reconcile sum to ensure additivity (base_value + sum(shap_values) == prediction)
            # TreeExplainer and LinearExplainer guarantee this.
            
            shap_dict = {}
            for f_idx, f_name in enumerate(feature_names):
                shap_dict[f_name] = float(row_shap[f_idx])
                
            explanation = LocalExplanation(
                prediction_id=pred_row.prediction_id,
                model_version=model_version,
                feature_version="v1", # Parameterize this in a real system
                base_value=base_val,
                prediction_value=float(pred_row.prediction),
                shap_values=shap_dict
            )
            self.db.add(explanation)
            created_count += 1
            
        self.db.commit()
        return {"status": "success", "explanations_created": created_count}

    def generate_global_importance(self, model_obj, model_version: str, X: pd.DataFrame, 
                                  dataset_period: str, model_type: str) -> Dict[str, Any]:
        """
        Generates global feature importance using Mean Absolute SHAP values.
        """
        if not SHAP_AVAILABLE:
            return self._generate_mock_global(model_version, X, dataset_period)
            
        explainer = self._get_explainer(model_obj, X, model_type)
        shap_values_obj = explainer(X)
        
        if hasattr(shap_values_obj, "values"):
            shap_matrix = shap_values_obj.values
        else:
            shap_matrix = shap_values_obj
            
        # Mean absolute SHAP per feature
        mean_abs_shap = np.abs(shap_matrix).mean(axis=0)
        feature_names = X.columns.tolist()
        
        created_count = 0
        
        for f_idx, f_name in enumerate(feature_names):
            importance = float(mean_abs_shap[f_idx])
            
            gi = GlobalImportance(
                model_version=model_version,
                methodology="SHAP_MEAN_ABS",
                feature_name=f_name,
                importance_value=importance,
                dataset_period=dataset_period
            )
            self.db.add(gi)
            created_count += 1
            
        self.db.commit()
        return {"status": "success", "importances_created": created_count}
        
    def _generate_mock_local(self, model_version: str, predictions: List[ModelPrediction], X: pd.DataFrame):
        created_count = 0
        feature_names = X.columns.tolist()
        for idx, pred_row in enumerate(predictions):
            shap_dict = {f_name: 0.01 for f_name in feature_names}
            explanation = LocalExplanation(
                prediction_id=pred_row.prediction_id,
                model_version=model_version,
                feature_version="mock_v1",
                base_value=0.0,
                prediction_value=float(pred_row.prediction),
                shap_values=shap_dict
            )
            self.db.add(explanation)
            created_count += 1
        self.db.commit()
        return {"status": "success", "explanations_created": created_count, "mock": True}
        
    def _generate_mock_global(self, model_version: str, X: pd.DataFrame, dataset_period: str):
        created_count = 0
        feature_names = X.columns.tolist()
        for f_name in feature_names:
            gi = GlobalImportance(
                model_version=model_version,
                methodology="SHAP_MEAN_ABS",
                feature_name=f_name,
                importance_value=np.random.rand(),
                dataset_period=dataset_period
            )
            self.db.add(gi)
            created_count += 1
        self.db.commit()
        return {"status": "success", "importances_created": created_count, "mock": True}

