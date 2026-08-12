from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ProviderError(Exception):
    """Base exception for provider errors."""
    pass

class ProviderRateLimitError(ProviderError):
    """Raised when the provider's rate limit is exceeded."""
    pass

class ProviderTimeoutError(ProviderError):
    """Raised when the provider request times out."""
    pass

class MalformedResponseError(ProviderError):
    """Raised when the provider returns unexpected or malformed data."""
    pass

class BaseProvider(ABC):
    """
    Abstract base class for market data providers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g., 'alpha_vantage')."""
        pass
        
    @abstractmethod
    def fetch_daily_ohlcv(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch daily OHLCV data for a given symbol.
        Should return a dictionary containing both the raw payload and a list of parsed records.
        """
        pass
