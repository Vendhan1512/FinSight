from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

CROSS_SECTIONAL_FEATURES = [
    # --- RELATIVE RETURNS ---
    FeatureDefinitionContract(
        feature_name="return_1m_percentile",
        description="Cross-Sectional Percentile Rank of 1-Month Return (0.0 to 1.0)",
        feature_category="cross_sectional",
        source_dataset="feature_observations", # These operate on already-computed ML features
        source_columns=["ret_1m"],
        formula="Rank(ret_1m_i) / N",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="return_1m_zscore",
        description="Cross-Sectional Z-Score of 1-Month Return",
        feature_category="cross_sectional",
        source_dataset="feature_observations",
        source_columns=["ret_1m"],
        formula="(ret_1m_i - Mean(ret_1m)) / Std(ret_1m)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- RELATIVE VOLATILITY ---
    FeatureDefinitionContract(
        feature_name="volatility_20d_percentile",
        description="Cross-Sectional Percentile Rank of 20-Day Volatility",
        feature_category="cross_sectional",
        source_dataset="feature_observations",
        source_columns=["vol_20d"],
        formula="Rank(vol_20d_i) / N",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- RELATIVE FUNDAMENTALS ---
    FeatureDefinitionContract(
        feature_name="operating_margin_zscore",
        description="Cross-Sectional Z-Score of Operating Margin",
        feature_category="cross_sectional",
        source_dataset="feature_observations",
        source_columns=["operating_margin"],
        formula="(operating_margin_i - Mean(operating_margin)) / Std(operating_margin)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="debt_to_equity_percentile",
        description="Cross-Sectional Percentile Rank of Leverage (Debt/Equity)",
        feature_category="cross_sectional",
        source_dataset="feature_observations",
        source_columns=["debt_to_equity"],
        formula="Rank(debt_to_equity_i) / N",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    )
]
