"""Unit tests verifying SAFE_MODE security enforcement."""

def test_safe_mode_simulation_success(client):
    payload = {
        "target_path": "/evidence/test_image.raw",
        "operation_type": "SECURE_WIPE_SIMULATION",
        "simulate": True
    }
    response = client.post("/api/v1/forensic/simulate-operation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SIMULATED"
    assert data["safe_mode_active"] is True
    assert "DRY RUN PREVIEW" in data["preview"]


def test_safe_mode_rejection_on_destructive_without_simulation(client):
    payload = {
        "target_path": "/evidence/test_image.raw",
        "operation_type": "SECURE_WIPE_UNPROTECTED",
        "simulate": False
    }
    response = client.post("/api/v1/forensic/simulate-operation", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SAFE_MODE_BLOCKED"
    assert "SAFE_MODE" in data["error"]["message"]
