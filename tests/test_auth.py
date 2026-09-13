"""Security Tests for Authentication, Password Verification, and Token Expiration."""

from datetime import timedelta
from app.core.security import create_access_token


def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Administrator"
    assert "case:create" in data["permissions"]


def test_login_invalid_password_failure(client):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "WrongPassword!"})
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert "Invalid username or password" in data["error"]["message"]


def test_expired_token_rejection(client):
    # Create an expired token (expired 10 seconds ago)
    expired_token = create_access_token(
        subject="admin",
        expires_delta=timedelta(seconds=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "INVALID_TOKEN"
    assert "expired" in data["error"]["message"].lower()


def test_malformed_token_rejection(client):
    headers = {"Authorization": "Bearer malformed.invalid.token"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_get_user_profile(client, investigator_headers):
    res = client.get("/api/v1/auth/me", headers=investigator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "investigator1"
    assert data["role"] == "Investigator"
