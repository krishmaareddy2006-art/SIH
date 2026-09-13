"""Pydantic Schemas for Safe Storage Sanitization Orchestration Layer."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SanitizationTokenRequest(BaseModel):
    """Payload to request a unique confirmation token for drive sanitization."""

    device_path: str = Field(..., example="/dev/sdb")
    case_id: int = Field(..., example=1)
    serial_number: Optional[str] = Field(None, example="WD-WCC3F123456")


class SanitizationTokenResponse(BaseModel):
    """Confirmation token response envelope."""

    device_path: str
    case_id: int
    confirmation_token: str
    required_confirmation_string: str = Field(..., example="CONFIRM:/dev/sdb:1:a1b2c3d4")
    expires_in_seconds: int = 900


class SanitizationPreflightRequest(BaseModel):
    """Payload to request a sanitization preflight inspection report."""

    device_path: str = Field(..., example="/dev/sdb")
    case_id: int = Field(..., example=1)


class SanitizationPreflightReport(BaseModel):
    """Preflight inspection report payload detailing safety gate results, classification, and dry-run plan."""

    device_path: str
    canonical_path: str
    stable_identifier: str
    target_class: str = Field(..., example="SSD", description="HDD, SSD, NVME, USB_FLASH, VIRTUAL_DISK, UNKNOWN")
    model: str
    vendor: str
    size_bytes: int
    recommended_method: str = Field(..., example="ATA_SECURE_ERASE", description="Recommended sanitization procedure")
    confidence_level: str = Field(..., example="HIGH", description="HIGH, MEDIUM, LOW")
    alternative_methods: List[str] = Field(default_factory=list)
    ftl_caveats: str
    is_boot_system_disk: bool
    is_mounted: bool
    safety_gate_passed: bool
    safety_gate_reasons: List[str] = Field(default_factory=list)
    planned_steps: List[str] = Field(default_factory=list)


class SanitizationExecuteRequest(BaseModel):
    """Payload to execute safe sanitization orchestration pipeline."""

    device_path: str = Field(..., example="/dev/sdb")
    case_id: int = Field(..., example=1)
    confirmation_token: str = Field(..., example="CONFIRM:/dev/sdb:1:a1b2c3d4")
    reason: str = Field(..., min_length=5, example="Authorized evidence drive sanitization dry-run")
    chosen_method: Optional[str] = Field(None, example="ATA_SECURE_ERASE")
    simulate: bool = Field(True, description="Enforce dry-run simulation mode")


class SanitizationStepResult(BaseModel):
    """Step result entry in sanitization execution report."""

    step_number: int
    step_name: str
    status: str = Field(..., example="COMPLETED")
    progress_percentage: float = Field(..., example=100.0)
    message: str
    timestamp: str


class SanitizationResultReport(BaseModel):
    """Execution audit report for storage sanitization operation."""

    job_id: str
    device_path: str
    case_id: int
    target_class: str
    method_used: str
    confidence_level: str
    status: str = Field(
        ...,
        example="SIMULATED",
        description="SIMULATED, COMPLETED_VERIFIED, COMPLETED_INCONCLUSIVE, FAILED, UNSUPPORTED, ABORTED, MANUAL_REVIEW",
    )
    safe_mode_active: bool
    execution_steps: List[SanitizationStepResult] = Field(default_factory=list)
    postflight_sample_verified: bool = Field(False)
    execution_time_ms: float
    disclaimer: str = Field(
        "PHYSICAL SANITIZATION DISCLAIMER: Real hardware commands (NVMe Format, ATA Secure Erase) require explicit REAL_DEVICE_OPERATIONS=true, physical test-lab allowlist approval, and hardware capability support.",
        description="Technical disclaimer",
    )
