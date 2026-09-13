"""Pydantic Schemas for Read-Only Device Discovery Engine."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PartitionInfo(BaseModel):
    """Metadata for individual disk partitions."""

    name: str = Field(..., example="sda1")
    device_path: str = Field(..., example="/dev/sda1")
    filesystem: Optional[str] = Field(None, example="ext4")
    size_bytes: int = Field(..., example=53687091200)
    mount_points: List[str] = Field(default_factory=list, example=["/boot"])
    is_swap: bool = Field(False, example=False)
    is_mounted: bool = Field(False, example=True)
    uuid: Optional[str] = Field(None, example="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    label: Optional[str] = Field(None, example="BOOT_PART")


class DiscoveredDevice(BaseModel):
    """Complete metadata inspection payload for a discovered block storage device."""

    device_path: str = Field(..., example="/dev/sda")
    canonical_path: str = Field(..., example="/dev/sda")
    stable_identifier: str = Field(..., example="/dev/disk/by-id/ata-WDC_WD10EZEX-00BN5A0_WD-WCC3F123456")
    model: str = Field(..., example="WDC WD10EZEX-00B")
    vendor: str = Field(..., example="Western Digital")
    size_bytes: int = Field(..., example=1000204886016)
    size_human: str = Field(..., example="931.51 GB")
    is_rotational: bool = Field(..., example=True, description="True for HDD, False for SSD/NVMe")
    transport: str = Field(..., example="sata", description="sata, nvme, usb, scsi")
    filesystem: Optional[str] = Field(None, example="ext4")
    mount_points: List[str] = Field(default_factory=list, example=["/"])
    is_read_only: bool = Field(..., example=False)
    is_removable: bool = Field(..., example=False)
    is_boot_system_disk: bool = Field(..., example=True, description="True if contains root / or /boot mount")
    is_destructible: bool = Field(..., example=False, description="Flagged False for boot/mounted/internal disks")
    risk_score: str = Field(..., example="CRITICAL", description="CRITICAL, HIGH, MEDIUM, LOW")
    risk_reasons: List[str] = Field(default_factory=list, example=["Contains active OS root filesystem"])
    partitions: List[PartitionInfo] = Field(default_factory=list)


class DeviceDiscoveryResponse(BaseModel):
    """Response envelope for system device discovery scan."""

    status: str = Field(..., example="SUPPORTED", description="SUPPORTED, UNSUPPORTED, ERROR")
    platform: str = Field(..., example="linux")
    device_count: int = Field(..., example=2)
    devices: List[DiscoveredDevice] = Field(default_factory=list)
    scan_timestamp: str = Field(..., example="2026-09-13T12:00:00Z")
    message: str = Field(..., example="Device discovery completed successfully.")
