import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from httpx import Response

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_pipeline.providers.fred import FredProvider
from data_pipeline.providers.base import MalformedResponseError

@pytest.fixture
def provider():
    return FredProvider(api_key="test_key")

def test_provider_initialization():
    with pytest.raises(ValueError):
        FredProvider(api_key="")

@patch("data_pipeline.providers.fred.httpx.Client.get")
def test_fetch_series_metadata(mock_get, provider):
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "seriess": [
            {
                "id": "FEDFUNDS",
                "title": "Effective Federal Funds Rate",
                "frequency_short": "M",
                "units_short": "%"
            }
        ]
    }
    mock_get.return_value = mock_response
    
    data = provider.fetch_series_metadata("FEDFUNDS")
    assert "seriess" in data
    assert data["seriess"][0]["id"] == "FEDFUNDS"

@patch("data_pipeline.providers.fred.httpx.Client.get")
def test_fetch_series_observations_missing_data(mock_get, provider):
    # Test that "." is parsed as None
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "observations": [
            {
                "realtime_start": "2023-01-01",
                "realtime_end": "2023-01-01",
                "date": "1999-01-01",
                "value": "."
            },
            {
                "realtime_start": "2023-01-01",
                "realtime_end": "2023-01-01",
                "date": "1999-02-01",
                "value": "5.33"
            }
        ]
    }
    mock_get.return_value = mock_response
    
    data = provider.fetch_series_observations("FEDFUNDS")
    parsed = data["parsed"]
    
    assert len(parsed) == 2
    
    obs_missing = parsed[0]
    assert obs_missing["date"] == "1999-01-01" # Note: date object assert later, here we just check key names wait it parsed to python date
    assert obs_missing["value"] is None
    
    obs_valid = parsed[1]
    assert obs_valid["value"] == 5.33
