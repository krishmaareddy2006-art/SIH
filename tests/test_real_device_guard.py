"""Unit tests verifying REAL_DEVICE_OPERATIONS feature flag enforcement."""

def test_real_device_operation_blocked(client):
    response = client.post("/api/v1/forensic/scan-hardware-device?device_path=\\\\.\\PhysicalDrive0")
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REAL_DEVICE_OPS_DISABLED"
    assert "REAL_DEVICE_OPERATIONS" in data["error"]["message"]
