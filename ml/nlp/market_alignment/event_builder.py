import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.news import NewsArticle
from app.models.nlp import NewsArticleSentiment, NewsArticleTopic
from app.models.warehouse import AnalyticalMarket
from app.models.market_events import NewsMarketEvent
from ml.nlp.market_alignment.calendar import MarketCalendarAligner

logger = logging.getLogger(__name__)

class EventBuilder:
    """
    Constructs NewsMarketEvent records by fusing NLP outputs with AnalyticalMarket data.
    """
    
    def __init__(self, db: Session, benchmark_ticker: str = "SPY"):
        self.db = db
        self.benchmark_ticker = benchmark_ticker
        self.calendar = MarketCalendarAligner()
        self.methodology = "event_study_v1"

    def build_events_for_ticker(self, ticker: str, horizons: List[int] = [1, 5, 20]) -> Dict[str, Any]:
        """
        Builds events for a given ticker and returns statistics of the build.
        """
        # Fetch analytical market data for asset and benchmark
        market_query = select(AnalyticalMarket).where(AnalyticalMarket.symbol == ticker).order_by(AnalyticalMarket.original_timestamp)
        bench_query = select(AnalyticalMarket).where(AnalyticalMarket.symbol == self.benchmark_ticker).order_by(AnalyticalMarket.original_timestamp)
        
        asset_data = self.db.scalars(market_query).all()
        bench_data = self.db.scalars(bench_query).all()
        
        if not asset_data:
            return {"status": "error", "message": f"No market data for {ticker}"}
            
        # Convert to DataFrame for easier shifting
        asset_df = pd.DataFrame([{
            "date": m.original_timestamp,
            "close": float(m.close) if m.close else None,
            "log_return": float(m.log_return) if m.log_return else None
        } for m in asset_data]).set_index("date")
        
        bench_df = pd.DataFrame([{
            "date": m.original_timestamp,
            "close": float(m.close) if m.close else None,
            "log_return": float(m.log_return) if m.log_return else None
        } for m in bench_data]).set_index("date")
        
        # Calculate future returns and volatilities for horizons
        for h in horizons:
            # Future return is simply the cumulative log return over the next h days
            # We can use rolling sum of log return, shifted backwards
            asset_df[f"fwd_ret_{h}d"] = asset_df["log_return"].shift(-h).rolling(window=h, min_periods=1).sum()
            bench_df[f"bench_fwd_ret_{h}d"] = bench_df["log_return"].shift(-h).rolling(window=h, min_periods=1).sum()
            
            # Future volatility
            if h > 1:
                asset_df[f"fwd_vol_{h}d"] = asset_df["log_return"].shift(-h).rolling(window=h, min_periods=2).std()
            else:
                asset_df[f"fwd_vol_{h}d"] = None
                
        # Fetch Articles and Sentiments for this ticker (Assuming article provider mapping exists, or we search topics)
        # For this implementation, we assume we want all articles mapped to this ticker in NewsArticleEntity.
        # But wait, earlier we linked entities by canonical_entity_id == ticker
        from app.models.nlp import NewsArticleEntity
        
        articles_query = (
            select(NewsArticle, NewsArticleEntity, NewsArticleSentiment)
            .join(NewsArticleEntity, NewsArticle.article_id == NewsArticleEntity.article_id)
            .outerjoin(NewsArticleSentiment, NewsArticle.article_id == NewsArticleSentiment.article_id)
            .where(NewsArticleEntity.canonical_entity_id == ticker)
        )
        
        results = self.db.execute(articles_query).all()
        
        created_count = 0
        skipped_count = 0
        
        for article, entity, sentiment in results:
            # 1. Align calendar
            align_res = self.calendar.align_event(article.published_at)
            target_date = align_res["target_observation_date"]
            relation = align_res["market_session_relation"]
            
            # Ensure target_date is in index
            if target_date not in asset_df.index:
                # We don't have market data for the target date, skip
                skipped_count += 1
                continue
                
            # 2. Get topics
            topics = self.db.scalars(select(NewsArticleTopic).where(NewsArticleTopic.article_id == article.article_id)).all()
            top_topic = topics[0].topic_name if topics else None
            
            # 3. Build events for each horizon
            for h in horizons:
                fwd_ret = asset_df.loc[target_date, f"fwd_ret_{h}d"]
                fwd_vol = asset_df.loc[target_date, f"fwd_vol_{h}d"]
                
                if pd.isna(fwd_ret):
                    continue # Not enough future data
                    
                bench_fwd_ret = bench_df.loc[target_date, f"bench_fwd_ret_{h}d"] if target_date in bench_df.index else None
                
                abnormal = None
                if fwd_ret is not None and bench_fwd_ret is not None and not pd.isna(bench_fwd_ret):
                    abnormal = float(fwd_ret - bench_fwd_ret) # Simple benchmark adjusted return
                    
                end_date = target_date + timedelta(days=h) # Rough approximation for end date storage
                
                # Check if event already exists
                existing = self.db.execute(
                    select(NewsMarketEvent).where(
                        (NewsMarketEvent.article_id == article.article_id) & 
                        (NewsMarketEvent.entity_id == ticker) &
                        (NewsMarketEvent.horizon == f"{h}d")
                    )
                ).scalar_one_or_none()
                
                if not existing:
                    event = NewsMarketEvent(
                        article_id=article.article_id,
                        entity_id=ticker,
                        published_at=article.published_at,
                        market_session_relation=relation,
                        sentiment=sentiment.sentiment_label if sentiment else None,
                        topic=top_topic,
                        market_observation_start=target_date,
                        market_observation_end=end_date,
                        horizon=f"{h}d",
                        future_return=float(fwd_ret),
                        future_volatility=float(fwd_vol) if pd.notna(fwd_vol) else None,
                        benchmark_id=self.benchmark_ticker,
                        benchmark_return=float(bench_fwd_ret) if pd.notna(bench_fwd_ret) else None,
                        abnormal_return=abnormal,
                        methodology_version=self.methodology
                    )
                    self.db.add(event)
                    created_count += 1
                    
        self.db.commit()
        
        return {
            "status": "success",
            "ticker": ticker,
            "events_created": created_count,
            "events_skipped_no_market_data": skipped_count
        }
