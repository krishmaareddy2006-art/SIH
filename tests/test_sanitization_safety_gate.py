"""System Disk Protection Test Suite for Sanitization Safety Gate & Orchestrator."""

from unittest.mock import patch, MagicMock
import pytest

from app.core.config import settings
from app.core.exceptions import ForensicShieldException
from app.services.sanitization_safety_gate import SanitizationSafetyGate


def test_non_admin_rejected_by_preflight(client, investigator_headers):
    # Attempting preflight with Investigator headers -> 403 Forbidden
    res = client.post(
        "/api/v1/sanitization/preflight",
        json={"device_path": "/dev/sdb", "case_id": 1},
        headers=investigator_headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


def test_system_boot_disk_rejected_by_safety_gate(client, admin_headers):
    # Create mock discovery response where /dev/sda is root boot disk
    mock_dev_sda = MagicMock()
    mock_dev_sda.canonical_path = "/dev/sda"
    mock_dev_sda.is_boot_system_disk = True
    mock_dev_sda.mount_points = ["/"]
    mock_dev_sda.partitions = []

    mock_discovery = MagicMock()
    mock_discovery.devices = [mock_dev_sda]

    with patch("app.services.device_discovery.DeviceDiscoveryService.discover_devices", return_value=mock_discovery):
        res = client.post(
            "/api/v1/sanitization/preflight",
            json={"device_path": "/dev/sda", "case_id": 1},
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["safety_gate_passed"] is False
        assert any("boot/root" in r for r in data["safety_gate_reasons"])


def test_mounted_partition_rejected_by_safety_gate(client, admin_headers):
    mock_dev_sdb = MagicMock()
    mock_dev_sdb.canonical_path = "/dev/sdb"
    mock_dev_sdb.is_boot_system_disk = False
    mock_dev_sdb.mount_points = ["/mnt/data"]
    mock_dev_sdb.partitions = []

    mock_discovery = MagicMock()
    mock_discovery.devices = [mock_dev_sdb]

    with patch("app.services.device_discovery.DeviceDiscoveryService.discover_devices", return_value=mock_discovery):
        res = client.post(
            "/api/v1/sanitization/preflight",
            json={"device_path": "/dev/sdb", "case_id": 1},
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["safety_gate_passed"] is False
        assert any("mounted partitions" in r for r in data["safety_gate_reasons"])


def test_invalid_confirmation_token_rejected_on_execute(client, admin_headers):
    # Attempt execution with invalid token string
    res = client.post(
        "/api/v1/sanitization/execute",
        json={
            "device_path": "/dev/sdb",
            "case_id": 1,
            "confirmation_token": "CONFIRM:/dev/sdb:1:INVALIDTOKEN",
            "reason": "Testing invalid token rejection",
            "simulate": True,
        },
        headers=admin_headers,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_CONFIRMATION_TOKEN"


def test_physical_test_lab_allowlist_enforcement():
    # Verify allowlist check raises exception for non-allowlisted devices when REAL_DEVICE_OPERATIONS=True
    with patch.object(settings, "REAL_DEVICE_OPERATIONS", True):
        with pytest.raises(ForensicShieldException) as exc_info:
            SanitizationSafetyGate.verify_physical_test_lab_allowlist(
                stable_identifier="/dev/disk/by-id/ata-UNAUTHORIZED_DRIVE_12345",
                serial_number="UNAUTHORIZED_SERIAL",
            )
        assert exc_info.value.code == "TEST_LAB_ALLOWLIST_DENIED"


def test_successful_simulated_sanitization_flow(client, admin_headers):
    # 1. Generate token
    token_res = client.post(
        "/api/v1/sanitization/token",
        json={"device_path": "/dev/sdb", "case_id": 1},
        headers=admin_headers,
    )
    assert token_res.status_code == 200
    req_token_str = token_res.json()["required_confirmation_string"]

    # 2. Execute simulated sanitization
    mock_dev_sdb = MagicMock()
    mock_dev_sdb.canonical_path = "/dev/sdb"
    mock_dev_sdb.is_boot_system_disk = False
    mock_dev_sdb.mount_points = []
    mock_dev_sdb.partitions = []
    mock_dev_sdb.transport = "usb"
    mock_dev_sdb.is_rotational = False
    mock_dev_sdb.model = "Ultra USB 3.0"
    mock_dev_sdb.vendor = "SanDisk"
    mock_dev_sdb.size_bytes = 32000000000
    mock_dev_sdb.stable_identifier = "/dev/disk/by-id/usb-SanDisk_Ultra_USB_3.0"

    mock_discovery = MagicMock()
    mock_discovery.devices = [mock_dev_sdb]

    with patch("app.services.device_discovery.DeviceDiscoveryService.discover_devices", return_value=mock_discovery):
        exec_res = client.post(
            "/api/v1/sanitization/execute",
            json={
                "device_path": "/dev/sdb",
                "case_id": 1,
                "confirmation_token": req_token_str,
                "reason": "Authorized test-lab USB sanitization dry-run",
                "simulate": True,
            },
            headers=admin_headers,
        )
        assert exec_res.status_code == 200
        report = exec_res.json()
        assert report["status"] == "SIMULATED"
        assert report["job_id"].startswith("san-")
        assert len(report["execution_steps"]) == 5
        assert all(step["status"] == "SIMULATED" for step in report["execution_steps"])
