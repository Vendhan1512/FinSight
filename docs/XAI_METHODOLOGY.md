# FinSight XAI Methodology

Explainable AI (XAI) ensures that ML predictions are interpretable by human portfolio managers.

## 1. Global Explanations
- Defines which features drive the model's behavior *on average* across the entire dataset.
- Evaluated using **Permutation Importance** (model-agnostic) or **Tree-based Feature Importance** (Gini impurity decrease).

## 2. Local Explanations
- Defines why the model made a specific prediction on a specific day for a specific asset.
- Evaluated using **SHAP (SHapley Additive exPlanations)**.
- SHAP values provide the exact marginal contribution of each feature to the final prediction probability.

## 3. Methodological Constraints
- **No Causal Claims**: SHAP values indicate correlation and feature attribution, NOT causation.
- Explanations are strictly bound to the exact `model_version` and `feature_version` that generated the prediction.
