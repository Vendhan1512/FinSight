# FinSight System Limitations

This document objectively outlines the limitations discovered during the implementation of FinSight.

## 1. Provider Bottlenecks
- **AlphaVantage Rate Limits**: The free tier severely restricts full-market scans, causing pipeline timeouts if not strictly batched.
- **SEC EDGAR**: XBRL tagging is notoriously inconsistent across companies. The Fundamental Pipeline drops companies entirely if they use non-standard GAAP tags.

## 2. Temporal & Methodology Limitations
- **Macro Lag**: FRED data is heavily revised. While ALFRED preserves vintage integrity, the actual lag before macroeconomic prints become available is often 30-45 days, limiting their predictive edge for short-term models.
- **Survivorship Bias**: The cross-sectional universe only contains assets that survived to the present. Bankrupt or delisted tickers are not adequately represented in the backtest.
- **News Entity Resolution**: Simple string matching (e.g. "Apple") occasionally triggers false positives for ambiguous names.

## 3. Infrastructure Limitations
- The current implementation defaults to SQLite. Under heavy parallel ingestion, SQLite suffers from `database is locked` errors due to concurrent write contention. A full PostgreSQL deployment is required for high concurrency.
- The pipeline does not yet implement a full orchestrator (like Airflow or Dagster), relying instead on linear Python scripts and basic cron jobs.
