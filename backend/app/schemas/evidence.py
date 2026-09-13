"""Pydantic Schemas for Evidence Items, Import Requests, Verification, and Manifest Exports."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EvidenceCreate(BaseModel):
    item_number: str = Field(..., example="EVID-001")
    title: str = Field(..., example="Workstation Hard Drive Image")
    file_path: str = Field(..., example="/evidence/workstation_disk.raw")
    sha256_hash: Optional[str] = Field(None, example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    file_size_bytes: Optional[int] = Field(None, example=500000000)


class EvidenceImportRequest(BaseModel):
    source_file_path: str = Field(..., description="Absolute file system path to original forensic image file", example="C:\\evidence\\image.raw")
    item_number: Optional[str] = Field(None, description="Optional custom item number (e.g., EVID-101)", example="EVID-101")
    title: Optional[str] = Field(None, description="Descriptive title for evidence item", example="Suspect Workstation Image")
    source_description: Optional[str] = Field(None, description="Detailed origin description", example="Acquired from SATA Slot 1 by Agent Smith")
    create_working_copy: bool = Field(True, description="Whether to create a read-only working copy for processing")


class EvidenceIntakeResponse(BaseModel):
    id: int
    evidence_id: str
    case_id: int
    item_number: str
    title: str
    original_filename: str
    file_path: str
    working_copy_path: Optional[str] = None
    sha256_hash: str
    file_size_bytes: int
    import_time: datetime
    source_description: Optional[str] = None
    operator_username: str
    tool_version: str
    processing_status: str
    last_verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceVerificationRequest(BaseModel):
    stage: str = Field("PRE_PROCESSING", description="Processing stage requesting verification", example="DEEP_FILE_CARVING")


class EvidenceVerificationResponse(BaseModel):
    evidence_id: str
    case_id: int
    stage: str
    is_valid: bool
    expected_hash: str
    calculated_hash: str
    processing_status: str
    verified_at: datetime
    message: str


class EvidenceManifestJSON(BaseModel):
    manifest_version: str = Field("1.0.0", example="1.0.0")
    exported_at: datetime
    exported_by: str
    case_id: int
    case_number: str
    total_evidence_items: int
    evidence_items: List[EvidenceIntakeResponse]


class CaseAccessGrantRequest(BaseModel):
    user_id: int = Field(..., example=3)

