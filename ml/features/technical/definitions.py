from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

TECHNICAL_FEATURES = [
    # --- SIMPLE RETURNS ---
    FeatureDefinitionContract(
        feature_name="ret_1d",
        description="1-period simple return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-1) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ret_5d",
        description="5-period simple return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-5) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=5,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ret_20d",
        description="20-period simple return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-20) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ret_60d",
        description="60-period simple return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-60) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=60,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ret_120d",
        description="120-period simple return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-120) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=120,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ret_252d",
        description="252-period simple return (approx 1 year)",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Price_t / Price_t-252) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- LOG RETURNS ---
    FeatureDefinitionContract(
        feature_name="log_ret_1d",
        description="1-period logarithmic return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="ln(Price_t / Price_t-1)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="log_ret_5d",
        description="5-period logarithmic return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="ln(Price_t / Price_t-5)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=5,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="log_ret_20d",
        description="20-period logarithmic return",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="ln(Price_t / Price_t-20)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- MOVING AVERAGES ---
    FeatureDefinitionContract(
        feature_name="sma_20d",
        description="20-period Simple Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Arithmetic mean of Adjusted Close over last 20 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP, # Do not backfill SMAs
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="sma_50d",
        description="50-period Simple Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Arithmetic mean of Adjusted Close over last 50 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=50,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="sma_100d",
        description="100-period Simple Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Arithmetic mean of Adjusted Close over last 100 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=100,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="sma_200d",
        description="200-period Simple Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Arithmetic mean of Adjusted Close over last 200 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=200,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ema_20d",
        description="20-period Exponential Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Exponentially weighted mean (span=20) of Adjusted Close",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="ema_50d",
        description="50-period Exponential Moving Average",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Exponentially weighted mean (span=50) of Adjusted Close",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=50,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- PRICE RELATIONSHIPS ---
    FeatureDefinitionContract(
        feature_name="price_to_sma_20d",
        description="Ratio of current price to 20d SMA",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close / SMA_20d",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="price_to_sma_50d",
        description="Ratio of current price to 50d SMA",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close / SMA_50d",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=50,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="price_to_sma_200d",
        description="Ratio of current price to 200d SMA",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close / SMA_200d",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=200,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="dist_from_rolling_high_252d",
        description="Distance from 252d rolling maximum",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Adjusted_Close / RollingMax(Adjusted_Close, 252)) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="dist_from_rolling_low_252d",
        description="Distance from 252d rolling minimum",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="(Adjusted_Close / RollingMin(Adjusted_Close, 252)) - 1",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- MOMENTUM ---
    FeatureDefinitionContract(
        feature_name="mom_20d",
        description="20-period absolute price momentum",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close_t - Adjusted_Close_t-20",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="mom_60d",
        description="60-period absolute price momentum",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close_t - Adjusted_Close_t-60",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=60,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="mom_120d",
        description="120-period absolute price momentum",
        feature_category="technical",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="Adjusted_Close_t - Adjusted_Close_t-120",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=120,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    )
]
