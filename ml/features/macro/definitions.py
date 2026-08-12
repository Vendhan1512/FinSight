from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

MACRO_FEATURES = [
    # --- LEVELS ---
    FeatureDefinitionContract(
        feature_name="fedfunds_level",
        description="Effective Federal Funds Rate (Point-in-Time)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["fedfunds"],
        formula="Latest available FEDFUNDS rate as of prediction date",
        frequency=FeatureFrequency.DAILY, # The feature is daily, though the source is monthly
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="cpi_level",
        description="Consumer Price Index (CPIAUCSL) (Point-in-Time)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["cpiaucsl"],
        formula="Latest available CPIAUCSL as of prediction date",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="unrate_level",
        description="Unemployment Rate (Point-in-Time)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["unrate"],
        formula="Latest available UNRATE as of prediction date",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="gs10_level",
        description="10-Year Treasury Yield (Point-in-Time)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["gs10"],
        formula="Latest available GS10 yield as of prediction date",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.FORWARD_FILL,
        version_tag="1.0.0"
    ),

    # --- CHANGES (Assuming monthly base frequency for these indicators) ---
    FeatureDefinitionContract(
        feature_name="cpi_change_1m",
        description="1-Month Change in CPI (Point-in-Time)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["cpiaucsl"],
        formula="(CPI_t / CPI_t-1) - 1",
        frequency=FeatureFrequency.MONTHLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="cpi_change_12m",
        description="12-Month Change in CPI (Point-in-Time YoY Inflation)",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["cpiaucsl"],
        formula="(CPI_t / CPI_t-12) - 1",
        frequency=FeatureFrequency.MONTHLY,
        lookback_periods=12,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="unrate_change_3m",
        description="3-Month Change in Unemployment Rate",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["unrate"],
        formula="UNRATE_t - UNRATE_t-3",
        frequency=FeatureFrequency.MONTHLY,
        lookback_periods=3,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- SPREADS ---
    FeatureDefinitionContract(
        feature_name="spread_10y_ff",
        description="Yield Spread: 10-Year Treasury minus Federal Funds Rate",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["gs10", "fedfunds"],
        formula="GS10_t - FEDFUNDS_t",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- MOMENTUM / VOLATILITY ---
    FeatureDefinitionContract(
        feature_name="cpi_volatility_12m",
        description="12-Month Rolling Standard Deviation of CPI Changes",
        feature_category="macro",
        source_dataset="economic_observations",
        source_columns=["cpiaucsl"],
        formula="StdDev(CPI_1m_changes, 12)",
        frequency=FeatureFrequency.MONTHLY,
        lookback_periods=12,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    )
]
