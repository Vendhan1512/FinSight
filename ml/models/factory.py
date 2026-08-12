from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import logging

logger = logging.getLogger(__name__)

try:
    from xgboost import XGBRegressor, XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("xgboost not installed. Gradient boosting models will be unavailable.")

try:
    from lightgbm import LGBMRegressor, LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("lightgbm not installed. Gradient boosting models will be unavailable.")

class ModelFactory:
    """
    Dispenses strict Scikit-Learn Pipelines.
    By embedding preprocessing (imputation, scaling) INSIDE the pipeline,
    we mathematically guarantee that transformations are fitted ONLY on the
    training set, completely eliminating data leakage into the validation set.
    """
    
    @staticmethod
    def get_preprocessing_steps():
        """Standard preprocessing for financial tabular data."""
        return [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]

    @classmethod
    def get_model(cls, model_name: str, **kwargs) -> Pipeline:
        """Returns an un-fitted scikit-learn Pipeline."""
        
        # ---------------------------------------------------------
        # REGRESSION BASELINES
        # ---------------------------------------------------------
        if model_name == "baseline_zero_return":
            # Predicts a constant 0.0 (e.g., market is a random walk)
            return Pipeline([("model", DummyRegressor(strategy="constant", constant=0.0))])
            
        elif model_name == "baseline_historical_mean":
            # Predicts the mean of the training set
            return Pipeline([("model", DummyRegressor(strategy="mean"))])

        # ---------------------------------------------------------
        # REGRESSION CLASSICAL
        # ---------------------------------------------------------
        elif model_name == "linear_regression":
            return Pipeline(cls.get_preprocessing_steps() + [("model", LinearRegression(**kwargs))])
            
        elif model_name == "ridge":
            return Pipeline(cls.get_preprocessing_steps() + [("model", Ridge(**kwargs))])
            
        elif model_name == "lasso":
            return Pipeline(cls.get_preprocessing_steps() + [("model", Lasso(**kwargs))])
            
        elif model_name == "elastic_net":
            return Pipeline(cls.get_preprocessing_steps() + [("model", ElasticNet(**kwargs))])
            
        elif model_name == "random_forest_regressor":
            # Trees don't strictly need scaling, but imputation is required.
            return Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestRegressor(**kwargs))
            ])

        # ---------------------------------------------------------
        # CLASSIFICATION BASELINES
        # ---------------------------------------------------------
        elif model_name == "baseline_majority_class":
            # Always predicts whichever class was most frequent in the training set
            return Pipeline([("model", DummyClassifier(strategy="prior"))])
            
        # ---------------------------------------------------------
        # CLASSIFICATION CLASSICAL
        # ---------------------------------------------------------
        elif model_name == "logistic_regression":
            return Pipeline(cls.get_preprocessing_steps() + [("model", LogisticRegression(**kwargs))])
            
        elif model_name == "random_forest_classifier":
            return Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestClassifier(**kwargs))
            ])
            
        # ---------------------------------------------------------
        # GRADIENT BOOSTING
        # ---------------------------------------------------------
        elif model_name == "xgboost_regressor":
            if not HAS_XGBOOST:
                raise ImportError("XGBoost is not installed.")
            return Pipeline(cls.get_preprocessing_steps() + [("model", XGBRegressor(**kwargs))])
            
        elif model_name == "lightgbm_regressor":
            if not HAS_LIGHTGBM:
                raise ImportError("LightGBM is not installed.")
            return Pipeline(cls.get_preprocessing_steps() + [("model", LGBMRegressor(**kwargs))])
            
        elif model_name == "xgboost_classifier":
            if not HAS_XGBOOST:
                raise ImportError("XGBoost is not installed.")
            return Pipeline(cls.get_preprocessing_steps() + [("model", XGBClassifier(**kwargs))])
            
        elif model_name == "lightgbm_classifier":
            if not HAS_LIGHTGBM:
                raise ImportError("LightGBM is not installed.")
            return Pipeline(cls.get_preprocessing_steps() + [("model", LGBMClassifier(**kwargs))])
            
        else:
            raise ValueError(f"Model '{model_name}' is not supported by the ModelFactory.")
