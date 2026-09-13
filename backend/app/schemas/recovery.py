"""Pydantic Schemas for Filesystem Recovery Operations and Provenance Data."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DataExtent(BaseModel):
    offset_bytes: int = Field(..., description="Absolute byte offset within source disk image")
    length_bytes: int = Field(..., description="Data extent length in bytes")
    is_valid_bounds: bool = Field(True, description="Whether offset and length fall strictly within disk boundaries")


class CandidateItem(BaseModel):
    candidate_id: str = Field(..., example="REC-CAND-001")
    name: str = Field(..., example="invoice_deleted.pdf")
    path: str = Field(..., example="/documents/financial/invoice_deleted.pdf")
    record_identifier: str = Field(..., example="Inode #1042 / MFT Record #452")
    declared_size_bytes: int = Field(..., example=1048576)
    created_at: Optional[str] = Field(None, example="2026-09-01T12:00:00Z")
    modified_at: Optional[str] = Field(None, example="2026-09-10T14:30:00Z")
    deleted_at: Optional[str] = Field(None, example="2026-09-12T09:15:00Z")
    extents: List[DataExtent] = Field(default_factory=list)
    classification_status: str = Field(
        ...,
        example="RECOVERABLE",
        description="RECOVERABLE, PARTIALLY_RECOVERABLE, METADATA_ONLY, CORRUPTED, UNSUPPORTED",
    )
    filesystem_type: str = Field(..., example="FAT32", description="FAT32, NTFS, EXT4, UNSUPPORTED")
    notes: Optional[str] = Field(None, example="Clean directory record entry carved")


class RecoveryScanRequest(BaseModel):
    evidence_id: str = Field(..., description="Target forensic evidence identifier", example="EVD-20260913-001")
    target_output_dir: Optional[str] = Field(None, description="Optional custom directory for extracted outputs")


class RecoveryScanResponse(BaseModel):
    scan_id: str = Field(..., example="scan-9a8b7c6d")
    evidence_id: str
    case_id: int
    filesystem_detected: str = Field(..., example="FAT32")
    pre_scan_sha256: str = Field(..., example="a2c44cb544d9e0c7297d5dd5761bed2e0f36a57a46cdce53e5bd3e53d172b74c")
    post_scan_sha256: str = Field(..., example="a2c44cb544d9e0c7297d5dd5761bed2e0f36a57a46cdce53e5bd3e53d172b74c")
    is_evidence_untouched: bool = Field(True, description="Verified pre_scan_sha256 == post_scan_sha256")
    total_candidates_found: int
    candidates_by_status: Dict[str, int]
    candidates: List[CandidateItem]
    manual_review_message: Optional[str] = Field(None, description="Detailed guidance if filesystem is unsupported or corrupted")


class RecoveryExtractRequest(BaseModel):
    evidence_id: str = Field(..., example="EVD-20260913-001")
    candidate_ids: List[str] = Field(..., example=["REC-CAND-001", "REC-CAND-002"])
    custom_output_dir: Optional[str] = Field(None, description="Optional custom export folder")


class ExtractedArtifactResponse(BaseModel):
    artifact_id: str
    candidate_id: str
    original_path: str
    output_file_path: str
    recovered_file_hash: str
    source_evidence_id: str
    source_image_hash: str
    source_offset_bytes: int
    file_size_bytes: int
    classification_status: str
    filesystem_type: str
    recovery_method: str
    tool_version: str
    operator_username: str
    recovered_at: datetime

    class Config:
        from_attributes = True


class RecoveryExtractJobResponse(BaseModel):
    job_id: str
    evidence_id: str
    total_requested: int
    successfully_extracted: int
    failed_extractions: int
    extracted_artifacts: List[ExtractedArtifactResponse]
