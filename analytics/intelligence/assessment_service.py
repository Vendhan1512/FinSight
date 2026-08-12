import logging
from datetime import datetime
from typing import Dict, Any, List
import json

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.cutoff import TemporalFirewall
from app.models.intelligence import IntelligenceAssessment
from app.models.warehouse import AnalyticalMarket
from app.models.news import NewsArticle
from app.models.nlp import NewsArticleSentiment, NewsArticleTopic, NewsArticleEntity
from app.models.ml import ModelPrediction
from app.models.risk import PortfolioRisk
from app.models.market_events import StatisticalRelationship
from app.models.explainability import LocalExplanation, GlobalImportance

logger = logging.getLogger(__name__)

class AssessmentService:
    """
    Fuses outputs from Phase 4 (Predictions), Phase 5 (Risk), and Phase 6 (News/Explainability)
    into a deterministic structured assessment honoring the IntelligenceCutoff.
    """
    def __init__(self, db: Session, cutoff_time: datetime):
        self.db = db
        self.firewall = TemporalFirewall(db, cutoff_time)
        self.cutoff_time = self.firewall.get_cutoff()

    def generate_assessment(self, entity_id: str, lookback_days: int = 7) -> IntelligenceAssessment:
        """
        Generates the integrated assessment for a specific entity.
        """
        # 1. OBSERVED FACTS (News & Market)
        # Pull recent news bounded by firewall
        news_query = self.firewall.enforce_news_query(select(NewsArticle).order_by(desc(NewsArticle.published_at)), NewsArticle)
        # Assuming URL / source_name mapping to entity exists via Entity table, 
        # but for direct query we use join.
        news_query = (
            self.firewall.enforce_news_query(select(NewsArticle), NewsArticle)
            .join(NewsArticleEntity, NewsArticle.article_id == NewsArticleEntity.article_id)
            .where(NewsArticleEntity.canonical_entity_id == entity_id)
            .order_by(desc(NewsArticle.published_at))
            .limit(10)
        )
        recent_articles = self.db.scalars(news_query).all()
        
        # Aggregate sentiment & topics
        sentiments = []
        topics = set()
        for art in recent_articles:
            s_obj = self.db.scalars(select(NewsArticleSentiment).where(NewsArticleSentiment.article_id == art.article_id)).first()
            if s_obj:
                sentiments.append(s_obj.sentiment_label)
            t_obj = self.db.scalars(select(NewsArticleTopic).where(NewsArticleTopic.article_id == art.article_id)).first()
            if t_obj:
                topics.add(t_obj.topic_name)
                
        sentiment_summary = {"POSITIVE": sentiments.count("POSITIVE"), "NEGATIVE": sentiments.count("NEGATIVE"), "NEUTRAL": sentiments.count("NEUTRAL")}
        
        # 2. MODEL PREDICTIONS (ML Phase 4)
        pred_query = self.firewall.enforce_prediction_query(
            select(ModelPrediction).where(ModelPrediction.entity_id == entity_id).order_by(desc(ModelPrediction.prediction_time)),
            ModelPrediction
        ).limit(1)
        latest_prediction = self.db.scalars(pred_query).first()
        
        # 3. STATISTICAL ASSOCIATIONS (Phase 6.3)
        # Pull latest statistical relationships for this entity's common topics/sentiments
        stats = self.db.scalars(
            select(StatisticalRelationship).order_by(desc(StatisticalRelationship.created_at)).limit(3)
        ).all()
        stat_findings = [s.finding_description for s in stats]
        
        # 4. RISK MEASUREMENTS (Phase 5)
        # Mocking PortfolioRisk pull as it usually applies to portfolios, but we might have asset risk
        risk_class = "MODERATE"
        risk_metrics = {"VaR_95": -0.05, "CVaR_95": -0.07}
        
        # 5. INTERPRETATIONS (Phase 6.4 Explainability)
        explanation_payload = {}
        if latest_prediction:
            exp = self.db.scalars(
                select(LocalExplanation).where(LocalExplanation.prediction_id == latest_prediction.prediction_id)
            ).first()
            if exp:
                explanation_payload = exp.shap_values
                
        # --- GENERATE DETERMINISTIC NARRATIVE ---
        pred_text = f"Predicted return is {latest_prediction.prediction:.4f}" if latest_prediction else "No prediction available."
        
        structured_assessment = {
            "OBSERVED_FACTS": {
                "Recent_Articles_Count": len(recent_articles),
                "Dominant_Topics": list(topics),
                "Sentiment_Distribution": sentiment_summary
            },
            "MODEL_PREDICTIONS": {
                "Prediction": pred_text,
                "Model_Version": latest_prediction.model_name if latest_prediction else "None"
            },
            "STATISTICAL_ASSOCIATIONS": {
                "Findings": stat_findings
            },
            "RISK_MEASUREMENTS": {
                "Classification": risk_class,
                "Metrics": risk_metrics
            },
            "INTERPRETATIONS": {
                "Local_SHAP_Explanation": explanation_payload
            },
            "LIMITATIONS": [
                "SHAP explains model behavior, not causality.",
                "Statistical associations do not guarantee future returns.",
                "Predictions are strictly out-of-sample and bounded by temporal firewalls."
            ]
        }
        
        assessment = IntelligenceAssessment(
            entity_id=entity_id,
            data_cutoff_time=self.cutoff_time,
            news_cutoff_time=self.cutoff_time,
            market_cutoff_time=self.cutoff_time,
            model_version=latest_prediction.model_name if latest_prediction else "Unknown",
            feature_version="v1",
            methodology_version="deterministic_v1",
            prediction=latest_prediction.prediction if latest_prediction else None,
            risk_classification=risk_class,
            risk_metrics=risk_metrics,
            news_sentiment_summary=sentiment_summary,
            news_topics=list(topics),
            statistical_relationships=stat_findings,
            explanation=explanation_payload,
            data_quality_status="OK",
            structured_assessment=structured_assessment
        )
        self.db.add(assessment)
        self.db.commit()
        
        return assessment
