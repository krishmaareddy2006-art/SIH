"""Pydantic Validation Schemas for ForensicShield Recovery Validation Engine.

Defines factor evaluations, transparent scoring breakdowns, confidence labels,
reasons, warnings, security flags, and manual review recommendation schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FactorEvaluation(BaseModel):
    """Evaluation result for an individual scoring factor."""

    passed: bool = Field(..., description="Whether the factor criteria was met")
    score_granted: int = Field(..., description="Points awarded for this factor")
    max_score: int = Field(..., description="Maximum possible points for this factor")
    details: str = Field(..., description="Explanatory details for the factor evaluation")


class ValidationFactorsBreakdown(BaseModel):
    """Breakdown of all 7 explainable scoring factors."""

    valid_header: FactorEvaluation = Field(..., description="Header magic byte signature check (max 20 pts)")
    valid_footer: FactorEvaluation = Field(..., description="Footer / end marker signature check (max 15 pts)")
    parser_success: FactorEvaluation = Field(..., description="Format-specific structural parsing success (max 20 pts)")
    complete_length: FactorEvaluation = Field(..., description="Declared vs calculated length consistency (max 15 pts)")
    checksum_crc_success: FactorEvaluation = Field(..., description="Payload CRC32 / checksum verification (max 15 pts)")
    source_provenance: FactorEvaluation = Field(..., description="Source evidence hash & offset bounds match (max 10 pts)")
    overlap_ambiguity: FactorEvaluation = Field(..., description="Absence of overlapping signature conflicts (max 5 pts)")


class ValidationRequest(BaseModel):
    """Request payload for validating a recovered or carved artifact file."""

    file_path: str = Field(..., description="Path to the recovered file artifact on disk")
    expected_format: Optional[str] = Field(None, description="Expected format identifier (e.g., JPEG, PNG, PDF, ZIP)")
    source_evidence_hash: Optional[str] = Field(None, description="Expected SHA-256 hash of source evidence image")
    source_offset: Optional[int] = Field(None, description="Source offset byte position in evidence image")
    claimed_size: Optional[int] = Field(None, description="Declared or expected file size in bytes")


class ValidationReport(BaseModel):
    """Comprehensive recovery validation report and confidence-scoring response."""

    file_path: str = Field(..., description="Path to the validated file")
    file_name: str = Field(..., description="Filename of the validated artifact")
    file_size_bytes: int = Field(..., description="Actual file size in bytes")
    file_sha256: str = Field(..., description="SHA-256 digest of the validated artifact")
    detected_format: str = Field(..., description="Detected format identifier (JPEG, PNG, PDF, ZIP, GENERIC)")
    declared_extension: str = Field(..., description="Extension extracted from file path")
    is_extension_matched: bool = Field(..., description="Whether declared extension matches detected format")
    
    overall_score: int = Field(..., description="Deterministic heuristic score (0-100)")
    confidence_label: str = Field(..., description="Confidence label (HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, UNRELIABLE_CORRUPTED)")
    
    factors: ValidationFactorsBreakdown = Field(..., description="Explainable 7-factor scoring breakdown")
    reasons: List[str] = Field(default_factory=list, description="Human-readable positive and diagnostic reasons")
    warnings: List[str] = Field(default_factory=list, description="Format, truncation, or checksum warning messages")
    security_flags: List[str] = Field(default_factory=list, description="Security flags (e.g. macro detection, PDF active scripts, embedded executables)")
    
    requires_manual_review: bool = Field(..., description="Whether manual forensic review is recommended")
    validation_version: str = Field("v1.0.0-val-engine", description="Deterministic validation engine version")
    disclaimer: str = Field(
        "Empirical heuristic quality index (0-100). This score is NOT a statistical probability of truth.",
        description="Mandatory disclaimer prohibiting representation as statistical probability",
    )
