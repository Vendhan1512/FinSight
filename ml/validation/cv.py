import numpy as np
import pandas as pd
from typing import Generator, Tuple
import logging

logger = logging.getLogger(__name__)

class EmbargoTimeSeriesSplit:
    """
    Time-Series Cross-Validation that explicitly enforces an Embargo (Gap) between
    the training set and validation set.
    
    If the target is a 5-day future return, the model learns the future outcome of day T.
    If day T is exactly before the validation set starts, the target of day T leaks into the
    first 4 days of the validation set (since they share the same overlapping price path).
    
    This Splitter explicitly drops `gap` days between train and validation.
    """
    def __init__(self, n_splits: int = 5, gap: int = 0, test_size: int = None):
        self.n_splits = n_splits
        self.gap = gap
        self.test_size = test_size

    def split(self, X, y=None, groups=None) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Yields (train_indices, val_indices)
        """
        n_samples = len(X)
        
        # We need enough data for n_splits + test_size + gap
        if self.test_size is None:
            # Auto-calculate test size based on splits
            self.test_size = n_samples // (self.n_splits + 1)
            
        if self.test_size <= 0:
            raise ValueError("Calculated test_size is 0. Provide more data or fewer splits.")
            
        fold_size = self.test_size
        
        # We move backwards from the end of the dataset
        # Fold 1: Train [0 : end - fold_size - gap], Val [end - fold_size : end]
        # Fold 2: Train [0 : end - 2*fold_size - gap], Val [end - 2*fold_size : end - fold_size]
        
        indices = np.arange(n_samples)
        
        for i in range(self.n_splits):
            val_end = n_samples - i * fold_size
            val_start = val_end - fold_size
            
            train_end = val_start - self.gap
            train_start = 0
            
            if train_end <= 0:
                logger.warning(f"Fold {i} has 0 training samples due to gap. Stopping splits early.")
                break
                
            yield indices[train_start:train_end], indices[val_start:val_end]
