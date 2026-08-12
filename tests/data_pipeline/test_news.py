import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.models.news import NewsSource, NewsArticle, NewsArticleDuplicate, NewsIngestionRun
from data_pipeline.ingest_news import NewsIngestor
from data_pipeline.validation.news_validator import NewsQualityEngine

# ==========================================
# TEST FIXTURES
# ==========================================
MOCK_NEWSAPI_RESPONSE = {
    "status": "ok",
    "total_results": 2,
    "articles": [
        {
            "source": {"id": "reuters", "name": "Reuters"},
            "author": "Jane Doe",
            "title": "Apple announces new product",
            "description": "Apple Inc is announcing...",
            "url": "https://reuters.com/apple-news-1",
            "publishedAt": "2023-10-01T12:00:00Z",
            "content": "Full content of article 1 [+100 chars]"
        },
        {
            "source": {"id": None, "name": "Unknown Blog"},
            "author": None,
            "title": "Duplicate Apple News",
            # We use the exact same title/url to trigger deduplication check if modified, but let's make it a unique article first
            "description": "Another article",
            "url": "https://blog.com/apple-news-2",
            "publishedAt": "2023-10-01T13:00:00Z",
            "content": "Short content"
        }
    ]
}

@pytest.fixture
def mock_news_provider():
    with patch("data_pipeline.ingest_news.NewsAPIProvider") as MockProvider:
        instance = MockProvider.return_value
        instance.fetch_articles.return_value = MOCK_NEWSAPI_RESPONSE
        yield instance

def test_news_ingestion_pipeline(db_session, mock_news_provider):
    """Test that ingestion correctly inserts articles, handles sources, and tracks the run."""
    ingestor = NewsIngestor(db_session)
    ingestor.provider = mock_news_provider
    
    result = ingestor.run_ingestion(
        entity_query='"Apple Inc"',
        start_date="2023-10-01",
        end_date="2023-10-02"
    )
    
    assert result["status"] == "COMPLETED"
    assert result["records_received"] == 2
    assert result["records_inserted"] == 2
    assert result["duplicates"] == 0
    
    # Verify DB
    articles = db_session.query(NewsArticle).all()
    assert len(articles) == 2
    
    reuters_article = db_session.query(NewsArticle).filter(NewsArticle.url == "https://reuters.com/apple-news-1").first()
    assert reuters_article is not None
    assert "TRUNCATED_BY_PROVIDER" in reuters_article.content
    
    # Verify Run tracked
    run = db_session.query(NewsIngestionRun).filter(NewsIngestionRun.run_id == result["run_id"]).first()
    assert run.records_inserted == 2

def test_news_deduplication(db_session, mock_news_provider):
    """Test that duplicate insertions are intercepted and logged."""
    ingestor = NewsIngestor(db_session)
    ingestor.provider = mock_news_provider
    
    # Run once
    ingestor.run_ingestion("Apple", "2023-10-01", "2023-10-02")
    
    # Run again with same mock response
    result2 = ingestor.run_ingestion("Apple", "2023-10-01", "2023-10-02")
    
    assert result2["duplicates"] == 2
    assert result2["records_inserted"] == 0
    
    # Verify DB has duplicate records logged
    dups = db_session.query(NewsArticleDuplicate).all()
    assert len(dups) == 2

def test_news_quality_engine(db_session, mock_news_provider):
    """Test the quality engine catches leaks and missing data."""
    ingestor = NewsIngestor(db_session)
    ingestor.provider = mock_news_provider
    ingestor.run_ingestion("Apple", "2023-10-01", "2023-10-02")
    
    engine = NewsQualityEngine(db_session)
    report = engine.run_quality_check()
    
    # Assuming the mock data is clean
    assert report["status"] == "PASS"
    assert report["issues"]["missing_url"] == 0
    assert report["issues"]["future_timestamps"] == 0
