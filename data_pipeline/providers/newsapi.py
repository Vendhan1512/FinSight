import os
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class NewsProvider(ABC):
    """Abstract base class for all News Providers."""
    
    @abstractmethod
    def fetch_articles(self, entity: str, start_date: str, end_date: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        pass

class NewsAPIProvider(NewsProvider):
    """
    Implementation for NewsAPI (newsapi.org).
    Respects rate limits and exact historical queries.
    """
    
    BASE_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("CRITICAL: NEWS_API_KEY environment variable is missing. Real ingestion requires a valid key.")
            
    def fetch_articles(self, entity: str, start_date: str, end_date: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Fetches historical articles for a given entity constraint.
        Requires exact date boundaries to prevent leakage.
        """
        # We assume entity string can contain boolean logic supported by NewsAPI 
        # e.g., '"Apple Inc" OR "AAPL"'
        
        params = {
            "q": entity,
            "from": start_date,
            "to": end_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "page": page,
            "apiKey": self.api_key
        }
        
        try:
            logger.info(f"NewsAPI Request: q='{entity}', from={start_date}, to={end_date}, page={page}")
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            
            # Catch HTTP errors
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                raise ValueError(f"NewsAPI Error: {data.get('message', 'Unknown error')}")
                
            return {
                "total_results": data.get("totalResults", 0),
                "articles": data.get("articles", [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI HTTP Error: {e}")
            raise
