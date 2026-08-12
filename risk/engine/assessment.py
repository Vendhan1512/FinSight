import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RiskAssessmentEngine:
    """
    Transparent, Rule-Based Risk Classification Engine.
    Strictly avoids arbitrary "weighted scores" or LLM hallucinations.
    Classifications are derived exclusively from empirical metrics.
    """
    
    @staticmethod
    def evaluate_risk(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a portfolio or asset's metrics against a strict cascading rule set.
        """
        classification = "LOW"
        triggered_rules = []
        
        max_drawdown = abs(metrics.get("max_drawdown", 0.0))
        cvar_99 = abs(metrics.get("cvar_99", 0.0)) # Expected Shortfall
        cvar_95 = abs(metrics.get("historical_cvar", 0.0))
        volatility = metrics.get("annualized_volatility", 0.0)
        risk_concentration = metrics.get("top_3_risk_concentration", 0.0)
        
        # --- RULE SET (Cascading) ---
        
        # 1. CRITICAL RULES
        if max_drawdown > 0.40:
            classification = "CRITICAL"
            triggered_rules.append(f"Max Drawdown ({max_drawdown:.1%}) exceeds 40% threshold.")
            
        if cvar_99 > 0.10:
            classification = "CRITICAL"
            triggered_rules.append(f"Expected Shortfall 99% ({cvar_99:.1%}) exceeds 10% daily tail threshold.")
            
        # 2. HIGH RULES (Only evaluate if not already CRITICAL)
        if classification != "CRITICAL":
            if max_drawdown > 0.20:
                classification = "HIGH"
                triggered_rules.append(f"Max Drawdown ({max_drawdown:.1%}) exceeds 20% threshold.")
                
            if cvar_95 > 0.05:
                classification = "HIGH"
                triggered_rules.append(f"Expected Shortfall 95% ({cvar_95:.1%}) exceeds 5% daily tail threshold.")
                
            if risk_concentration > 0.60:
                classification = "HIGH"
                triggered_rules.append(f"Severe Risk Concentration: Top 3 assets generate {risk_concentration:.1%} of portfolio volatility.")
                
        # 3. MODERATE RULES (Only evaluate if still LOW)
        if classification == "LOW":
            if volatility > 0.15:
                classification = "MODERATE"
                triggered_rules.append(f"Annualized Volatility ({volatility:.1%}) exceeds 15% threshold.")
                
            if cvar_95 > 0.02:
                classification = "MODERATE"
                triggered_rules.append(f"Expected Shortfall 95% ({cvar_95:.1%}) exceeds 2% daily tail threshold.")
                
        # If still LOW, explicit rule
        if classification == "LOW":
            triggered_rules.append("All metrics fall below MODERATE risk thresholds.")
            
        return {
            "classification": classification,
            "drivers": triggered_rules,
            "supporting_metrics": metrics,
            "methodology_version": "v1.0"
        }
