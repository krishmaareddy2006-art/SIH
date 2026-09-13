"""Pytest Fixtures & Security Authentication Helpers."""

import os
import sys
from pathlib import Path

# Insert backend directory into sys.path to enable app module imports
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.init_db import init_db

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_forensic_shield_sec.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)
    db.close()

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_forensic_shield_sec.db"):
        try:
            os.remove("./test_forensic_shield_sec.db")
        except PermissionError:
            pass



def get_auth_token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(client):
    token = get_auth_token(client, "admin", "AdminPass123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def investigator_headers(client):
    token = get_auth_token(client, "investigator1", "InvestigatorPass123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def operator_headers(client):
    token = get_auth_token(client, "operator1", "OperatorPass123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client):
    token = get_auth_token(client, "viewer1", "ViewerPass123!")
    return {"Authorization": f"Bearer {token}"}
