from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

VOLUME_FEATURES = [
    FeatureDefinitionContract(
        feature_name="vol_change_1d",
        description="Percentage change in daily trading volume",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="(Volume_t / Volume_t-1) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_sma_20d",
        description="20-day Simple Moving Average of Volume",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="Mean(Volume, 20)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_sma_50d",
        description="50-day Simple Moving Average of Volume",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="Mean(Volume, 50)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=50,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_std_20d",
        description="20-day Standard Deviation of Volume",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="StdDev(Volume, 20)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_zscore_20d",
        description="Current volume normalized against 20-day distribution",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="(Volume_t - Mean(Volume, 20)) / StdDev(Volume, 20)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_ratio_20d",
        description="Ratio of current volume to 20-day SMA",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["volume"],
        formula="Volume_t / Mean(Volume, 20)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="obv",
        description="On-Balance Volume (Cumulative)",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["close", "volume"],
        formula="If Close > Prior Close: +Volume, If Close < Prior Close: -Volume",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=2, # Requires prior close to determine direction
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vwap_intraday",
        description="Volume Weighted Average Price (Requires Intraday Data)",
        feature_category="volume",
        source_dataset="analytical_market",
        source_columns=["high", "low", "close", "volume"],
        formula="Cumulative(Price * Volume) / Cumulative(Volume)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0",
        status="Unavailable" # Explicitly disabled due to daily data constraints
    )
]
