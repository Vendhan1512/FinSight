import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from httpx import Response

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_pipeline.providers.sec_edgar import SecEdgarProvider
from data_pipeline.providers.base import ProviderRateLimitError

@pytest.fixture
def provider():
    return SecEdgarProvider(user_agent="TestAgent/1.0 (test@example.com)")

def test_provider_initialization():
    with pytest.raises(ValueError):
        SecEdgarProvider(user_agent="")

@patch("data_pipeline.providers.sec_edgar.httpx.Client.get")
def test_fetch_company_facts_success(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "cik": 320193,
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "end": "2023-09-30",
                                "val": 383285000000,
                                "accn": "0000320193-23-000106",
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2023-11-03"
                            }
                        ]
                    }
                },
                "UnmappedConceptThatShouldBeSkipped": {
                    "units": {
                        "USD": [{"end": "2023-09-30", "val": 100}]
                    }
                }
            }
        }
    }
    mock_get.return_value = mock_response
    
    with patch("time.sleep"):  # Mock rate limit sleep
        data = provider.fetch_company_facts("320193")
        
    assert "raw" in data
    assert "parsed" in data
    
    parsed = data["parsed"]
    assert parsed["unmapped_count"] == 1
    assert "us-gaap:UnmappedConceptThatShouldBeSkipped" in parsed["unmapped_concepts"]
    
    mapped_facts = parsed["mapped_facts"]
    assert len(mapped_facts) == 1
    
    fact = mapped_facts[0]
    assert fact["cik"] == "0000320193"
    assert fact["concept"] == "us-gaap:Revenues"
    assert fact["metric"] == "Revenue"
    assert fact["value"] == 383285000000
    assert fact["end_date"] == date(2023, 9, 30)
    assert fact["fiscal_year"] == 2023
    assert fact["fiscal_period"] == "FY"
    assert fact["accession_number"] == "0000320193-23-000106"

@patch("data_pipeline.providers.sec_edgar.httpx.Client.get")
def test_fetch_company_facts_rate_limit(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 429
    mock_get.return_value = mock_response
    
    with patch("time.sleep"):
        with pytest.raises(ProviderRateLimitError):
            provider.fetch_company_facts("320193")
