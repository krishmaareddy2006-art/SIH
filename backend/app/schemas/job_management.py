"""Pydantic Schemas for ForensicShield Job Management Layer."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class JobSubmitRequest(BaseModel):
    """Payload for submitting a long-running background job."""

    case_id: Optional[int] = Field(None, description="Associated forensic case ID")
    type: str = Field(..., description="Job type (SANITIZATION, RECOVERY, CARVING, ERASURE, EVIDENCE_INTAKE)")
    target_identifier: str = Field(..., description="Target device path, file path, or evidence ID")
    reason: str = Field(..., description="Mandatory audit justification reason (min 5 chars)")
    explicit_confirmation: str = Field("CONFIRM_SENSITIVE_ACTION", description="Explicit confirmation string")
    simulate: bool = Field(True, description="Whether to execute dry-run simulation mode")


class JobDetailResponse(BaseModel):
    """Detailed response for a persistent Job record."""

    id: int
    job_id: str
    case_id: Optional[int] = None
    type: str
    status: str = Field(..., description="Status: queued, running, cancelling, completed, failed, aborted, manual-review")
    target_identifier: str
    progress: float = Field(0.0, description="Progress percentage from 0.0 to 100.0")
    progress_stage: str = Field("Queued", description="Human-readable current execution stage")
    is_progress_exact: bool = Field(True, description="Whether progress percentage is exact or estimated")

    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    cancellation_requested: bool = False
    error_summary: Optional[str] = None
    reason: str
    operator_username: str
    worker_node_id: str = "in-process-worker-1"

    preview: Optional[str] = Field(None, description="Safe mode preview message")
    execution_details: Optional[str] = Field(None, description="Detailed execution narrative")

    class Config:
        from_attributes = True


class JobCancelResponse(BaseModel):
    """Response returned upon job cancellation request."""

    job_id: str
    status: str
    message: str


class JobRecoveryResponse(BaseModel):
    """Response returned upon server startup stale job state recovery."""

    recovered_jobs_count: int
    aborted_jobs_count: int
    message: str
