import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.cutoff import TemporalFirewall
from app.models.news import NewsArticle
from app.models.warehouse import AnalyticalMarket
from app.models.ml import ModelPrediction
from app.models.nlp import NewsArticleEntity

logger = logging.getLogger(__name__)

class TimelineBuilder:
    """
    Constructs a strictly chronologically ordered event timeline.
    Forbids automated causal narratives.
    """
    
    def __init__(self, db: Session, cutoff_time: datetime):
        self.db = db
        self.firewall = TemporalFirewall(db, cutoff_time)
        
    def build_timeline(self, entity_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        events = []
        
        # 1. Get News Events
        news_query = (
            self.firewall.enforce_news_query(select(NewsArticle), NewsArticle)
            .join(NewsArticleEntity, NewsArticle.article_id == NewsArticleEntity.article_id)
            .where(NewsArticleEntity.canonical_entity_id == entity_id)
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        for art in self.db.scalars(news_query).all():
            events.append({
                "timestamp": art.published_at,
                "type": "NEWS EVENT",
                "description": f"Article published: {art.title}",
                "source_id": str(art.article_id)
            })
            
        # 2. Get Market Observations (just extreme moves or recent ones to avoid flooding)
        # We'll just grab the 5 most recent prior to cutoff
        market_query = (
            self.firewall.enforce_market_query(select(AnalyticalMarket), AnalyticalMarket)
            .where(AnalyticalMarket.symbol == entity_id)
            .order_by(desc(AnalyticalMarket.original_timestamp))
            .limit(5)
        )
        for mkt in self.db.scalars(market_query).all():
            events.append({
                "timestamp": mkt.original_timestamp,
                "type": "MARKET OBSERVATION",
                "description": f"Market closed at {mkt.close:.2f} (Log Return: {mkt.log_return})",
                "source_id": str(mkt.id)
            })
            
        # 3. Get Model Predictions
        pred_query = (
            self.firewall.enforce_prediction_query(select(ModelPrediction), ModelPrediction)
            .where(ModelPrediction.entity_id == entity_id)
            .order_by(desc(ModelPrediction.prediction_time))
            .limit(5)
        )
        for pred in self.db.scalars(pred_query).all():
            events.append({
                "timestamp": pred.prediction_time,
                "type": "MODEL PREDICTION",
                "description": f"Model '{pred.model_name}' predicted {pred.prediction:.4f}",
                "source_id": str(pred.prediction_id)
            })
            
        # Sort strictly chronologically
        events.sort(key=lambda x: x["timestamp"])
        
        return events
