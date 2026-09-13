"""Pydantic Schemas for ForensicShield Report Generation & Compliance Module."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    """Metadata parameters for a generated forensic report."""

    report_id: str = Field(..., description="Unique report identifier (e.g. RPT-20260913-A1B2C3D4)")
    case_id: int = Field(..., description="Forensic case database ID")
    case_number: str = Field(..., description="Case number identifier")
    case_title: str = Field(..., description="Case title")
    generated_at: datetime = Field(..., description="UTC timestamp of report generation")
    generated_by: str = Field(..., description="Operator username who generated the report")
    tool_version: str = Field("ForensicShield v1.0.0", description="ForensicShield tool version")
    environment: str = Field("production", description="Execution environment description")


class StatusClassificationCounts(BaseModel):
    """5-point status classification breakdown matrix."""

    verified: int = Field(0, description="Total verified intact evidence or operations")
    inconclusive: int = Field(0, description="Total inconclusive operations")
    failed: int = Field(0, description="Total failed operations")
    unsupported: int = Field(0, description="Total unsupported operations requiring manual review")
    manual_review: int = Field(0, description="Total items flagged for manual forensic review")


class ReportSummary(BaseModel):
    """Summary statistics for case forensic artifacts and evidence."""

    evidence_count: int = Field(0, description="Total evidence items ingested")
    total_evidence_bytes: int = Field(0, description="Total size of evidence image files in bytes")
    carved_artifacts_count: int = Field(0, description="Total carved file artifacts extracted")
    recovered_artifacts_count: int = Field(0, description="Total filesystem recovery artifacts extracted")
    audit_events_count: int = Field(0, description="Total audit events recorded in audit log chain")
    audit_chain_status: str = Field("INTACT", description="Status of local audit log hash chain ('INTACT' or 'BROKEN')")


class ForensicReportRequest(BaseModel):
    """Request parameters for generating a forensic report."""

    include_evidence: bool = Field(True, description="Include evidence intake inventory")
    include_recovery: bool = Field(True, description="Include filesystem recovery artifacts")
    include_carving: bool = Field(True, description="Include file carving artifacts")
    include_audit_trail: bool = Field(True, description="Include tamper-evident audit log trail")
    format: str = Field("both", description="Report format: 'pdf', 'json', or 'both'")


class ForensicReportResponse(BaseModel):
    """Response containing report execution details, SHA-256 digests, and download links."""

    report_id: str = Field(..., description="Unique report ID")
    case_id: int = Field(..., description="Associated case ID")
    generated_at: datetime = Field(..., description="UTC timestamp of report generation")
    pdf_sha256: str = Field(..., description="SHA-256 cryptographic digest of generated PDF report")
    json_sha256: str = Field(..., description="SHA-256 cryptographic digest of generated JSON manifest")
    audit_event_id: str = Field(..., description="Event ID of audit event recording report SHA-256 digest")
    pdf_download_url: Optional[str] = Field(None, description="Download URL for PDF report")
    json_download_url: Optional[str] = Field(None, description="Download URL for JSON manifest")

    summary: ReportSummary = Field(..., description="Case artifact summary statistics")
    classifications: StatusClassificationCounts = Field(..., description="5-point status classification counts")


class ReportPreviewResponse(BaseModel):
    """Response for report preview metadata."""

    case_id: int = Field(..., description="Case ID")
    case_number: str = Field(..., description="Case number string")
    case_title: str = Field(..., description="Compliance-scrubbed case title")
    summary: ReportSummary = Field(..., description="Summary statistics")
    classifications: StatusClassificationCounts = Field(..., description="Classification breakdown")
    audit_chain_valid: bool = Field(True, description="Audit chain validity status")
    evidence_count: int = Field(0, description="Total evidence count")
    artifact_count: int = Field(0, description="Total artifact count")

