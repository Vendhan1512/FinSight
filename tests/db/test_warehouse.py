import pytest
from datetime import datetime, date
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.app.models.warehouse import DataSource, MarketAsset, MarketPrice
from backend.app.crud import crud_warehouse

# Note: These tests require a test database to run. 
# They are structured as unit tests but test the DB schema configuration.

def test_data_source_creation(db):
    # This assumes `db` fixture provides a SQLAlchemy session (from conftest.py)
    # If the DB is down, this test will error during fixture setup.
    source = crud_warehouse.data_source.get_or_create(db, id="test_source", name="Test", provider="test")
    assert source.id == "test_source"
    assert source.name == "Test"

def test_market_price_idempotency(db):
    # This verifies the UPSERT constraint logic works.
    
    # 1. Setup Data Source and Asset
    crud_warehouse.data_source.get_or_create(db, id="test_src", name="Test", provider="test")
    
    # Normally we'd use a CRUD for MarketAsset, but we do it manually for the test
    from sqlalchemy.dialects.postgresql import insert
    db.execute(insert(MarketAsset).values(symbol="TEST_SYM", asset_type="equity", name="Test Co").on_conflict_do_nothing())
    db.commit()

    # 2. Insert Price
    records = [{
        "symbol": "TEST_SYM",
        "timestamp": datetime(2023, 1, 1),
        "open": 100.0,
        "high": 105.0,
        "low": 95.0,
        "close": 100.0,
        "volume": 1000,
        "source_id": "test_src"
    }]
    crud_warehouse.market_price.batch_upsert(db, records)
    
    # 3. Upsert Price (Same constraints, different close)
    records_updated = [{
        "symbol": "TEST_SYM",
        "timestamp": datetime(2023, 1, 1),
        "open": 100.0,
        "high": 105.0,
        "low": 95.0,
        "close": 102.0, # Updated
        "volume": 1500, # Updated
        "source_id": "test_src"
    }]
    crud_warehouse.market_price.batch_upsert(db, records_updated)
    
    # 4. Verify
    prices = db.query(MarketPrice).filter(MarketPrice.symbol == "TEST_SYM").all()
    assert len(prices) == 1
    assert prices[0].close == 102.0
    assert prices[0].volume == 1500
