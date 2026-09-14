"""Pydantic Schemas for Signature-Based File Carving Operations and Metrics."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CarvingMetrics(BaseModel):
    bytes_scanned: int = Field(..., description="Total bytes read from source disk image")
    candidates_found: int = Field(..., description="Total raw header signature matches detected")
    validated_files: int = Field(..., description="Candidates passing format validation checks")
    rejected_candidates: int = Field(..., description="Candidates failing validation checks")
    elapsed_time_ms: float = Field(..., description="Scan execution duration in milliseconds")
    peak_memory_kb: float = Field(..., description="Estimated peak memory consumption in kilobytes")


class CarvingCandidateItem(BaseModel):
    candidate_id: str = Field(..., example="CARV-CAND-001")
    format: str = Field(..., example="JPEG", description="JPEG, PNG, PDF, ZIP")
    start_offset: int = Field(..., example=65536)
    end_offset: int = Field(..., example=131072)
    length_bytes: int = Field(..., example=65536)
    header_signature_hex: str = Field(..., example="FFD8FF")
    footer_signature_hex: Optional[str] = Field(None, example="FFD9")
    confidence_level: str = Field(..., example="HIGH", description="HIGH, MEDIUM, LOW")
    validation_reason: str = Field(..., example="Valid SOI, EOI, and APP0/EXIF metadata headers verified")
    is_valid: bool = Field(True)


class CarvingScanRequest(BaseModel):
    evidence_id: Optional[str] = Field(None, example="EVD-20260913-001")
    device_path: Optional[str] = Field(None, example="E:\\")
    target_formats: Optional[List[str]] = Field(None, description="Optional target formats filter ['JPEG', 'PNG', 'PDF', 'ZIP']")
    custom_output_dir: Optional[str] = Field(None, description="Optional custom extraction output directory")


class CarvedArtifactResponse(BaseModel):
    id: int
    carved_id: str
    case_id: int
    source_evidence_id: Optional[str] = None
    source_device_path: Optional[str] = None
    file_format: str
    output_file_path: str
    carved_file_hash: str
    source_image_hash: str
    source_start_offset: int
    source_end_offset: int
    file_size_bytes: int
    confidence_level: str
    validation_details: Optional[str] = None
    scan_version: str
    tool_version: str
    operator_username: str
    carved_at: datetime

    class Config:
        from_attributes = True


class CarvingScanResponse(BaseModel):
    scan_id: str
    evidence_id: Optional[str] = None
    device_path: Optional[str] = None
    case_id: int
    pre_scan_sha256: str
    post_scan_sha256: str
    is_evidence_untouched: bool
    metrics: CarvingMetrics
    carved_artifacts: List[CarvedArtifactResponse]

