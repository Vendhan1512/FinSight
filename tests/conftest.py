import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.main import app
from app.db.session import SessionLocal

@pytest.fixture(scope="session")
def db():
    """
    Returns a database session for testing.
    Since we don't have a test database setup yet, this just uses the standard session for the health check.
    For destructive tests, a separate test database should be configured.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Returns a FastAPI TestClient instance.
    """
    with TestClient(app) as c:
        yield c
