"""Forensic Signature-Based File Carving Orchestration Service for ForensicShield.

Executes read-only image parsing, pre/post scanning SHA-256 evidence verification,
chunked overlapping signature scanning, candidate format validation, output deduplication,
provenance persistence, and performance metric tracking.
"""

import hashlib
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.models.case import ForensicCase, EvidenceItem, CarvedFileArtifact
from app.schemas.carving import (
    CarvingScanRequest,
    CarvingScanResponse,
    CarvingMetrics,
    CarvedArtifactResponse,
)
from app.services.carving.carving_scanner import CarvingScanner
from app.services.carving.signature_registry import CarvingSignatureRegistry
from app.services.evidence_intake import StreamingHashCalculator


class FileCarvingService:
    """High-level service orchestrating signature file carving, output deduplication, and metrics."""

    def __init__(self, scanner: Optional[CarvingScanner] = None):
        self.scanner = scanner or CarvingScanner()

    def execute_carving_scan(
        self,
        db: Session,
        case_id: int,
        request: CarvingScanRequest,
        operator_username: str,
        custom_output_dir: Optional[Path] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> CarvingScanResponse:
        """
        Executes signature-based file carving scan:
        1. Validates case and evidence item context.
        2. Calculates PRE-SCAN SHA-256 evidence hash.
        3. Scans evidence image in bounded overlapping chunks for target signatures.
        4. Validates candidates using format-aware checks (JPEG, PNG, PDF, ZIP).
        5. Extracts candidate data to output directory, computing extracted SHA-256 hashes.
        6. Deduplicates identical output file hashes.
        7. Calculates POST-SCAN SHA-256 evidence hash and verifies zero evidence alteration.
        8. Tracks performance metrics (bytes_scanned, candidates_found, validated_files, rejected_candidates, elapsed_time_ms, peak_memory_kb).
        """
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == request.evidence_id).first()
        if not evidence:
            raise ForensicShieldException(
                message=f"Evidence item '{request.evidence_id}' not found.",
                code="EVIDENCE_NOT_FOUND",
                status_code=404,
            )

        # Select file path (prefer working copy if available, else original source)
        image_path = Path(evidence.working_copy_path) if (evidence.working_copy_path and Path(evidence.working_copy_path).exists()) else Path(evidence.file_path)

        if not image_path.exists():
            raise ForensicShieldException(
                message=f"Evidence file '{image_path}' not found on disk.",
                code="FILE_NOT_FOUND",
                status_code=404,
            )

        start_time = time.time()

        # 1. PRE-SCAN SHA-256 Evidence Hash Verification
        pre_scan_hash, image_size = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        scan_id = f"carve-scan-{uuid.uuid4().hex[:8]}"

        # Prepare export output directory
        if custom_output_dir is None:
            if request.custom_output_dir:
                custom_output_dir = Path(request.custom_output_dir)
            else:
                custom_output_dir = image_path.parent / "carved_output" / f"case_{case_id}"

        custom_output_dir.mkdir(parents=True, exist_ok=True)

        # 2. Open evidence strictly in binary read-only ('rb') mode and run scanner
        with open(image_path, "rb") as f_img:
            candidates, bytes_scanned, candidates_found, rejected_count = self.scanner.scan_image(
                f_img,
                image_size=image_size,
                target_formats=request.target_formats,
                check_cancelled=check_cancelled,
            )

            seen_carved_hashes: Set[str] = set()
            carved_artifacts: List[CarvedArtifactResponse] = []

            # 3. Extract and deduplicate candidates
            with open(image_path, "rb") as f_read:
                for cand in candidates:
                    if check_cancelled and check_cancelled():
                        break

                    sig_def = CarvingSignatureRegistry.get_signature_by_format(cand.format)
                    ext = sig_def.extension if sig_def else ".dat"

                    now = datetime.now(timezone.utc)
                    carved_id = f"CARV-{cand.format}-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
                    out_filename = f"{carved_id}_{cand.start_offset}_{cand.length_bytes}{ext}"
                    out_path = custom_output_dir / out_filename

                    # Read candidate window safely
                    f_read.seek(cand.start_offset)
                    cand_data = f_read.read(cand.length_bytes)

                    # Compute output file SHA-256 hash
                    file_hash = hashlib.sha256(cand_data).hexdigest()

                    # Deduplication check: skip saving duplicate file content
                    if file_hash in seen_carved_hashes:
                        continue

                    seen_carved_hashes.add(file_hash)

                    # Write carved file to output directory
                    out_path.write_bytes(cand_data)

                    # Create DB Record
                    db_artifact = CarvedFileArtifact(
                        carved_id=carved_id,
                        case_id=case_id,
                        source_evidence_id=request.evidence_id,
                        file_format=cand.format,
                        output_file_path=str(out_path),
                        carved_file_hash=file_hash,
                        source_image_hash=pre_scan_hash,
                        source_start_offset=cand.start_offset,
                        source_end_offset=cand.end_offset,
                        file_size_bytes=len(cand_data),
                        confidence_level=cand.confidence_level,
                        validation_details=cand.validation_reason,
                        scan_version="v1.0.0-carver",
                        tool_version="ForensicShield v1.0.0",
                        operator_username=operator_username,
                        carved_at=now,
                    )
                    db.add(db_artifact)
                    db.commit()
                    db.refresh(db_artifact)

                    carved_artifacts.append(CarvedArtifactResponse.model_validate(db_artifact))

        # 4. POST-SCAN SHA-256 Evidence Hash Verification
        post_scan_hash, _ = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        if pre_scan_hash.lower() != post_scan_hash.lower():
            raise ForensicShieldException(
                message="CRITICAL EVIDENCE TAMPERING DETECTED: Source image hash changed during file carving scan!",
                code="EVIDENCE_TAMPER_DETECTED",
                status_code=409,
            )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        # Estimate peak memory based on scanner chunk size (1 MB chunk + buffers)
        peak_memory_kb = round((self.scanner.chunk_size + 512 * 1024) / 1024, 2)

        metrics = CarvingMetrics(
            bytes_scanned=bytes_scanned,
            candidates_found=candidates_found,
            validated_files=len(carved_artifacts),
            rejected_candidates=rejected_count,
            elapsed_time_ms=elapsed_ms,
            peak_memory_kb=peak_memory_kb,
        )

        audit_log(
            message=f"Signature carving completed for '{request.evidence_id}'. Found {len(carved_artifacts)} unique carved files in {elapsed_ms}ms.",
            operation="EVIDENCE_CARVING_SCAN",
            status="SUCCESS",
            case_id=str(case_id),
            user_id=operator_username,
            extra_payload={
                "evidence_id": request.evidence_id,
                "validated_files": len(carved_artifacts),
                "elapsed_ms": elapsed_ms,
            },
        )

        return CarvingScanResponse(
            scan_id=scan_id,
            evidence_id=request.evidence_id,
            case_id=case_id,
            pre_scan_sha256=pre_scan_hash,
            post_scan_sha256=post_scan_hash,
            is_evidence_untouched=True,
            metrics=metrics,
            carved_artifacts=carved_artifacts,
        )
