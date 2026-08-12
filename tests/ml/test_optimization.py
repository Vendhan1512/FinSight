import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ml.validation.cv import EmbargoTimeSeriesSplit

def test_embargo_cv_drops_gap():
    # 20 samples
    X = np.arange(20)
    
    # 2 splits, gap of 2, test_size of 4
    cv = EmbargoTimeSeriesSplit(n_splits=2, gap=2, test_size=4)
    
    splits = list(cv.split(X))
    assert len(splits) == 2
    
    # Analyze the most recent fold (Fold 0 in the generator)
    # n_samples = 20. Fold size = 4. 
    # Val End = 20, Val Start = 16. -> Val is [16, 17, 18, 19]
    # Train End = Val Start - Gap = 16 - 2 = 14. -> Train is [0 ... 13]
    train_0, val_0 = splits[0]
    
    assert len(val_0) == 4
    assert val_0[0] == 16
    assert val_0[-1] == 19
    
    assert train_0[-1] == 13 # The embargo gap successfully dropped 14 and 15
    assert len(train_0) == 14
    
    # Check the older fold (Fold 1)
    # Val End = 16, Val Start = 12. -> Val is [12, 13, 14, 15]
    # Train End = 12 - 2 = 10. -> Train is [0 ... 9]
    train_1, val_1 = splits[1]
    
    assert val_1[0] == 12
    assert val_1[-1] == 15
    
    assert train_1[-1] == 9 # Embargo gap dropped 10 and 11
    
def test_embargo_cv_stops_early_if_no_training_data():
    # 10 samples
    X = np.arange(10)
    
    # If gap is 5 and test_size is 5, there is 0 training data for fold 0
    cv = EmbargoTimeSeriesSplit(n_splits=2, gap=5, test_size=5)
    
    splits = list(cv.split(X))
    
    # Generator should yield 0 folds because it detects train_end <= 0
    assert len(splits) == 0
