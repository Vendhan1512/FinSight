import pandas as pd
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class LeakageDetectedError(Exception):
    """Raised when the LeakageValidator detects any form of Look-Ahead Bias."""
    pass

class PointInTimeJoiner:
    """
    Generic engine for Point-in-Time (PIT) dataset joins.
    Strictly enforces availability_timestamp <= prediction_timestamp.
    """
    
    @staticmethod
    def join_asof(
        target_df: pd.DataFrame, 
        feature_df: pd.DataFrame, 
        prediction_time_col: str, 
        availability_time_col: str,
        feature_cols: List[str]
    ) -> pd.DataFrame:
        """
        Performs an as-of join bridging a feature dataset to a prediction calendar.
        GUARANTEES that the feature was publicly available on or before the prediction date.
        """
        # Ensure sorting for merge_asof
        target = target_df.sort_values(by=prediction_time_col)
        feat = feature_df.sort_values(by=availability_time_col).dropna(subset=[availability_time_col])
        
        cols_to_keep = [availability_time_col] + feature_cols
        feat = feat[cols_to_keep]
        
        aligned = pd.merge_asof(
            target,
            feat,
            left_on=prediction_time_col,
            right_on=availability_time_col,
            direction="backward" # Strictly backward to prevent lookahead
        )
        return aligned


class LeakageValidator:
    """
    The final security firewall for the ML Pipeline.
    Explicitly scans combined feature datasets and crashes if Look-Ahead bias is detected.
    """
    
    @staticmethod
    def validate_dataset(df: pd.DataFrame, prediction_col: str, availability_cols: List[str]):
        """
        Scans the dataframe. 
        If ANY availability_col > prediction_col, it raises a fatal error.
        
        Args:
            df: The merged ML training dataset.
            prediction_col: The timestamp representing 'Now' (T).
            availability_cols: A list of timestamps representing when data became available.
        """
        if df.empty:
            logger.warning("Empty dataframe provided to LeakageValidator.")
            return
            
        if prediction_col not in df.columns:
            raise ValueError(f"Prediction column '{prediction_col}' missing from dataset.")
            
        invalid_rows_total = 0
        report = []
        
        for avail_col in availability_cols:
            if avail_col not in df.columns:
                continue
                
            # Leakage Rule: Availability > Prediction
            # e.g., Fact became available on May 10, but Prediction is March 31.
            mask = df[avail_col] > df[prediction_col]
            leaks = df[mask]
            
            if not leaks.empty:
                invalid_rows_total += len(leaks)
                report.append(f"- '{avail_col}': {len(leaks)} rows leaked future information.")
                
        if invalid_rows_total > 0:
            error_msg = f"FATAL: LeakageValidator detected {invalid_rows_total} invalid rows.\n" + "\n".join(report)
            logger.error(error_msg)
            # The prompt mandates: "If leakage is detected, the command must return a failure status. Do not silently repair."
            raise LeakageDetectedError(error_msg)
            
        logger.info("LeakageValidator passed: No Point-in-Time violations detected.")
        return True
