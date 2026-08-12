import httpx
import time
from datetime import datetime
from typing import Dict, Any, List
import logging

from .base import (
    BaseProvider,
    ProviderRateLimitError,
    ProviderTimeoutError,
    MalformedResponseError
)

logger = logging.getLogger(__name__)

class FredProvider(BaseProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FRED_API_KEY must be configured.")
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self._name = "fred"
        
        # Free FRED API limit is typically 120 requests per minute
        self.max_retries = 3
        self.retry_delay = 2.0

    @property
    def name(self) -> str:
        return self._name

    def fetch_daily_ohlcv(self, symbol: str) -> Dict[str, Any]:
        """Not applicable for FRED."""
        raise NotImplementedError("FRED provides macroeconomic series, not standard OHLCV.")
        
    def fetch_series_metadata(self, series_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/series"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json"
        }
        return self._get(url, params, f"metadata for {series_id}")

    def fetch_series_observations(self, series_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json"
        }
        
        raw_data = self._get(url, params, f"observations for {series_id}")
        
        if "observations" not in raw_data:
            raise MalformedResponseError(f"Missing 'observations' array in FRED response for {series_id}.")
            
        parsed_records = []
        for obs in raw_data["observations"]:
            try:
                # Handle FRED's missing value indicator "."
                val_str = obs.get("value")
                value = None if val_str == "." else float(val_str)
                
                parsed_records.append({
                    "series_id": series_id,
                    "observation_date": datetime.strptime(obs.get("date"), "%Y-%m-%d").date(),
                    "value": value,
                    "realtime_start": datetime.strptime(obs.get("realtime_start"), "%Y-%m-%d").date(),
                    "realtime_end": datetime.strptime(obs.get("realtime_end"), "%Y-%m-%d").date()
                })
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse FRED observation for {series_id}: {obs}. Error: {e}")
                
        return {
            "raw": raw_data,
            "parsed": parsed_records
        }

    def _get(self, url: str, params: dict, context: str) -> dict:
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(url, params=params)
                    
                    if response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        raise ProviderRateLimitError(f"HTTP 429 Rate limit exceeded from FRED for {context}.")
                        
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.TimeoutException as e:
                logger.error(f"Timeout connecting to FRED for {context}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise ProviderTimeoutError(f"Timeout connecting to FRED: {str(e)}")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400 and "Bad Request" in e.response.text:
                    raise MalformedResponseError(f"FRED API error for {context}: {e.response.text}")
                raise ProviderError(f"HTTP Error from FRED: {e.response.status_code} - {e.response.text}")
                
        raise ProviderError(f"Max retries exceeded for {context}")
