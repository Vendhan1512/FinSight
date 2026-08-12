# FinSight Architecture

## System Overview
FinSight is an institutional-grade, predictive analytics and risk intelligence platform for public equities. The architecture enforces strict **Point-In-Time (PIT)** integrity, preventing lookahead bias in machine learning models and trading simulations.

## Core Layers

1. **Ingestion Layer (Data Pipeline)**
   - **Market Data**: Ingests daily price/volume data via AlphaVantage.
   - **Macroeconomic Data**: Ingests ALFRED (ArchivaL FRED) vintage data to ensure only information known *at the time* is used.
   - **Fundamental Data**: Ingests SEC EDGAR XBRL filings, aligning to the *filing date*, not the report date.
   - **News Data**: Ingests raw news articles via NewsAPI for NLP processing.

2. **Feature Store**
   - Implements strict temporal joins using `pandas.merge_asof`.
   - Groups features into Technical, Volatility, Volume, Fundamental, and Macro.
   - Runs `LeakageValidator` to explicitly abort if $T_{feature} > T_{prediction}$.

3. **Machine Learning Pipeline**
   - Supports Scikit-Learn tree-based models and Optuna hyperparameter optimization.
   - Uses `TimeSeriesSplit` with an explicit `gap` (embargo) to prevent serial correlation leakage.
   - Outputs probabilistic classifications (e.g., "Outperform").

4. **Risk Engine**
   - Computes Value at Risk (VaR) and Conditional VaR (Expected Shortfall).
   - Generates Portfolio Risk Attribution (MCR, CCR, PCR).
   - Executes Historical Stress Tests (e.g., COVID-19, GFC).

5. **API & Frontend**
   - FastAPI backend exposes RESTful endpoints with JWT authentication.
   - React/Vite frontend visualizes intelligence asynchronously.

## Deployment Model
- Python 3.11 virtual environment.
- SQLite backend (PostgreSQL target for production).
- Uvicorn ASGI server.
