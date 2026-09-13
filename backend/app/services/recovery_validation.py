"""Forensic Recovery Validation & Confidence-Scoring Service for ForensicShield.

Evaluates recovered and carved file artifacts using a transparent 7-factor scoring rubric,
safe static format parsers, deterministic versioning, and explainable forensic reports.
"""

import hashlib
import os
from pathlib import Path
from typing import List, Optional, Tuple

from app.core.exceptions import ForensicShieldException
from app.schemas.validation import (
    FactorEvaluation,
    ValidationFactorsBreakdown,
    ValidationRequest,
    ValidationReport,
)
from app.services.validation.format_parsers import FormatParserFactory, StaticParseResult

VALIDATION_ENGINE_VERSION = "v1.0.0-val-engine"

FORMAT_EXTENSION_MAP = {
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "PDF": {".pdf"},
    "ZIP": {".zip", ".jar", ".docx", ".xlsx", ".pptx"},
    "GENERIC": set(),
}


class RecoveryValidationService:
    """High-level service orchestrating recovery validation and factor-based scoring."""

    def __init__(self, version: str = VALIDATION_ENGINE_VERSION):
        self.version = version

    def validate_file(self, request: ValidationRequest) -> ValidationReport:
        """
        Validates a recovered or carved artifact file on disk:
        1. Reads file safely in binary mode without executing.
        2. Auto-detects or validates format magic bytes.
        3. Executes safe static format parser (checking CRCs, headers, footers, security flags).
        4. Calculates 7 explainable factor scores (0-100 total).
        5. Evaluates extension match and manual review flags.
        6. Returns deterministic ValidationReport.
        """
        path = Path(request.file_path)
        if not path.exists():
            raise ForensicShieldException(
                message=f"Artifact file '{request.file_path}' not found on disk.",
                code="FILE_NOT_FOUND",
                status_code=404,
            )

        # Read artifact binary payload
        data = path.read_bytes()
        file_size = len(data)
        file_sha256 = hashlib.sha256(data).hexdigest()
        file_name = path.name
        declared_ext = path.suffix.lower()

        # Get safe static format parser
        parser = FormatParserFactory.get_parser(fmt=request.expected_format, data=data)
        parse_res: StaticParseResult = parser.parse(data)

        detected_format = parse_res.detected_format
        expected_exts = FORMAT_EXTENSION_MAP.get(detected_format, set())
        is_ext_matched = (declared_ext in expected_exts) if expected_exts else True

        if expected_exts and not is_ext_matched:
            parse_res.warnings.append(
                f"Extension mismatch: File has declared extension '{declared_ext}' but payload signature matches format '{detected_format}'"
            )

        # ---------------------------------------------------------
        # Factor 1: Valid Header (max 20 pts)
        # ---------------------------------------------------------
        if parse_res.header_valid:
            f1 = FactorEvaluation(passed=True, score_granted=20, max_score=20, details="Header magic signature verified successfully")
        else:
            f1 = FactorEvaluation(passed=False, score_granted=0, max_score=20, details="Missing or corrupted header magic signature")

        # ---------------------------------------------------------
        # Factor 2: Valid Footer (max 15 pts)
        # ---------------------------------------------------------
        if parse_res.footer_valid:
            f2 = FactorEvaluation(passed=True, score_granted=15, max_score=15, details="Footer / end marker signature verified successfully")
        else:
            f2 = FactorEvaluation(passed=False, score_granted=0, max_score=15, details="Missing or unverified footer end marker")

        # ---------------------------------------------------------
        # Factor 3: Parser Success (max 20 pts)
        # ---------------------------------------------------------
        if parse_res.parser_success:
            f3 = FactorEvaluation(passed=True, score_granted=20, max_score=20, details="Format-specific structural elements parsed cleanly")
        else:
            f3 = FactorEvaluation(passed=False, score_granted=0, max_score=20, details="Format-specific structural parsing failed or incomplete")

        # ---------------------------------------------------------
        # Factor 4: Complete Length (max 15 pts)
        # ---------------------------------------------------------
        if parse_res.length_complete:
            f4 = FactorEvaluation(passed=True, score_granted=15, max_score=15, details="File length matches calculated format container length exactly")
        elif parse_res.calculated_length > 0 and parse_res.calculated_length <= file_size:
            f4 = FactorEvaluation(passed=True, score_granted=10, max_score=15, details=f"Valid container length ({parse_res.calculated_length} B) with minor trailing data")
        else:
            f4 = FactorEvaluation(passed=False, score_granted=0, max_score=15, details="File truncated or container length unverified")

        # ---------------------------------------------------------
        # Factor 5: Checksum / CRC Success (max 15 pts)
        # ---------------------------------------------------------
        if parse_res.crc_valid:
            f5 = FactorEvaluation(passed=True, score_granted=15, max_score=15, details="Internal payload CRC32/checksum verification passed")
        else:
            f5 = FactorEvaluation(passed=False, score_granted=0, max_score=15, details="Internal payload CRC32 checksum mismatch or unverified")

        # ---------------------------------------------------------
        # Factor 6: Source Provenance (max 10 pts)
        # ---------------------------------------------------------
        prov_score = 0
        prov_details = []
        if request.source_evidence_hash:
            prov_score += 5
            prov_details.append("Source evidence image SHA-256 hash provided")

        if request.source_offset is not None and request.source_offset >= 0:
            prov_score += 5
            prov_details.append(f"Valid source byte offset ({request.source_offset}) recorded")

        if prov_score == 0:
            f6 = FactorEvaluation(passed=False, score_granted=0, max_score=10, details="No source evidence provenance metadata supplied")
        else:
            f6 = FactorEvaluation(passed=True, score_granted=prov_score, max_score=10, details="; ".join(prov_details))

        # ---------------------------------------------------------
        # Factor 7: Overlap or Ambiguity (max 5 pts)
        # ---------------------------------------------------------
        # Check if file has trailing garbage or suspicious double headers
        if f1.passed and f2.passed and not parse_res.warnings:
            f7 = FactorEvaluation(passed=True, score_granted=5, max_score=5, details="No overlapping signature conflicts or container ambiguity")
        elif f1.passed:
            f7 = FactorEvaluation(passed=True, score_granted=3, max_score=5, details="Minor boundary ambiguity detected")
        else:
            f7 = FactorEvaluation(passed=False, score_granted=0, max_score=5, details="Ambiguous container boundaries or header conflicts")

        factors = ValidationFactorsBreakdown(
            valid_header=f1,
            valid_footer=f2,
            parser_success=f3,
            complete_length=f4,
            checksum_crc_success=f5,
            source_provenance=f6,
            overlap_ambiguity=f7,
        )

        overall_score = sum([
            f1.score_granted,
            f2.score_granted,
            f3.score_granted,
            f4.score_granted,
            f5.score_granted,
            f6.score_granted,
            f7.score_granted,
        ])
        overall_score = min(100, max(0, overall_score))

        # Determine Confidence Label
        if overall_score >= 85:
            label = "HIGH_CONFIDENCE"
        elif overall_score >= 60:
            label = "MEDIUM_CONFIDENCE"
        elif overall_score >= 30:
            label = "LOW_CONFIDENCE"
        else:
            label = "UNRELIABLE_CORRUPTED"

        requires_review = (overall_score < 70) or (len(parse_res.warnings) > 0) or (len(parse_res.security_flags) > 0) or (not is_ext_matched)

        return ValidationReport(
            file_path=str(path),
            file_name=file_name,
            file_size_bytes=file_size,
            file_sha256=file_sha256,
            detected_format=detected_format,
            declared_extension=declared_ext,
            is_extension_matched=is_ext_matched,
            overall_score=overall_score,
            confidence_label=label,
            factors=factors,
            reasons=parse_res.reasons,
            warnings=parse_res.warnings,
            security_flags=parse_res.security_flags,
            requires_manual_review=requires_review,
            validation_version=self.version,
        )
