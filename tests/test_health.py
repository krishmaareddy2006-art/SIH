"""Unit tests for System Health and Security Flags Endpoint."""

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "ForensicShield"
    assert data["status"] == "HEALTHY"
    assert data["safe_mode"] is True
    assert data["real_device_operations"] is False
    assert "X-Request-ID" in response.headers
