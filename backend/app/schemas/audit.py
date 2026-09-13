"""Pydantic Schemas for ForensicShield Tamper-Evident Audit Logging System."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    """Input payload for recording an audit event."""

    actor: str = Field(..., description="Username or system component initiating the action")
    role: str = Field(..., description="Role of the actor (Administrator, Investigator, Operator, Viewer, System)")
    action: str = Field(..., description="Category or action performed (LOGIN, CASE_CREATE, DRY_RUN, etc.)")
    target_summary: str = Field(..., description="Concise, sanitized summary of target resource")
    result: str = Field(..., description="Outcome of action (SUCCESS, FAILED, DENIED, ABORTED, SIMULATED)")
    case_id: Optional[int] = Field(None, description="Associated forensic case ID")
    evidence_id: Optional[str] = Field(None, description="Associated evidence item identifier")


class AuditEventResponse(BaseModel):
    """Response representation of an immutable audit log record."""

    id: int
    event_id: str
    timestamp: datetime
    clock_source: str = "SERVER_UTC"
    actor: str
    role: str
    case_id: Optional[int] = None
    evidence_id: Optional[str] = None
    action: str
    target_summary: str
    result: str
    tool_version: str
    previous_hash: str
    current_hash: str

    class Config:
        from_attributes = True


class AuditChainVerificationResponse(BaseModel):
    """Response model for audit hash chain integrity verification scans."""

    is_valid: bool = Field(..., description="Whether the entire hash chain is cryptographically intact")
    total_events: int = Field(..., description="Total number of audit log records checked")
    chain_status: str = Field(..., description="Status summary ('INTACT' or 'BROKEN_CHAIN_DETECTED')")
    first_broken_event_id: Optional[str] = Field(None, description="Event ID of the first broken link or tampered record")
    broken_index: Optional[int] = Field(None, description="Zero-based sequence index where the chain was broken")
    reason: Optional[str] = Field(None, description="Detailed forensic explanation of verification failure")
    affected_event_ids: List[str] = Field(default_factory=list, description="List of all downstream event IDs affected by the break")
    verified_at: datetime = Field(..., description="UTC timestamp when verification scan was executed")


class AuditExportResponse(BaseModel):
    """Response model for exported audit log archives."""

    export_format: str = Field(..., description="Format of export (JSON or CSV)")
    event_count: int = Field(..., description="Total audit events exported")
    export_sha256: str = Field(..., description="SHA-256 cryptographic digest of exported byte stream")
    exported_at: datetime = Field(..., description="UTC timestamp of export generation")
