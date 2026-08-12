import httpx
import time
from datetime import datetime
from typing import Dict, Any
import logging

from .base import (
    BaseProvider,
    ProviderRateLimitError,
    ProviderTimeoutError,
    MalformedResponseError
)

logger = logging.getLogger(__name__)

class AlphaVantageProvider(BaseProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Alpha Vantage API key must be configured.")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self._name = "alpha_vantage"
        
        # Free tier is 25 req/day and 5 req/min
        self.max_retries = 3
        self.retry_delay = 5.0 # seconds

    @property
    def name(self) -> str:
        return self._name

    def fetch_daily_ohlcv(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches TIME_SERIES_DAILY from Alpha Vantage.
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "compact" # returns only the last 100 data points
        }
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(self.base_url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Alpha Vantage rate limits usually return a 200 OK but with an "Information" key
                    if "Information" in data and "rate limit" in data["Information"].lower():
                        logger.warning(f"Rate limit hit for {symbol}. Attempt {attempt + 1}/{self.max_retries}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        raise ProviderRateLimitError(f"Rate limit exceeded from {self.name}: {data['Information']}")
                        
                    if "Error Message" in data:
                        raise MalformedResponseError(f"Provider Error: {data['Error Message']}")
                        
                    if "Time Series (Daily)" not in data:
                        raise MalformedResponseError(f"Unexpected JSON structure from {self.name}. Missing 'Time Series (Daily)'. Raw: {data}")
                        
                    # Successfully parsed, return raw data
                    return {
                        "raw": data,
                        "parsed": self._parse_daily(symbol, data)
                    }
                    
            except httpx.TimeoutException as e:
                logger.error(f"Timeout connecting to {self.name}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise ProviderTimeoutError(f"Timeout connecting to {self.name}: {str(e)}")
                
            except httpx.HTTPStatusError as e:
                # E.g., 429 Too Many Requests
                if e.response.status_code == 429:
                     if attempt < self.max_retries - 1:
                         time.sleep(self.retry_delay)
                         continue
                     raise ProviderRateLimitError(f"HTTP 429 Rate limit exceeded from {self.name}.")
                raise ProviderError(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                
        raise ProviderError(f"Max retries exceeded for {symbol}")
        
    def _parse_daily(self, symbol: str, raw_data: dict) -> list:
        parsed = []
        time_series = raw_data.get("Time Series (Daily)", {})
        # Note: Alpha Vantage daily is end-of-day (historical), not realtime.
        for date_str, values in time_series.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                parsed.append({
                    "symbol": symbol,
                    "timestamp": dt,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                    "source_type": "historical", # Alpha vantage daily is historical EOD
                    "provider": self.name,
                    "endpoint": "TIME_SERIES_DAILY"
                })
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to parse row for {date_str}: {e}")
                raise MalformedResponseError(f"Failed to parse row for {date_str}: {e}")
        return parsed
