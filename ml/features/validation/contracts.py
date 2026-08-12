from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum

class FeatureFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class MissingValuePolicy(str, Enum):
    DROP = "drop"
    FORWARD_FILL = "forward_fill"
    MEAN_IMPUTE = "mean_impute"
    ZERO_FILL = "zero_fill"
    IGNORE = "ignore" # For models that natively handle NaNs (like XGBoost)

class FeatureDefinitionContract(BaseModel):
    """
    Strict validation contract for defining a new Machine Learning feature.
    Guarantees that no feature enters the registry without explicitly declaring
    its mathematical formula and data provenance.
    """
    feature_name: str = Field(..., description="Unique identifier for the feature (e.g., 'rsi_14_daily')")
    description: str = Field(..., description="Human-readable explanation of what this feature represents")
    feature_category: str = Field(..., description="e.g., technical, volatility, macro, fundamental")
    
    # Provenance
    source_dataset: str = Field(..., description="The upstream table/dataset this relies on (e.g., 'analytical_market')")
    source_columns: List[str] = Field(..., min_items=1, description="The specific columns required to compute this feature")
    
    # Logic
    formula: str = Field(..., description="Mathematical formula or plain English algorithmic description")
    frequency: FeatureFrequency
    lookback_periods: int = Field(..., description="Number of historical periods required")
    missing_value_policy: MissingValuePolicy = Field(..., description="How to handle missing values")
    version_tag: str = Field(..., description="Semantic version of the feature definition")
    status: str = Field("CANDIDATE", description="Lifecycle status: CANDIDATE, VALIDATED, SELECTED, REJECTED, DEPRECATED, Unavailable")
    rejection_reason: Optional[str] = Field(None, description="Explicit reason if the feature is REJECTED or DEPRECATED")

    @validator("feature_name")
    def validate_naming_convention(cls, v):
        if not v.islower() or " " in v:
            raise ValueError("feature_name must be lowercase and use underscores instead of spaces.")
        return v
        
    @validator("formula")
    def validate_formula_not_empty(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Formula description is too short to be meaningful.")
        return v
