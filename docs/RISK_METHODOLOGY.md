# FinSight Risk Methodology

## 1. Value at Risk (VaR)
FinSight computes VaR using the **Historical Simulation** method by default.
- **Confidence Levels**: 95%, 99%.
- **Horizon**: Daily (can be scaled via $\sqrt{t}$).
- **Formula**: `Percentile(Historical Returns, 1 - Confidence)`.

## 2. Conditional VaR (Expected Shortfall)
Measures the expected loss *given* that the VaR threshold has been breached.
- **Formula**: `Mean(Returns[Returns < VaR])`.
- Captures tail risk better than standard VaR in non-normal distributions.

## 3. Portfolio Risk Attribution
- **Marginal Contribution to Risk (MCR)**: How much portfolio volatility changes by adding 1 unit of the asset.
- **Component Contribution to Risk (CCR)**: The absolute risk contribution (MCR * weight).
- **Percentage Contribution to Risk (PCR)**: CCR / Total Portfolio Volatility.

## 4. Historical Stress Testing
Replays historical crisis scenarios (e.g., 2008 GFC, 2020 COVID-19) on the current portfolio weights to estimate theoretical drawdowns.
