# FinSight Data Lineage

This document traces how raw telemetry is mutated into an actionable intelligence assessment.

## Lineage Trace

1. **Ingestion** (`data_pipeline/`)
   - `MarketPrice`
   - `SECFinancialFact` -> `SECFiling`
   - `EconomicObservation`
   - `NewsArticle`

2. **Analytical Aggregation** (`analytics/`)
   - The `AnalyticalMarket` warehouse view normalizes price strings to numeric formats and aligns trading days.
   
3. **Feature Generation** (`ml/features/`)
   - `TechnicalFeatureEngine`
   - `VolatilityAndRiskEngine`
   - `FundamentalFeatureEngine` (Joins SEC Fact + SEC Filing)
   - `MacroFeatureEngine`
   - **Validation Gate**: `LeakageValidator` checks all features against prediction timestamps.

4. **Model Execution** (`ml/models/`)
   - Evaluates features against frozen `.pkl` model weights.
   - Outputs: `prediction`, `prediction_probability`.

5. **Risk Execution** (`risk/engine/`)
   - Calculates tail-risk on historical price matrix.
   - Outputs: `VaR`, `CVaR`, `Risk Classification`.

6. **Intelligence Assembly** (`analytics/intelligence/`)
   - Combines Prediction + Risk + News Sentiment.
   - Outputs: `IntelligenceAssessment`.

## Provenance Enforcement
Every `IntelligenceAssessment` requires:
- `model_version`
- `feature_version`
- `risk_engine_version`
- `data_cutoff_time`

This guarantees that a dashboard metric can always be reconstructed exactly as it existed at the time of generation.
