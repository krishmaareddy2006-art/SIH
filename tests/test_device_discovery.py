"""Unit Tests for Read-Only Device Discovery Service, Path Validator, and Risk Engine."""

import json
import subprocess
from unittest.mock import patch, MagicMock

from app.services.device_discovery import (
    DeviceDiscoveryService,
    DevicePathValidator,
    DeviceRiskEvaluator,
)

# Mocked lsblk JSON payload
MOCK_LSBLK_JSON = {
    "blockdevices": [
        {
            "name": "sda",
            "path": "/dev/sda",
            "type": "disk",
            "size": 1000204886016,
            "rota": True,
            "rm": False,
            "hotplug": False,
            "tran": "sata",
            "model": "WDC WD10EZEX-00B",
            "vendor": "Western Digital",
            "ro": False,
            "children": [
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "type": "part",
                    "size": 53687091200,
                    "fstype": "ext4",
                    "mountpoints": ["/"],
                    "uuid": "uuid-root-sda1",
                    "label": "OS_ROOT",
                }
            ],
        },
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "type": "disk",
            "size": 32000000000,
            "rota": False,
            "rm": True,
            "hotplug": True,
            "tran": "usb",
            "model": "Ultra USB 3.0",
            "vendor": "SanDisk",
            "ro": False,
            "children": [
                {
                    "name": "sdb1",
                    "path": "/dev/sdb1",
                    "type": "part",
                    "size": 32000000000,
                    "fstype": "exfat",
                    "mountpoints": [None],
                    "uuid": "uuid-usb-sdb1",
                    "label": "EVIDENCE_USB",
                }
            ],
        },
        {
            "name": "nvme0n1",
            "path": "/dev/nvme0n1",
            "type": "disk",
            "size": 512110190592,
            "rota": False,
            "rm": False,
            "hotplug": False,
            "tran": "nvme",
            "model": "Samsung SSD 980 500GB",
            "vendor": "Samsung",
            "ro": False,
            "children": [
                {
                    "name": "nvme0n1p1",
                    "path": "/dev/nvme0n1p1",
                    "type": "part",
                    "size": 16000000000,
                    "fstype": "swap",
                    "mountpoints": ["[SWAP]"],
                    "uuid": "uuid-swap-nvme",
                    "label": "SWAP_PART",
                }
            ],
        },
    ]
}


def test_device_path_validator():
    # Valid allowed paths
    assert DevicePathValidator.validate_and_canonicalize("/dev/sda") == "/dev/sda"
    assert DevicePathValidator.validate_and_canonicalize("/dev/nvme0n1") == "/dev/nvme0n1"
    assert DevicePathValidator.validate_and_canonicalize("/dev/sdb1") == "/dev/sdb1"

    # Invalid / Malicious paths (Path Traversal / Command Injection)
    assert DevicePathValidator.validate_and_canonicalize("/dev/../etc/passwd") is None
    assert DevicePathValidator.validate_and_canonicalize("/dev/sda; rm -rf /") is None
    assert DevicePathValidator.validate_and_canonicalize("/etc/shadow") is None
    assert DevicePathValidator.validate_and_canonicalize("") is None
    assert DevicePathValidator.validate_and_canonicalize(None) is None


def test_non_linux_platform_returns_unsupported():
    service = DeviceDiscoveryService(platform_override="win32")
    res = service.discover_devices()
    assert res.status == "UNSUPPORTED"
    assert res.device_count == 0
    assert "supported only on Linux" in res.message


def test_successful_lsblk_mock_parsing():
    service = DeviceDiscoveryService(platform_override="linux")

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(MOCK_LSBLK_JSON)
    mock_process.stderr = ""

    with patch("subprocess.run", return_value=mock_process):
        res = service.discover_devices()

    assert res.status == "SUPPORTED"
    assert res.device_count == 3

    dev_sda = next(d for d in res.devices if d.device_path == "/dev/sda")
    assert dev_sda.is_boot_system_disk is True
    assert dev_sda.risk_score == "CRITICAL"
    assert dev_sda.is_destructible is False

    dev_sdb = next(d for d in res.devices if d.device_path == "/dev/sdb")
    assert dev_sdb.is_removable is True
    assert dev_sdb.risk_score == "LOW"
    assert dev_sdb.is_destructible is True

    dev_nvme = next(d for d in res.devices if d.device_path == "/dev/nvme0n1")
    assert dev_nvme.risk_score == "HIGH"
    assert dev_nvme.is_destructible is False


def test_malformed_json_handling():
    service = DeviceDiscoveryService(platform_override="linux")

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "INVALID_JSON_RESPONSE{{{"
    mock_process.stderr = ""

    with patch("subprocess.run", return_value=mock_process):
        res = service.discover_devices()

    assert res.status == "ERROR"
    assert "Failed to parse lsblk JSON" in res.message


def test_missing_lsblk_binary_handling():
    service = DeviceDiscoveryService(platform_override="linux")

    with patch("subprocess.run", side_effect=FileNotFoundError):
        res = service.discover_devices()

    assert res.status == "ERROR"
    assert "command 'lsblk' not found" in res.message


def test_subprocess_timeout_handling():
    service = DeviceDiscoveryService(platform_override="linux")

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="lsblk", timeout=5),
    ):
        res = service.discover_devices()

    assert res.status == "ERROR"
    assert "scan timed out" in res.message


def test_device_discovery_api_endpoint(client, investigator_headers):
    res = client.get("/api/v1/devices/discover", headers=investigator_headers)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "devices" in data
