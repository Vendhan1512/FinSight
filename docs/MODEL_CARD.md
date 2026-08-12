# FinSight Model Card

## 1. Model Details
- **Architecture**: Configurable (RandomForestClassifier, GradientBoostingClassifier, XGBoost).
- **Target**: Next $N$-day returns exceeding the benchmark (Binary Classification: OUTPERFORM / UNDERPERFORM).
- **Optimization**: Optuna Hyperparameter Optimization with `PR_AUC` objective.

## 2. Intended Use
- **Primary Use Case**: Assisting institutional portfolio managers in identifying asymmetrical risk-reward setups in public equities.
- **Out-of-Scope**: High-frequency trading (HFT), intraday execution, or fully autonomous trading.

## 3. Factors and Features
- **Technical**: Moving averages, RSI, MACD.
- **Fundamental**: Debt-to-Equity, Operating Margins (strictly Point-In-Time).
- **Macro**: CPI, Interest Rates, Unemployment (strictly Vintage-aligned).
- **Risk**: Volatility, Beta.

## 4. Evaluation Data
- **Validation**: Walk-Forward expanding window cross-validation (TimeSeriesSplit).
- **Embargo**: A mandatory $N$-day gap exists between train/test splits to eliminate serial correlation leakage.

## 5. Quantitative Analyses
- Primary evaluation metrics are Precision, Recall, PR-AUC, and F1-Score, due to the inherent class imbalance of financial returns.
- Probability Calibration (Platt Scaling / Isotonic) is applied to ensure prediction probabilities represent true likelihoods.

## 6. Ethical Considerations and Limitations
- The model is trained on surviving assets (Survivorship Bias risk).
- Market regime shifts (e.g., COVID-19) rapidly degrade predictive accuracy. Model performance is continuously monitored via KS and PSI drift metrics.
