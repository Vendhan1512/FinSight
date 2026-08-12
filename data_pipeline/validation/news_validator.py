import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.news import NewsArticle, NewsArticleDuplicate

logger = logging.getLogger(__name__)

class NewsQualityEngine:
    """Validates the data integrity and leakage risk of ingested news."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def run_quality_check(self) -> Dict[str, Any]:
        """Runs the full suite of data quality checks on the news database."""
        
        now = datetime.utcnow()
        
        total_articles = self.db.query(NewsArticle).count()
        total_duplicates_logged = self.db.query(NewsArticleDuplicate).count()
        
        # 1. Missing publication timestamp
        missing_pub_time = self.db.query(NewsArticle).filter(NewsArticle.published_at == None).count()
        
        # 2. Missing URL
        missing_url = self.db.query(NewsArticle).filter((NewsArticle.url == None) | (NewsArticle.url == "")).count()
        
        # 3. Missing Title
        missing_title = self.db.query(NewsArticle).filter((NewsArticle.title == None) | (NewsArticle.title == "")).count()
        
        # 4. Future Publication Timestamp (Extreme Leakage Risk)
        future_timestamps = self.db.query(NewsArticle).filter(NewsArticle.published_at > now).count()
        
        # 5. Database-level Duplicate Content Hashes (Should be 0 if ingestor works)
        # Groups by hash, counts occurrences > 1
        dup_hash_query = self.db.query(NewsArticle.content_hash, func.count(NewsArticle.content_hash)) \
                            .group_by(NewsArticle.content_hash) \
                            .having(func.count(NewsArticle.content_hash) > 1).all()
        db_duplicate_hashes = len(dup_hash_query)
        
        passed = (missing_pub_time == 0 and 
                  missing_url == 0 and 
                  missing_title == 0 and 
                  future_timestamps == 0 and 
                  db_duplicate_hashes == 0)
                  
        return {
            "status": "PASS" if passed else "FAIL",
            "total_articles": total_articles,
            "total_duplicates_intercepted": total_duplicates_logged,
            "issues": {
                "missing_publication_time": missing_pub_time,
                "missing_url": missing_url,
                "missing_title": missing_title,
                "future_timestamps": future_timestamps,
                "unhandled_duplicate_hashes": db_duplicate_hashes
            }
        }
