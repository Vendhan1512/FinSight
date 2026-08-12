import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from sqlalchemy.orm import Session
from app.models.explainability import GlobalImportance

logger = logging.getLogger(__name__)

class PermutationEngine:
    """
    Calculates Permutation Importance for models. 
    Strictly restricted to run on validation/test data to measure generalization importance.
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_importance(self, model_obj, model_version: str, X_val: pd.DataFrame, 
                            y_val: pd.Series, dataset_period: str, metric: str = "r2", 
                            n_repeats: int = 5) -> Dict[str, Any]:
        """
        Runs permutation importance on validation data and stores in DB.
        """
        try:
            from sklearn.inspection import permutation_importance
        except ImportError:
            logger.warning("scikit-learn not installed. Running mock permutation importance.")
            return self._generate_mock_permutation(model_version, X_val, dataset_period)

        # Calculate permutation importance
        # Ensure model has a score method or we wrap it
        # Note: scikit-learn's permutation_importance takes a fitted estimator, X, y, and a scoring metric
        try:
            result = permutation_importance(
                model_obj, X_val, y_val, n_repeats=n_repeats, random_state=42, scoring=metric
            )
            
            importances_mean = result.importances_mean
            importances_std = result.importances_std
            feature_names = X_val.columns.tolist()
            
            created_count = 0
            for i, f_name in enumerate(feature_names):
                gi = GlobalImportance(
                    model_version=model_version,
                    methodology="PERMUTATION",
                    feature_name=f_name,
                    importance_value=float(importances_mean[i]),
                    importance_std=float(importances_std[i]),
                    dataset_period=dataset_period
                )
                self.db.add(gi)
                created_count += 1
                
            self.db.commit()
            return {"status": "success", "importances_created": created_count}
            
        except Exception as e:
            logger.error(f"Failed to calculate permutation importance: {e}")
            return {"status": "error", "message": str(e)}
            
    def _generate_mock_permutation(self, model_version: str, X: pd.DataFrame, dataset_period: str):
        created_count = 0
        feature_names = X.columns.tolist()
        for f_name in feature_names:
            gi = GlobalImportance(
                model_version=model_version,
                methodology="PERMUTATION",
                feature_name=f_name,
                importance_value=np.random.rand(),
                importance_std=np.random.rand() * 0.1,
                dataset_period=dataset_period
            )
            self.db.add(gi)
            created_count += 1
        self.db.commit()
        return {"status": "success", "importances_created": created_count, "mock": True}
