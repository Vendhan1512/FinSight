import pytest
from datetime import date

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_pipeline.validation.validators import MarketValidator, SecValidator, FredValidator

def test_market_validation():
    validator = MarketValidator()
    
    records = [
        # Valid
        {
            "symbol": "AAPL",
            "timestamp": date(2023, 1, 1),
            "open": 100,
            "high": 110,
            "low": 90,
            "close": 105,
            "volume": 1000
        },
        # High < Low
        {
            "symbol": "AAPL",
            "timestamp": date(2023, 1, 2),
            "open": 100,
            "high": 90, # Invalid
            "low": 110, # Invalid
            "close": 105,
            "volume": 1000
        },
        # Negative Volume
        {
            "symbol": "AAPL",
            "timestamp": date(2023, 1, 3),
            "open": 100,
            "high": 110,
            "low": 90,
            "close": 105,
            "volume": -100 # Invalid
        },
        # Missing Field
        {
            "symbol": "AAPL",
            "timestamp": date(2023, 1, 4),
            # open missing
            "high": 110,
            "low": 90,
            "close": 105,
            "volume": 1000
        }
    ]
    
    valid_records = validator.validate(records)
    
    assert len(valid_records) == 1
    assert valid_records[0]["timestamp"] == date(2023, 1, 1)
    
    assert len(validator.results) == 3
    assert validator.results[0].check_name == "high_less_than_low"
    assert validator.results[1].check_name == "negative_volume"
    assert validator.results[2].check_name == "missing_fields"

def test_sec_validation():
    validator = SecValidator()
    
    records = [
        # Valid
        {
            "accession_number": "123",
            "concept": "us-gaap:Revenue",
            "end_date": date(2023, 1, 1),
            "value": 1000
        },
        # Missing end_date (CRITICAL)
        {
            "accession_number": "123",
            "concept": "us-gaap:Revenue",
            # end_date missing
            "value": 1000
        },
        # Null value (WARNING, kept)
        {
            "accession_number": "123",
            "concept": "us-gaap:Revenue",
            "end_date": date(2023, 1, 2),
            "value": None
        }
    ]
    
    valid_records = validator.validate(records)
    
    assert len(valid_records) == 2
    assert validator.results[0].severity == "CRITICAL"
    assert validator.results[1].severity == "WARNING"

def test_fred_validation():
    validator = FredValidator()
    
    records = [
        # Valid
        {
            "series_id": "GDP",
            "observation_date": date(2023, 1, 1),
            "value": 20000
        },
        # Missing value (WARNING, kept)
        {
            "series_id": "GDP",
            "observation_date": date(2023, 1, 2),
            "value": None
        }
    ]
    
    valid_records = validator.validate(records)
    
    assert len(valid_records) == 2
    assert len(validator.results) == 1
    assert validator.results[0].severity == "WARNING"
