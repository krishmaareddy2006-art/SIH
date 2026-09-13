"""Pydantic Schemas for Sensitive Jobs (Sanitization & Recovery)."""

from pydantic import BaseModel, Field


class SensitiveJobRequest(BaseModel):
    case_id: int = Field(..., example=1, description="Target case ID")
    reason: str = Field(..., min_length=5, example="Sanitizing temporary cache partition after analysis", description="Audit justification reason")
    target_identifier: str = Field(..., example="/evidence/target_partition.raw", description="Target device/file identifier")
    explicit_confirmation: str = Field(..., example="CONFIRM_SENSITIVE_ACTION", description="Strict confirmation string requirement")
    simulate: bool = Field(True, description="Enforce dry-run simulation mode")


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    case_id: int
    target_identifier: str
    status: str
    safe_mode_active: bool
    preview: str
    execution_details: str
