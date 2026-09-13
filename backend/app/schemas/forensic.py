"""Pydantic Schemas for ForensicShield API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# Case Schemas
class CaseBase(BaseModel):
    case_number: str = Field(..., example="CASE-2026-001")
    title: str = Field(..., example="Target Machine Disk Inspection")
    investigator: Optional[str] = Field("Analyst", example="Analyst-42")
    description: Optional[str] = Field(None, example="Inspection of suspect workstation")

    @field_validator("investigator", mode="before")
    @classmethod
    def format_investigator(cls, v):
        if hasattr(v, "username"):
            return v.username
        if isinstance(v, str):
            return v
        return "Analyst"


class CaseCreate(CaseBase):
    pass


class CaseResponse(CaseBase):
    id: int
    status: str = "OPEN"
    investigator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True




# System Health & Status Schemas
class SystemStatusResponse(BaseModel):
    project_name: str
    version: str
    safe_mode: bool
    real_device_operations: bool
    environment: str
    status: str = "HEALTHY"


# Forensic Operation Schemas
class OperationRequest(BaseModel):
    target_path: str = Field(..., example="/evidence/disk_image.raw")
    operation_type: str = Field(..., example="SECURE_WIPE_SIMULATION")
    simulate: bool = Field(True, description="Enforce dry-run simulation mode")


class OperationResponse(BaseModel):
    operation_id: str
    status: str
    safe_mode_active: bool
    target_path: str
    preview: str
    execution_time_ms: float
