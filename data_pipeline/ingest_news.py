import logging
import hashlib
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.news import NewsSource, NewsArticle, NewsArticleDuplicate, NewsIngestionRun
from data_pipeline.providers.newsapi import NewsAPIProvider

logger = logging.getLogger(__name__)

class NewsIngestor:
    """Orchestrates the retrieval, deduplication, and insertion of real news."""
    
    def __init__(self, db: Session):
        self.db = db
        # Instantiating provider will throw ValueError if API key is missing.
        self.provider = NewsAPIProvider()
        
    def _generate_content_hash(self, title: str, url: str, source_name: str) -> str:
        """Generates a deterministic hash to prevent duplicate ingestion."""
        raw = f"{title}|{url}|{source_name}".lower().encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    def _process_article(self, article_data: Dict[str, Any]) -> str:
        """
        Processes a single article. 
        Returns "INSERTED", "DUPLICATE", or "ERROR".
        """
        try:
            source_data = article_data.get("source", {})
            source_name = source_data.get("name", "Unknown")
            source_id_str = source_data.get("id")
            
            title = article_data.get("title")
            url = article_data.get("url")
            published_at_str = article_data.get("publishedAt")
            
            if not title or not url or not published_at_str:
                return "ERROR" # Malformed article
                
            content_hash = self._generate_content_hash(title, url, source_name)
            
            # Check for exact duplicate hash in the DB
            existing_article = self.db.query(NewsArticle).filter(NewsArticle.content_hash == content_hash).first()
            
            if existing_article:
                # Log duplicate explicitly
                duplicate = NewsArticleDuplicate(
                    canonical_article_id=existing_article.article_id,
                    duplicate_article_id=url,
                    decision_reason="Identical content_hash (title+url+source)"
                )
                self.db.add(duplicate)
                self.db.commit()
                return "DUPLICATE"
                
            # Upsert Source if needed
            if source_id_str:
                existing_source = self.db.query(NewsSource).filter(NewsSource.source_id == source_id_str).first()
                if not existing_source:
                    new_source = NewsSource(source_id=source_id_str, name=source_name)
                    self.db.add(new_source)
                    
            # Insert Article
            # Truncation check
            content = article_data.get("content", "")
            if content and "[+" in content: # NewsAPI truncates with [+1234 chars]
                content = content + " [TRUNCATED_BY_PROVIDER]"
                
            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
                
            new_article = NewsArticle(
                provider="newsapi",
                source_id=source_id_str,
                source_name=source_name,
                author=article_data.get("author"),
                title=title,
                description=article_data.get("description"),
                content=content,
                url=url,
                published_at=published_at,
                content_hash=content_hash
            )
            self.db.add(new_article)
            self.db.commit()
            return "INSERTED"
            
        except IntegrityError:
            self.db.rollback()
            return "ERROR"
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            self.db.rollback()
            return "ERROR"

    def run_ingestion(self, entity_query: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Runs the end-to-end ingestion pipeline."""
        
        # 1. Initialize Run Tracking
        run = NewsIngestionRun(
            provider="newsapi",
            query=entity_query
        )
        self.db.add(run)
        self.db.commit()
        
        logger.info(f"Started News Ingestion Run: {run.run_id}")
        
        try:
            # 2. Fetch Data
            # Note: A production system would loop through pages. We fetch page 1 (100 articles) for Sprint 6.1.
            response = self.provider.fetch_articles(entity_query, start_date, end_date, page=1, page_size=100)
            
            articles = response.get("articles", [])
            run.records_requested = response.get("total_results", 0)
            run.records_received = len(articles)
            
            # 3. Process Articles
            for article in articles:
                status = self._process_article(article)
                if status == "INSERTED":
                    run.records_inserted += 1
                elif status == "DUPLICATE":
                    run.duplicates += 1
                elif status == "ERROR":
                    run.errors += 1
                    
            run.status = "COMPLETED"
            run.end_time = datetime.utcnow()
            self.db.commit()
            
            return {
                "run_id": str(run.run_id),
                "status": run.status,
                "records_requested": run.records_requested,
                "records_received": run.records_received,
                "records_inserted": run.records_inserted,
                "duplicates": run.duplicates,
                "errors": run.errors
            }
            
        except Exception as e:
            run.status = "FAILED"
            run.error_message = str(e)
            run.end_time = datetime.utcnow()
            self.db.commit()
            logger.error(f"Ingestion Run {run.run_id} FAILED: {e}")
            raise
