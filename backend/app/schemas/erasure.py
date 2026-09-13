"""Pydantic Schemas for Controlled Secure File & Folder Erasure Module."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ErasureTokenRequest(BaseModel):
    """Request payload for generating a confirmation token for a specific erasure target."""

    target_path: str = Field(..., example="/evidence/sandbox/target_folder")
    approved_root: str = Field(..., example="/evidence/sandbox")


class ErasureTokenResponse(BaseModel):
    """Token response containing the required typed confirmation string."""

    target_path: str
    approved_root: str
    confirmation_token: str
    required_confirmation_string: str = Field(
        ..., example="CONFIRM:/evidence/sandbox/target_folder:a1b2c3d4"
    )
    expires_in_seconds: int = 900


class ErasureItemResult(BaseModel):
    """Per-item status result entry."""

    path: str
    item_type: str = Field(..., example="FILE", description="FILE, DIRECTORY, SYMLINK, SPECIAL")
    status: str = Field(
        ...,
        example="ERASED",
        description="PLANNED, ERASED, FAILED, SKIPPED, UNSUPPORTED, REQUIRES_REVIEW",
    )
    size_bytes: int = 0
    passes_completed: int = 0
    message: str = Field(..., example="Logical file overwrite and unlink completed.")


class ErasureExecuteRequest(BaseModel):
    """Request payload for executing dry-run preview or live logical file erasure."""

    target_path: str = Field(..., example="/evidence/sandbox/target_folder")
    approved_root: Optional[str] = Field(None, example="/evidence/sandbox")
    confirmation_token: Optional[str] = Field(
        None, example="CONFIRM:/evidence/sandbox/target_folder:a1b2c3d4"
    )
    dry_run: bool = Field(False, description="Enforce dry-run listing without modifying files")
    overwrite_passes: int = Field(1, description="Number of overwrite passes (1 or 3)")
    follow_symlinks: bool = Field(False, description="Strictly False. Symlinks are not followed.")
    reason: str = Field("Standard DFIR file erasure", min_length=3, example="Authorized evidence directory cleanup")


class ErasureReport(BaseModel):
    """Complete execution audit report for file erasure operation."""

    execution_id: str
    target_path: str
    approved_root: str
    dry_run: bool
    safe_mode_active: bool
    overwrite_passes: int
    total_items: int
    erased_items: int
    skipped_items: int
    failed_items: int
    total_bytes_erased: int
    execution_time_ms: float
    status: str = Field(..., example="COMPLETED", description="SIMULATED, COMPLETED, PARTIAL_SUCCESS, FAILED")
    items: List[ErasureItemResult] = Field(default_factory=list)
    disclaimer: str = Field(
        "LOGICAL FILE ERASURE DISCLAIMER: File contents were logically overwritten with zero/pattern passes and unlinked via filesystem fsync. Physical flash media (SSD/NVMe) wear-leveling FTL blocks may retain latent physical data without ATA/NVMe hardware sanitization.",
        description="Legal/technical disclaimer",
    )
