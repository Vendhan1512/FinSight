# FinSight Data Sources

This document strictly defines the authoritative sources of truth for the FinSight platform.

## 1. Market Data (AlphaVantage)
- **Type**: Daily End-of-Day (EOD) pricing and volume.
- **Usage**: Calculation of technical indicators, volatility, returns, and target generation.
- **Provider Limit**: Subject to API rate limits (e.g. 25 requests/day on free tier).

## 2. Fundamental Data (SEC EDGAR)
- **Type**: 10-K and 10-Q XBRL financial facts.
- **Usage**: Debt-to-Equity, Operating Margin, Revenue.
- **Integrity**: FinSight explicitly maps facts to their `filing_date` (the day the public saw it), rejecting the `end_date` (the quarter boundary) for ML training to prevent lookahead bias.

## 3. Macroeconomic Data (FRED)
- **Type**: Inflation (CPI), Interest Rates (FEDFUNDS, GS10), Unemployment (UNRATE).
- **Usage**: Regime detection, macroeconomic feature engineering.
- **Integrity**: Requires `realtime_start` vintage mapping.

## 4. News Data (NewsAPI)
- **Type**: Financial news articles and headlines.
- **Usage**: Sentiment analysis, topic clustering, and event study alignment.
- **Integrity**: Aligned to market data using calendar-aware timestamp mapping.
