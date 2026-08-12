from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

RISK_FEATURES = [
    # --- VOLATILITY ---
    FeatureDefinitionContract(
        feature_name="vol_20d",
        description="20-period annualized rolling volatility",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="StdDev(log_return, 20) * sqrt(252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=20,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_60d",
        description="60-period annualized rolling volatility",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="StdDev(log_return, 60) * sqrt(252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=60,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_120d",
        description="120-period annualized rolling volatility",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="StdDev(log_return, 120) * sqrt(252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=120,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="vol_252d",
        description="252-period annualized rolling volatility",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="StdDev(log_return, 252) * sqrt(252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- DOWNSIDE VOLATILITY ---
    FeatureDefinitionContract(
        feature_name="downside_vol_252d",
        description="252-period annualized rolling downside volatility",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="StdDev(min(log_return, 0), 252) * sqrt(252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- DRAWDOWN ---
    FeatureDefinitionContract(
        feature_name="max_drawdown_252d",
        description="Maximum rolling drawdown over 252 periods",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["adjusted_close"],
        formula="min( (Price / RollingMax(Price, 252)) - 1 ) over 252 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- RISK-ADJUSTED METRICS ---
    FeatureDefinitionContract(
        feature_name="sharpe_252d",
        description="252-period rolling Sharpe Ratio (annualized)",
        feature_category="volatility",
        source_dataset="analytical_market_and_fred",
        source_columns=["log_return", "rfr_daily"],
        formula="sqrt(252) * Mean(excess_return, 252) / StdDev(excess_return, 252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="sortino_252d",
        description="252-period rolling Sortino Ratio (annualized)",
        feature_category="volatility",
        source_dataset="analytical_market_and_fred",
        source_columns=["log_return", "rfr_daily"],
        formula="sqrt(252) * Mean(excess_return, 252) / DownsideVol(excess_return, 252)",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- MARKET SENSITIVITY ---
    FeatureDefinitionContract(
        feature_name="beta_252d",
        description="252-period rolling Beta relative to dynamic benchmark",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="Covariance(Asset, Benchmark) / Variance(Benchmark) over 252 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="correlation_252d",
        description="252-period rolling Pearson correlation to benchmark",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="Correlation(Asset, Benchmark) over 252 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- EMPIRICAL RISK ---
    FeatureDefinitionContract(
        feature_name="var_95_252d",
        description="Historical 95% Value at Risk (5th percentile return)",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="Percentile(log_return, 5) over 252 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="cvar_95_252d",
        description="Historical 95% Conditional VaR (Expected Shortfall)",
        feature_category="volatility",
        source_dataset="analytical_market",
        source_columns=["log_return"],
        formula="Mean of log_returns < var_95_252d over 252 periods",
        frequency=FeatureFrequency.DAILY,
        lookback_periods=252,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    )
]
