import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class LeakageAssertionError(Exception):
    pass

class ChronologicalSplitter:
    """Strict temporal boundaries to prevent look-ahead bias in financial ML."""
    
    # Proposed boundaries per the implementation plan
    TRAIN_END = pd.to_datetime("2020-12-31")
    VAL_START = pd.to_datetime("2021-01-01")
    VAL_END = pd.to_datetime("2022-12-31")
    TEST_START = pd.to_datetime("2023-01-01")

    @classmethod
    def assign_partitions(cls, df: pd.DataFrame, time_col: str = "prediction_time") -> pd.DataFrame:
        """Assigns TRAIN, VALIDATION, or TEST based on strictly defined time boundaries."""
        if df.empty or time_col not in df.columns:
            return df
            
        df = df.copy()
        
        # Initialize partition
        df["partition"] = "NONE"
        
        # Assign
        df.loc[df[time_col] <= cls.TRAIN_END, "partition"] = "TRAIN"
        df.loc[(df[time_col] >= cls.VAL_START) & (df[time_col] <= cls.VAL_END), "partition"] = "VALIDATION"
        df.loc[df[time_col] >= cls.TEST_START, "partition"] = "TEST"
        
        # Drop unassigned (if any gaps exist in config)
        df = df[df["partition"] != "NONE"]
        
        return df


class DatasetBuilder:
    """
    Joins Point-In-Time features with future targets, asserts zero leakage,
    and assigns chronological partitions.
    """
    
    @staticmethod
    def build(
        features_df: pd.DataFrame, 
        targets_df: pd.DataFrame, 
        availability_cols: List[str]
    ) -> pd.DataFrame:
        """
        Args:
            features_df: Dataframe with ['symbol', 'prediction_time'] and feature columns.
            targets_df: Dataframe with ['symbol', 'prediction_time', 'target_end_time', 'target_value'].
            availability_cols: Columns containing availability timestamps (e.g. sec_filing_date) to assert against.
        """
        logger.info("Building Supervised Dataset...")
        
        # 1. Join on T (prediction_time)
        # We use an inner join because we need BOTH the features and the realized future target.
        df = pd.merge(
            features_df,
            targets_df,
            on=["symbol", "prediction_time"],
            how="inner"
        )
        
        if df.empty:
            logger.error("Dataset build failed: 0 rows resulted from the feature-target join.")
            return df
            
        # 2. Hard Leakage Assertion (The Final Firewall)
        # We explicitly verify that the features joined to this prediction row were 
        # actually available on or before the prediction time.
        logger.info("Running Dataset Leakage Assertion...")
        for avail_col in availability_cols:
            if avail_col in df.columns:
                leaks = df[df[avail_col] > df["prediction_time"]]
                if not leaks.empty:
                    msg = f"FATAL LEAKAGE: {len(leaks)} rows where {avail_col} > prediction_time."
                    logger.error(msg)
                    raise LeakageAssertionError(msg)
                    
        # 3. Target Future Assertion
        # Explicitly verify the target was realized strictly AFTER the prediction time
        if not df[df["target_end_time"] <= df["prediction_time"]].empty:
            msg = "FATAL LEAKAGE: Target was realized on or before prediction time."
            logger.error(msg)
            raise LeakageAssertionError(msg)
                    
        logger.info("[+] Dataset Leakage Assertion Passed.")
        
        # 4. Chronological Split
        logger.info("Applying Chronological Partitions...")
        df = ChronologicalSplitter.assign_partitions(df, "prediction_time")
        
        return df
