import logging
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.explainability import GlobalImportance, TemporalStability

logger = logging.getLogger(__name__)

class TemporalAnalysisEngine:
    """
    Evaluates feature importance stability across time (folds/periods).
    """
    def __init__(self, db: Session):
        self.db = db

    def evaluate_stability(self, model_version: str):
        """
        Calculates stability of all features for a given model version.
        """
        # Fetch all global importances for this model
        importances = self.db.scalars(
            select(GlobalImportance)
            .where(GlobalImportance.model_version == model_version)
        ).all()
        
        if not importances:
            return {"status": "error", "message": "No importances found for model."}
            
        # Group by feature_name
        feature_history = {}
        for imp in importances:
            # We skip 'none' or 'mock' periods if we want, but assume all periods valid here
            if imp.feature_name not in feature_history:
                feature_history[imp.feature_name] = []
            feature_history[imp.feature_name].append(imp.importance_value)
            
        created_count = 0
        
        for feature_name, values in feature_history.items():
            if len(values) < 2:
                continue # Cannot assess stability with 1 period
                
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Coeff of variation
            cv = std_val / (mean_val + 1e-9)
            
            # Determine classification
            # If CV is low, it's stable.
            # If CV is high, it's unstable.
            # Regime-dependent requires deeper timeseries analysis, 
            # but we can proxy it by checking if it has distinct clusters of values.
            is_regime_dependent = False
            
            if cv < 0.5:
                classification = "STABLE"
            elif cv > 1.5:
                classification = "UNSTABLE"
            else:
                classification = "REGIME_DEPENDENT"
                is_regime_dependent = True
                
            stability = TemporalStability(
                model_version=model_version,
                feature_name=feature_name,
                stability_score=float(cv),
                is_regime_dependent=is_regime_dependent,
                stability_classification=classification
            )
            self.db.add(stability)
            created_count += 1
            
        self.db.commit()
        return {"status": "success", "stability_records_created": created_count}
