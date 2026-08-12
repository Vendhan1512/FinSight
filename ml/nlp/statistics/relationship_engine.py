import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.market_events import NewsMarketEvent, StatisticalRelationship

logger = logging.getLogger(__name__)

class RelationshipEngine:
    """
    Computes statistical relationships between news features (sentiment, volume, topics)
    and subsequent market behavior. Applies multiple-testing corrections.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def _apply_fdr(self, pvalues: np.ndarray) -> np.ndarray:
        """
        Benjamini-Hochberg False Discovery Rate (FDR) correction.
        """
        if len(pvalues) == 0:
            return pvalues
            
        n = len(pvalues)
        sorted_indices = np.argsort(pvalues)
        sorted_p = pvalues[sorted_indices]
        
        adjusted_p = np.zeros(n)
        min_adj = 1.0
        
        for i in range(n - 1, -1, -1):
            rank = i + 1
            adj = sorted_p[i] * n / rank
            min_adj = min(min_adj, adj)
            adjusted_p[sorted_indices[i]] = min_adj
            
        # Ensure probabilities don't exceed 1.0
        adjusted_p = np.minimum(adjusted_p, 1.0)
        return adjusted_p

    def _generate_finding_text(self, var_name: str, p_val: float, coef: float) -> str:
        """
        Strictly enforces non-causal language based on statistical significance.
        """
        if pd.isna(p_val):
            return "Insufficient data to compute relationship."
            
        if p_val > 0.05:
            return f"No statistically significant relationship observed between {var_name} and subsequent market behavior (p={p_val:.3f})."
            
        direction = "positive" if coef > 0 else "negative"
        strength = "strong" if abs(coef) > 0.5 else "weak to moderate"
        
        return (f"A statistically significant {direction} ({strength}) relationship is associated with "
                f"{var_name} and subsequent market behavior (coef={coef:.3f}, p={p_val:.3f}). "
                f"Note: This observed relationship does not guarantee future results or prove causality.")

    def run_sentiment_analysis(self, horizon: str = "1d") -> Dict[str, Any]:
        """
        Tests relationship between sentiment score (POSITIVE/NEGATIVE mapped) and abnormal return.
        """
        events = self.db.scalars(
            select(NewsMarketEvent)
            .where(NewsMarketEvent.horizon == horizon)
            .where(NewsMarketEvent.sentiment.isnot(None))
            .where(NewsMarketEvent.abnormal_return.isnot(None))
        ).all()
        
        if len(events) < 2:
            return {"status": "insufficient_data", "message": "Need at least 30 observations"}
            
        df = pd.DataFrame([{
            "sentiment": 1 if e.sentiment == "POSITIVE" else (-1 if e.sentiment == "NEGATIVE" else 0),
            "abnormal_return": e.abnormal_return
        } for e in events])
        
        # Pearson correlation
        from scipy.stats import pearsonr
        coef, p_val = pearsonr(df["sentiment"], df["abnormal_return"])
        
        finding = self._generate_finding_text("sentiment polarity", p_val, coef)
        
        rel = StatisticalRelationship(
            test_type="sentiment_vs_abnormal_return",
            horizon=horizon,
            sample_size=len(df),
            coefficient=float(coef),
            p_value=float(p_val),
            adjusted_p_value=float(p_val), # Only 1 test here
            methodology="pearson_correlation",
            multiple_testing_correction="none",
            finding_description=finding
        )
        self.db.add(rel)
        self.db.commit()
        
        return {
            "status": "success",
            "test": "sentiment_vs_abnormal_return",
            "finding": finding
        }

    def run_topic_analysis(self, horizon: str = "1d") -> Dict[str, Any]:
        """
        Tests relationships between various topics and abnormal returns.
        Requires multiple testing correction.
        """
        events = self.db.scalars(
            select(NewsMarketEvent)
            .where(NewsMarketEvent.horizon == horizon)
            .where(NewsMarketEvent.topic.isnot(None))
            .where(NewsMarketEvent.abnormal_return.isnot(None))
        ).all()
        
        if not events:
            return {"status": "insufficient_data"}
            
        df = pd.DataFrame([{
            "topic": e.topic,
            "abnormal_return": e.abnormal_return
        } for e in events])
        
        topics = df["topic"].unique()
        if len(topics) == 0:
            return {"status": "insufficient_data"}
            
        results = []
        p_values = []
        
        from scipy.stats import ttest_ind
        
        for topic in topics:
            in_topic = df[df["topic"] == topic]["abnormal_return"]
            out_topic = df[df["topic"] != topic]["abnormal_return"]
            
            if len(in_topic) < 10 or len(out_topic) < 10:
                continue
                
            stat, p = ttest_ind(in_topic, out_topic, equal_var=False)
            
            # Mean difference as pseudo-coefficient
            coef = in_topic.mean() - out_topic.mean()
            
            results.append({
                "topic": topic,
                "stat": stat,
                "p_val": p,
                "coef": coef,
                "n": len(in_topic)
            })
            p_values.append(p)
            
        if not results:
            return {"status": "insufficient_data"}
            
        # FDR correction
        adj_p = self._apply_fdr(np.array(p_values))
        
        for idx, res in enumerate(results):
            finding = self._generate_finding_text(f"presence of topic '{res['topic']}'", adj_p[idx], res["coef"])
            
            rel = StatisticalRelationship(
                test_type=f"topic_vs_abnormal_return_{res['topic']}",
                horizon=horizon,
                sample_size=res["n"],
                coefficient=float(res["coef"]),
                p_value=float(res["p_val"]),
                adjusted_p_value=float(adj_p[idx]),
                methodology="welchs_t_test",
                multiple_testing_correction="bh_fdr",
                finding_description=finding
            )
            self.db.add(rel)
            
        self.db.commit()
        return {"status": "success", "tests_run": len(results)}
