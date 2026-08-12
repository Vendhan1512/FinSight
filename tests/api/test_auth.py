import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base_class import Base
from app.api import deps
from app.models.auth import User
from app.core import security

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to create tables
from app.models import auth, intelligence, orchestration

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[deps.get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_users():
    db = TestingSessionLocal()
    
    admin = User(username="admin", hashed_password=security.get_password_hash("admin123"), role="ADMIN")
    analyst = User(username="analyst", hashed_password=security.get_password_hash("analyst123"), role="ANALYST")
    viewer = User(username="viewer", hashed_password=security.get_password_hash("viewer123"), role="VIEWER")
    
    db.add_all([admin, analyst, viewer])
    db.commit()
    db.close()
    yield
    # No teardown needed for in-memory

def test_login_success(setup_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure(setup_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 400

def test_protected_route_without_token():
    # Trying to trigger system pipeline without a token
    response = client.post("/api/v1/system/pipeline/trigger")
    assert response.status_code == 401

def test_rbac_analyst_cannot_trigger_pipeline(setup_users):
    # Analyst token
    res = client.post("/api/v1/auth/login", data={"username": "analyst", "password": "analyst123"})
    token = res.json()["access_token"]
    
    response = client.post(
        "/api/v1/system/pipeline/trigger",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
