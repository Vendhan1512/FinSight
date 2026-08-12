import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from httpx import Response, TimeoutException

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_pipeline.providers.alpha_vantage import AlphaVantageProvider
from data_pipeline.providers.base import MalformedResponseError, ProviderRateLimitError, ProviderTimeoutError

@pytest.fixture
def provider():
    return AlphaVantageProvider(api_key="test_key")

def test_alpha_vantage_initialization():
    with pytest.raises(ValueError):
        AlphaVantageProvider(api_key="")

@patch("data_pipeline.providers.alpha_vantage.httpx.Client.get")
def test_fetch_daily_success(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.json.return_value = {
        "Meta Data": {},
        "Time Series (Daily)": {
            "2023-10-27": {
                "1. open": "173.05",
                "2. high": "173.05",
                "3. low": "170.65",
                "4. close": "171.21",
                "5. volume": "500000"
            }
        }
    }
    mock_get.return_value = mock_response
    
    data = provider.fetch_daily_ohlcv("AAPL")
    
    assert "raw" in data
    assert "parsed" in data
    assert len(data["parsed"]) == 1
    
    record = data["parsed"][0]
    assert record["symbol"] == "AAPL"
    assert record["open"] == 173.05
    assert record["volume"] == 500000
    assert record["provider"] == "alpha_vantage"
    assert record["source_type"] == "historical"

@patch("data_pipeline.providers.alpha_vantage.httpx.Client.get")
def test_fetch_malformed_response(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.json.return_value = {"Error Message": "Invalid API call"}
    mock_get.return_value = mock_response
    
    with pytest.raises(MalformedResponseError):
        provider.fetch_daily_ohlcv("INVALID")

@patch("data_pipeline.providers.alpha_vantage.httpx.Client.get")
def test_fetch_rate_limit(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.json.return_value = {"Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."}
    mock_get.return_value = mock_response
    
    # We speed up the test by mocking sleep
    with patch("time.sleep"):
        with pytest.raises(ProviderRateLimitError):
            provider.fetch_daily_ohlcv("AAPL")

@patch("data_pipeline.providers.alpha_vantage.httpx.Client.get")
def test_fetch_timeout(mock_get, provider):
    mock_get.side_effect = TimeoutException("Timeout")
    
    with patch("time.sleep"):
        with pytest.raises(ProviderTimeoutError):
            provider.fetch_daily_ohlcv("AAPL")
