# FinSight Production Monitoring

Monitoring ensures the production system remains statistically valid and operationally healthy.

## 1. Data Quality Monitoring
Checks run natively against the warehouse:
- Record count anomalies.
- Null/Missingness thresholds.
- Data Freshness (staleness alerts).

## 2. Feature & Prediction Drift
- **Continuous Features**: Evaluated using the **Kolmogorov-Smirnov (KS)** test to detect shifting distributions.
- **Categorical Features & Missingness**: Evaluated using the **Population Stability Index (PSI)**.
- **Prediction Drift**: Monitors if the model starts predicting "OUTPERFORM" at vastly different rates than during training.

## 3. Realized Performance Tracking
- The `performance_engine` securely waits until $T + horizon$ has elapsed in real calendar time before joining predictions against the true warehouse outcomes.
- Prevents premature scoring and lookahead leakage in monitoring dashboards.

## 4. Alerting
- Violations generate `SystemAlert` records in the database with severity `WARNING` or `CRITICAL`.
