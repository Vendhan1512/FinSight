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
from ..mappings.sec_xbrl import map_concept

logger = logging.getLogger(__name__)

class SecEdgarProvider(BaseProvider):
    def __init__(self, user_agent: str):
        if not user_agent or user_agent == "FinSight/1.0 (developer@example.com)":
             # We allow the default for testing but strictly we should have a real one.
             # We just check it's not completely empty
            if not user_agent:
                raise ValueError("SEC_USER_AGENT must be configured for polite API access.")
            
        self.user_agent = user_agent
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK"
        self._name = "sec_edgar"
        
        # SEC rate limit: strictly no more than 10 requests per second.
        self.rate_limit_delay = 0.15 # 150ms between requests ensures < 10 req/s

    @property
    def name(self) -> str:
        return self._name

    def fetch_company_facts(self, cik: str) -> Dict[str, Any]:
        """
        Fetches all XBRL facts for a given CIK from SEC EDGAR.
        CIK must be exactly 10 digits (e.g. '0000320193' for AAPL).
        """
        # Ensure 10-digit CIK
        cik_10 = str(cik).zfill(10)
        url = f"{self.base_url}{cik_10}.json"
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }
        
        # Enforce rate limit delay before request
        time.sleep(self.rate_limit_delay)
        
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, headers=headers)
                
                if response.status_code == 429:
                    raise ProviderRateLimitError(f"HTTP 429 Rate limit exceeded from SEC EDGAR for CIK {cik_10}.")
                    
                response.raise_for_status()
                data = response.json()
                
                if "facts" not in data:
                    raise MalformedResponseError(f"Unexpected JSON from SEC. Missing 'facts'. Raw: {str(data)[:200]}")
                    
                return {
                    "raw": data,
                    "parsed": self._parse_facts(cik_10, data)
                }
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to SEC EDGAR for CIK {cik_10}: {str(e)}")
            raise ProviderTimeoutError(f"Timeout connecting to SEC EDGAR: {str(e)}")
            
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"HTTP Error from SEC EDGAR: {e.response.status_code} - {e.response.text}")
            
    def _parse_facts(self, cik: str, raw_data: dict) -> Dict[str, List[dict]]:
        """
        Parses raw SEC facts into a list of normalized dictionary records.
        """
        parsed_records = []
        unmapped_concepts = set()
        
        facts = raw_data.get("facts", {})
        
        # We focus on us-gaap taxonomy for now
        us_gaap = facts.get("us-gaap", {})
        
        for concept_name, concept_data in us_gaap.items():
            metric_name = map_concept(f"us-gaap:{concept_name}")
            
            if metric_name == "Unknown":
                unmapped_concepts.add(f"us-gaap:{concept_name}")
                continue # Skip unmapped for now, but could ingest them if needed
                
            units = concept_data.get("units", {})
            for unit_name, unit_facts in units.items():
                for fact in unit_facts:
                    try:
                        # Convert string dates to python dates
                        end_date_str = fact.get("end")
                        start_date_str = fact.get("start")
                        
                        if not end_date_str:
                            continue # Skip invalid facts without end date
                            
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
                        
                        parsed_records.append({
                            "cik": cik,
                            "concept": f"us-gaap:{concept_name}",
                            "taxonomy": "us-gaap",
                            "metric": metric_name,
                            "unit": unit_name,
                            "value": float(fact.get("val", 0)),
                            "start_date": start_date,
                            "end_date": end_date,
                            "fiscal_period": fact.get("fp"),
                            "fiscal_year": int(fact.get("fy")) if fact.get("fy") else None,
                            "accession_number": fact.get("accn")
                        })
                    except (KeyError, ValueError, TypeError) as e:
                        # Log but don't fail entire ingestion for a single bad fact
                        logger.debug(f"Failed to parse SEC fact {concept_name} for {cik}: {e}")
                        
        return {
            "mapped_facts": parsed_records,
            "unmapped_count": len(unmapped_concepts),
            "unmapped_concepts": list(unmapped_concepts)[:10] # Return a sample for logging
        }

    def fetch_daily_ohlcv(self, symbol: str) -> Dict[str, Any]:
        """Not implemented for SEC. SEC provides fundamental facts, not OHLCV."""
        raise NotImplementedError("SEC EDGAR provides fundamental data, not OHLCV.")
