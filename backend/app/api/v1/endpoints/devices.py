"""Read-Only Device Discovery API Endpoint for ForensicShield."""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Request, Query
from app.core.logging import audit_log
from app.core.dependencies import get_current_user, require_roles
from app.models.auth import User
from app.schemas.device import DeviceDiscoveryResponse
from app.services.device_discovery import DeviceDiscoveryService

router = APIRouter()

# Default Simulated Mock Devices for Windows/macOS/Development/Demo Environments
SIMULATED_DEVICES: List[Dict] = [
    {
        "device_path": "/dev/sda",
        "device_type": "HDD",
        "size_bytes": 1000204886016,
        "vendor": "Western Digital",
        "model": "WDC WD10EZEX-00B",
        "serial_number": "WD-WCC3F123456",
        "is_system_disk": True,
        "is_mounted": True,
        "bus_type": "SATA",
        "mount_point": "/",
        "recommended_method": "NIST 800-88 Clear (3-Pass Overwrite)",
        "confidence_level": "HIGH",
        "in_allowlist": False,
    },
    {
        "device_path": "/dev/sdb",
        "device_type": "SSD",
        "size_bytes": 512110190592,
        "vendor": "Samsung",
        "model": "SSD 870 EVO 500GB",
        "serial_number": "SAMSUNG-SSD-980-TEST-01",
        "is_system_disk": False,
        "is_mounted": False,
        "bus_type": "SATA",
        "mount_point": "",
        "recommended_method": "NIST 800-88 Purge (Cryptographic Erase)",
        "confidence_level": "HIGH",
        "in_allowlist": True,
    },
    {
        "device_path": "/dev/sdc",
        "device_type": "USB",
        "size_bytes": 32212254720,
        "vendor": "SanDisk",
        "model": "Ultra USB 3.0 32GB",
        "serial_number": "TEST-LAB-SERIAL-9999",
        "is_system_disk": False,
        "is_mounted": False,
        "bus_type": "USB",
        "mount_point": "",
        "recommended_method": "Single-Pass Zero Overwrite",
        "confidence_level": "HIGH",
        "in_allowlist": True,
    },
]


def _format_device_info(dev) -> Dict:
    """Formats DiscoveredDevice into DeviceInfo format."""
    d_type = "USB" if dev.transport == "usb" else ("HDD" if dev.is_rotational else ("NVMe" if dev.transport == "nvme" else "SSD"))
    rec_method = "NIST 800-88 Purge (NVMe Sanitize)" if d_type == "NVMe" else ("NIST 800-88 Clear" if d_type == "HDD" else "NIST 800-88 Block Erase")
    return {
        "device_path": dev.device_path,
        "device_type": d_type,
        "size_bytes": dev.size_bytes,
        "vendor": dev.vendor or "Generic Vendor",
        "model": dev.model or "Storage Device",
        "serial_number": dev.stable_identifier.split("/")[-1] if dev.stable_identifier else "GENERIC-SERIAL",
        "is_system_disk": dev.is_boot_system_disk,
        "is_mounted": len(dev.mount_points) > 0,
        "bus_type": dev.transport.upper(),
        "mount_point": dev.mount_points[0] if dev.mount_points else "",
        "recommended_method": rec_method,
        "confidence_level": "HIGH",
        "in_allowlist": True,
    }


@router.get("/scan", response_model=List[Dict])
@router.get("/list", response_model=List[Dict])
async def scan_devices(
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator", "Viewer"])),
):
    """
    Scans local storage devices. Returns list of DeviceInfo objects.
    Provides simulated fallback devices when running on Windows/macOS or in SAFE_MODE simulation.
    """
    discovery_service = DeviceDiscoveryService()
    res = discovery_service.discover_devices()

    if res.devices and len(res.devices) > 0:
        return [_format_device_info(d) for d in res.devices]

    return SIMULATED_DEVICES


@router.get("/discover", response_model=DeviceDiscoveryResponse)
async def discover_devices(
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator", "Viewer"])),
):
    """
    Scans local block storage devices using non-destructive, read-only system tools (lsblk -J).
    Returns complete device metadata, mount status, boot disk indicators, and risk evaluation scores.
    """
    request_id = getattr(request.state, "request_id", "N/A")
    discovery_service = DeviceDiscoveryService()
    result = discovery_service.discover_devices()

    audit_log(
        message=f"Device discovery scan executed by '{current_user.username}' (Status: '{result.status}', Discovered: {result.device_count} devices).",
        operation="DEVICE_DISCOVERY_SCAN",
        status=result.status,
        request_id=request_id,
        user_id=current_user.username,
        extra_payload={
            "device_count": result.device_count,
            "platform": result.platform,
        },
    )

    return result


@router.get("/details", response_model=Dict)
async def get_device_details(
    device_path: str = Query(..., example="/dev/sdb"),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator", "Viewer"])),
):
    """Returns detailed DeviceInfo object for a given device path."""
    discovery_service = DeviceDiscoveryService()
    res = discovery_service.discover_devices()

    if res.devices:
        target = next((d for d in res.devices if d.device_path == device_path), None)
        if target:
            return _format_device_info(target)

    target_sim = next((d for d in SIMULATED_DEVICES if d["device_path"] == device_path), SIMULATED_DEVICES[1])
    return target_sim
