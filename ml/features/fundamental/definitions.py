from ml.features.validation.contracts import FeatureDefinitionContract, FeatureFrequency, MissingValuePolicy

FUNDAMENTAL_FEATURES = [
    # --- GROWTH ---
    FeatureDefinitionContract(
        feature_name="revenue_growth_yoy",
        description="Year-over-Year Revenue Growth",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["revenue"],
        formula="(Revenue_t / Revenue_t-4) - 1", # Assuming quarterly data (4 quarters = 1 year)
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=4,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="net_income_growth_yoy",
        description="Year-over-Year Net Income Growth",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["net_income"],
        formula="(Net_Income_t / Net_Income_t-4) - 1",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=4,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="asset_growth_yoy",
        description="Year-over-Year Asset Growth",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["assets"],
        formula="(Assets_t / Assets_t-4) - 1",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=4,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- MARGINS ---
    FeatureDefinitionContract(
        feature_name="operating_margin",
        description="Operating Income / Revenue",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["operating_income", "revenue"],
        formula="Operating_Income / Revenue",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="net_margin",
        description="Net Income / Revenue",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["net_income", "revenue"],
        formula="Net_Income / Revenue",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    
    # --- PROFITABILITY ---
    FeatureDefinitionContract(
        feature_name="roa",
        description="Return on Assets (Net Income / Total Assets)",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["net_income", "assets"],
        formula="Net_Income / Assets",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="roe",
        description="Return on Equity (Net Income / Total Equity)",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["net_income", "equity"],
        formula="Net_Income / Equity",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="asset_turnover",
        description="Revenue / Total Assets",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["revenue", "assets"],
        formula="Revenue / Assets",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- LEVERAGE ---
    FeatureDefinitionContract(
        feature_name="debt_to_equity",
        description="Total Liabilities / Total Equity",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["liabilities", "equity"],
        formula="Liabilities / Equity",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),
    FeatureDefinitionContract(
        feature_name="debt_to_assets",
        description="Total Liabilities / Total Assets",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["liabilities", "assets"],
        formula="Liabilities / Assets",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0"
    ),

    # --- VALUATION (UNAVAILABLE) ---
    FeatureDefinitionContract(
        feature_name="pe_ratio",
        description="Price to Earnings Ratio (Requires PIT Shares Outstanding)",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["net_income", "market_price"],
        formula="Price / (Net_Income / Shares_Outstanding)",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0",
        status="Unavailable"
    ),
    FeatureDefinitionContract(
        feature_name="pb_ratio",
        description="Price to Book Ratio (Requires PIT Shares Outstanding)",
        feature_category="fundamental",
        source_dataset="sec_financial_facts",
        source_columns=["equity", "market_price"],
        formula="Price / (Equity / Shares_Outstanding)",
        frequency=FeatureFrequency.QUARTERLY,
        lookback_periods=1,
        missing_value_policy=MissingValuePolicy.DROP,
        version_tag="1.0.0",
        status="Unavailable"
    )
]
