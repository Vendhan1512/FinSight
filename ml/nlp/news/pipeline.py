import logging
import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.news import NewsArticle
from app.models.nlp import (
    NLPProcessingRun, NewsArticleSentiment, NewsArticleEntity, NewsArticleTopic
)
from ml.nlp.news.preprocessing.text_normalizer import TextNormalizer
from ml.nlp.news.sentiment.finbert_engine import FinBERTSentimentEngine
from ml.nlp.news.entities.ner_engine import NEREngine
from ml.nlp.news.entity_resolution.resolver import EntityResolver
from ml.nlp.news.topics.topic_extractor import TopicExtractor
from ml.nlp.news.quality.nlp_validator import NLPValidator

logger = logging.getLogger(__name__)

class NewsNLPPipeline:
    """
    Orchestrates the NLP processing of news articles.
    """
    def __init__(self, db: Session, fallback_mode: bool = False):
        self.db = db
        self.sentiment_engine = FinBERTSentimentEngine(fallback_mode=fallback_mode)
        self.ner_engine = NEREngine(fallback_mode=fallback_mode)
        self.entity_resolver = EntityResolver()
        self.topic_extractor = TopicExtractor()
        
        # We define a combined model version string to represent this pipeline's state
        self.pipeline_version = f"sent:{self.sentiment_engine.MODEL_NAME}_{self.sentiment_engine.VERSION}|ner:{self.ner_engine.MODEL_NAME}_{self.ner_engine.VERSION}|top:{self.topic_extractor.MODEL_VERSION}"

    def process_batch(self, limit: int = 100) -> Dict[str, Any]:
        """
        Incrementally processes articles that haven't been processed by this pipeline version.
        """
        start_time = time.time()
        
        # Find articles that haven't been processed by this pipeline version
        # To do this efficiently, we look for articles that DO NOT have a sentiment record with this model version
        # Subquery or outer join
        subq = (
            select(NewsArticleSentiment.article_id)
            .where(NewsArticleSentiment.model_version == f"{self.sentiment_engine.MODEL_NAME}_{self.sentiment_engine.VERSION}")
        ).scalar_subquery()
        
        articles_to_process = self.db.scalars(
            select(NewsArticle)
            .where(NewsArticle.article_id.notin_(subq))
            .limit(limit)
        ).all()
        
        if not articles_to_process:
            return {"status": "success", "processed": 0, "message": "No new articles to process"}
            
        # Create a run record
        run = NLPProcessingRun(model_version=self.pipeline_version)
        self.db.add(run)
        self.db.flush()
        
        errors = 0
        processed = 0
        
        for article in articles_to_process:
            try:
                self._process_single_article(article)
                processed += 1
            except Exception as e:
                logger.error(f"Error processing article {article.article_id}: {e}")
                errors += 1
                
        run.end_time = time.time() # Just for duration calculation
        run.duration = time.time() - start_time
        run.articles_processed = processed
        run.errors = errors
        
        # Actually save end_time correctly as datetime
        from datetime import datetime
        run.end_time = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "status": "success",
            "processed": processed,
            "errors": errors,
            "duration": run.duration,
            "run_id": str(run.run_id)
        }

    def _process_single_article(self, article: NewsArticle):
        """
        Processes a single article and writes results to the DB.
        """
        text = article.content if article.content else article.description
        if not text:
            text = article.title
            
        # 1. Validation
        val_res = NLPValidator.validate_article(text)
        if not val_res["valid"]:
            logger.warning(f"Article {article.article_id} skipped: {val_res['reason']}")
            # We must insert a dummy sentiment record so it doesn't get picked up again
            self._insert_failed_sentiment(article.article_id)
            return
            
        # 2. Normalization (Non-destructive to original)
        norm_text = TextNormalizer.normalize(text)
        
        # 3. Sentiment
        sentiment_res = self.sentiment_engine.analyze(norm_text)
        sentiment_record = NewsArticleSentiment(
            article_id=article.article_id,
            sentiment_model=self.sentiment_engine.MODEL_NAME,
            model_version=f"{self.sentiment_engine.MODEL_NAME}_{self.sentiment_engine.VERSION}",
            sentiment_label=sentiment_res["label"],
            sentiment_score=sentiment_res["score"],
            confidence=sentiment_res["confidence"]
        )
        self.db.add(sentiment_record)
        
        # 4. Entities
        raw_ents = self.ner_engine.extract_entities(norm_text)
        resolved_ents = self.entity_resolver.resolve(raw_ents)
        
        for ent in resolved_ents:
            entity_record = NewsArticleEntity(
                article_id=article.article_id,
                canonical_entity_id=ent["canonical_entity_id"],
                entity_type=ent["entity_type"],
                canonical_name=ent["canonical_name"],
                aliases=ent["aliases"],
                ticker=ent["ticker"],
                resolution_method=ent["resolution_method"],
                resolution_confidence=ent["resolution_confidence"]
            )
            self.db.add(entity_record)
            
        # 5. Topics
        topics = self.topic_extractor.extract_topics(norm_text)
        for t in topics:
            topic_record = NewsArticleTopic(
                article_id=article.article_id,
                topic_name=t["topic_name"],
                topic_score=t["topic_score"],
                model_version=t["model_version"],
                is_generated=t["is_generated"]
            )
            self.db.add(topic_record)
            
    def _insert_failed_sentiment(self, article_id):
        # Insert a blank sentiment to prevent infinite retry loop
        sentiment_record = NewsArticleSentiment(
            article_id=article_id,
            sentiment_model=self.sentiment_engine.MODEL_NAME,
            model_version=f"{self.sentiment_engine.MODEL_NAME}_{self.sentiment_engine.VERSION}",
            sentiment_label="NEUTRAL",
            sentiment_score=0.0,
            confidence=0.0
        )
        self.db.add(sentiment_record)
