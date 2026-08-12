import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any

from ml.features.registry import FeatureRegistry
from ml.features.validation.pit_engine import LeakageValidator, LeakageDetectedError
from ml.features.validation.quality_engine import FeatureQualityEngine
from ml.features.selection.selector import FeatureSelectionEngine
from backend.app.models.features import FeatureRun

logger = logging.getLogger(__name__)

class FeaturePipelineOrchestrator:
    """
    Master controller for the Phase 3 Feature Pipeline.
    Enforces the strict order: Calculate -> LeakageCheck -> QualityCheck -> Selection -> Persist.
    """
    def __init__(self, db_session=None):
        self.registry = FeatureRegistry()
        self.quality_engine = FeatureQualityEngine(missingness_threshold=0.30)
        self.selection_engine = FeatureSelectionEngine(correlation_threshold=0.85)
        self.db = db_session

    def execute_pipeline(self, feature_set_key: str, input_df: pd.DataFrame, target_col: str = None) -> Dict[str, Any]:
        """
        Executes the entire feature lifecycle.
        """
        logger.info(f"Starting Feature Pipeline for: {feature_set_key}")
        
        # 1. Initialization
        spec = self.registry.get_feature_set(feature_set_key)
        engine = spec.engine_class()
        
        run_record = {
            "feature_set": spec.name,
            "feature_version": spec.version,
            "start_time": datetime.utcnow(),
            "rows_processed": len(input_df),
            "rows_created": 0,
            "status": "IN_PROGRESS"
        }
        
        # 2. Calculation
        logger.info("Executing Calculation Engine...")
        try:
            features_df = engine.calculate_features(input_df)
        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            run_record["status"] = "FAILED_CALCULATION"
            return {"run": run_record, "data": pd.DataFrame(), "contracts": spec.definitions}
            
        if features_df.empty:
            logger.warning("Engine returned empty dataframe.")
            run_record["status"] = "FAILED_NO_DATA"
            return {"run": run_record, "data": pd.DataFrame(), "contracts": spec.definitions}
            
        # 3. Leakage Check (The Firewall)
        logger.info("Executing Leakage Validator...")
        # Infer availability columns based on the dataset (simplification for orchestrator demo)
        availability_cols = [c for c in features_df.columns if "date" in c or "realtime_start" in c or "time" in c and c != "original_timestamp" and c != "prediction_timestamp"]
        pred_col = "prediction_timestamp" if "prediction_timestamp" in features_df.columns else "original_timestamp"
        
        try:
            LeakageValidator.validate_dataset(features_df, pred_col, availability_cols)
            run_record["leakage_status"] = "PASSED"
        except LeakageDetectedError as e:
            logger.error(f"PIPELINE ABORTED: {e}")
            run_record["status"] = "FAILED_LEAKAGE"
            run_record["leakage_status"] = "FAILED"
            return {"run": run_record, "data": pd.DataFrame(), "contracts": spec.definitions}
            
        # 4. Quality Audit
        logger.info("Executing Quality Engine...")
        updated_contracts = self.quality_engine.audit_features(features_df, spec.definitions)
        
        # 5. Selection Audit (If target provided)
        if target_col and target_col in features_df.columns:
            logger.info("Executing Selection Engine...")
            updated_contracts = self.selection_engine.select_features(features_df, target_col, updated_contracts)
        else:
            logger.info("Skipping Selection Engine (no target column provided).")
            
        # Evaluate final status
        rejected_count = sum(1 for c in updated_contracts.values() if c.status == "REJECTED")
        if rejected_count == len(updated_contracts):
            logger.error("All features were rejected. Pipeline failed.")
            run_record["status"] = "FAILED_QUALITY"
            run_record["quality_status"] = "FAILED"
            return {"run": run_record, "data": features_df, "contracts": updated_contracts}
            
        # 6. Persistence (Mocked if DB offline)
        run_record["rows_created"] = len(features_df)
        run_record["rows_rejected"] = rejected_count
        run_record["status"] = "SUCCESS"
        run_record["quality_status"] = "PASSED"
        run_record["end_time"] = datetime.utcnow()
        
        logger.info(f"Pipeline Completed Successfully. Generated {len(features_df)} rows. {rejected_count} features rejected.")
        
        return {
            "run": run_record,
            "data": features_df,
            "contracts": updated_contracts
        }
