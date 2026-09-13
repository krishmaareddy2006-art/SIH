"""Forensic Filesystem-Aware Recovery Orchestration Service for ForensicShield.

Executes read-only evidence image parsing, pre/post scanning SHA-256 integrity checks,
adapter selection, candidate entry classification, safe bounds verification, export output
generation, and evidence provenance tracking.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.models.case import ForensicCase, EvidenceItem, RecoveredArtifact
from app.schemas.recovery import (
    CandidateItem,
    RecoveryScanRequest,
    RecoveryScanResponse,
    RecoveryExtractRequest,
    RecoveryExtractJobResponse,
    ExtractedArtifactResponse,
)
from app.services.evidence_intake import StreamingHashCalculator
from app.services.recovery_adapters.base_adapter import BaseFilesystemAdapter
from app.services.recovery_adapters.ext4_adapter import Ext4FilesystemAdapter
from app.services.recovery_adapters.fat32_adapter import FAT32FilesystemAdapter
from app.services.recovery_adapters.ntfs_adapter import NTFSFilesystemAdapter
from app.services.recovery_adapters.unsupported_adapter import UnsupportedFilesystemAdapter

REGISTERED_ADAPTERS: List[BaseFilesystemAdapter] = [
    FAT32FilesystemAdapter(),
    NTFSFilesystemAdapter(),
    Ext4FilesystemAdapter(),
]


class FilesystemRecoveryService:
    """High-level service executing read-only evidence recovery and provenance tracking."""

    @staticmethod
    def select_adapter(file_handle, image_size: int) -> Tuple[BaseFilesystemAdapter, str, Dict]:
        """Scans image headers to select matching filesystem adapter or returns Unsupported fallback."""
        for adapter in REGISTERED_ADAPTERS:
            is_detected, fs_name, meta = adapter.detect(file_handle, image_size)
            if is_detected:
                return adapter, fs_name, meta

        fallback = UnsupportedFilesystemAdapter()
        _, fs_name, meta = fallback.detect(file_handle, image_size)
        return fallback, fs_name, meta

    def scan_evidence_recovery(
        self,
        db: Session,
        case_id: int,
        evidence_id: str,
        operator_username: str,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> RecoveryScanResponse:
        """
        Executes read-only recovery scan:
        1. Validates case and evidence item access.
        2. Performs PRE-SCAN SHA-256 hash calculation on source evidence image.
        3. Opens evidence image strictly in binary read-only ('rb') mode.
        4. Detects filesystem signature and parses candidate deleted entries.
        5. Performs POST-SCAN SHA-256 hash calculation on source evidence image.
        6. Verifies evidence was untouched during scan (pre_hash == post_hash).
        7. Classifies candidates into RECOVERABLE, PARTIALLY_RECOVERABLE, METADATA_ONLY, CORRUPTED, UNSUPPORTED.
        """
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
        if not evidence:
            raise ForensicShieldException(
                message=f"Evidence item '{evidence_id}' not found in database.",
                code="EVIDENCE_NOT_FOUND",
                status_code=404,
            )

        # Select file path (prefer working copy if available, else original source)
        image_path = Path(evidence.working_copy_path) if (evidence.working_copy_path and Path(evidence.working_copy_path).exists()) else Path(evidence.file_path)

        if not image_path.exists():
            raise ForensicShieldException(
                message=f"Evidence image file '{image_path}' not found on disk.",
                code="FILE_NOT_FOUND",
                status_code=404,
            )

        # 1. PRE-SCAN SHA-256 Evidence Hash Verification
        pre_scan_hash, image_size = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        scan_id = f"scan-{uuid.uuid4().hex[:8]}"
        candidates: List[CandidateItem] = []
        manual_review_msg: Optional[str] = None

        # 2. Open evidence strictly in binary read-only ('rb') mode
        with open(image_path, "rb") as f_img:
            adapter, fs_name, meta = self.select_adapter(f_img, image_size)
            candidates = adapter.scan_deleted_entries(
                f_img, image_size=image_size, check_cancelled=check_cancelled
            )

            if fs_name == "UNSUPPORTED" or any(c.classification_status == "UNSUPPORTED" for c in candidates):
                manual_review_msg = (
                    "UNSUPPORTED_FILESYSTEM_MANUAL_REVIEW_REQUIRED: Target disk image contains an unsupported "
                    "or corrupted volume header. Automated carving halted to prevent false positive guesses. "
                    "Manual analyst laboratory inspection required per ISO/IEC 27037:2012."
                )

        # 3. POST-SCAN SHA-256 Evidence Hash Verification
        post_scan_hash, _ = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        # 4. Strict Evidence Integrity Check
        if pre_scan_hash.lower() != post_scan_hash.lower():
            audit_log(
                message=f"CRITICAL EVIDENCE TAMPERING: Source image '{evidence_id}' altered during recovery scan!",
                operation="EVIDENCE_TAMPER_DETECTED",
                status="CRITICAL_FAILURE",
                case_id=str(case_id),
                user_id=operator_username,
                extra_payload={"pre_hash": pre_scan_hash, "post_hash": post_scan_hash},
            )
            raise ForensicShieldException(
                message="CRITICAL EVIDENCE TAMPERING DETECTED: Source evidence image hash changed during scan operation!",
                code="EVIDENCE_TAMPER_DETECTED",
                status_code=409,
            )

        # Count candidates by status
        status_counts = {
            "RECOVERABLE": 0,
            "PARTIALLY_RECOVERABLE": 0,
            "METADATA_ONLY": 0,
            "CORRUPTED": 0,
            "UNSUPPORTED": 0,
        }
        for cand in candidates:
            status_counts[cand.classification_status] = status_counts.get(cand.classification_status, 0) + 1

        audit_log(
            message=f"Filesystem recovery scan completed for evidence '{evidence_id}'. Found {len(candidates)} candidates.",
            operation="EVIDENCE_RECOVERY_SCAN",
            status="SUCCESS",
            case_id=str(case_id),
            user_id=operator_username,
            extra_payload={
                "evidence_id": evidence_id,
                "filesystem": fs_name,
                "total_candidates": len(candidates),
                "status_counts": status_counts,
                "pre_hash": pre_scan_hash,
                "post_hash": post_scan_hash,
            },
        )

        return RecoveryScanResponse(
            scan_id=scan_id,
            evidence_id=evidence_id,
            case_id=case_id,
            filesystem_detected=fs_name,
            pre_scan_sha256=pre_scan_hash,
            post_scan_sha256=post_scan_hash,
            is_evidence_untouched=True,
            total_candidates_found=len(candidates),
            candidates_by_status=status_counts,
            candidates=candidates,
            manual_review_message=manual_review_msg,
        )

    def extract_recovery_candidates(
        self,
        db: Session,
        case_id: int,
        request: RecoveryExtractRequest,
        operator_username: str,
        custom_output_dir: Optional[Path] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> RecoveryExtractJobResponse:
        """
        Extracts selected recovery candidate data to output folder with complete provenance records.
        """
        # Run recovery scan to locate target candidates
        scan_response = self.scan_evidence_recovery(
            db=db,
            case_id=case_id,
            evidence_id=request.evidence_id,
            operator_username=operator_username,
            check_cancelled=check_cancelled,
        )

        evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == request.evidence_id).first()
        image_path = Path(evidence.working_copy_path) if (evidence.working_copy_path and Path(evidence.working_copy_path).exists()) else Path(evidence.file_path)

        # Prepare export output directory
        if custom_output_dir is None:
            if request.custom_output_dir:
                custom_output_dir = Path(request.custom_output_dir)
            else:
                custom_output_dir = image_path.parent / "recovered_output" / f"case_{case_id}"

        custom_output_dir.mkdir(parents=True, exist_ok=True)

        extracted_artifacts: List[ExtractedArtifactResponse] = []
        success_count = 0
        fail_count = 0
        job_id = f"job-extract-{uuid.uuid4().hex[:8]}"

        target_set = set(request.candidate_ids)
        target_candidates = [c for c in scan_response.candidates if c.candidate_id in target_set]

        # PRE-EXTRACTION Evidence Hash Check
        pre_extract_hash, image_size = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        with open(image_path, "rb") as f_img:
            adapter, fs_name, _ = self.select_adapter(f_img, image_size)

            for cand in target_candidates:
                if check_cancelled and check_cancelled():
                    break

                success, out_file, file_hash, bytes_written = adapter.extract_candidate_data(
                    f_img, candidate=cand, image_size=image_size, output_dir=custom_output_dir
                )

                if success and out_file and out_file.exists():
                    success_count += 1
                    now = datetime.now(timezone.utc)
                    artifact_id = f"EVD-REC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
                    source_offset = cand.extents[0].offset_bytes if cand.extents else 0

                    db_artifact = RecoveredArtifact(
                        artifact_id=artifact_id,
                        candidate_id=cand.candidate_id,
                        case_id=case_id,
                        source_evidence_id=request.evidence_id,
                        original_path=cand.path,

                        output_file_path=str(out_file),
                        recovered_file_hash=file_hash,
                        source_image_hash=pre_extract_hash,
                        source_offset_bytes=source_offset,
                        file_size_bytes=bytes_written,
                        classification_status=cand.classification_status,
                        filesystem_type=cand.filesystem_type,
                        recovery_method=f"{fs_name}_DELETED_CARVE",
                        tool_version="ForensicShield v1.0.0",
                        operator_username=operator_username,
                        recovered_at=now,
                    )
                    db.add(db_artifact)
                    db.commit()
                    db.refresh(db_artifact)

                    extracted_artifacts.append(ExtractedArtifactResponse.model_validate(db_artifact))
                else:
                    fail_count += 1

        # POST-EXTRACTION Evidence Hash Check
        post_extract_hash, _ = StreamingHashCalculator.calculate_sha256(
            image_path, check_cancelled=check_cancelled
        )

        if pre_extract_hash.lower() != post_extract_hash.lower():
            raise ForensicShieldException(
                message="CRITICAL EVIDENCE TAMPERING DETECTED: Source image hash changed during extraction!",
                code="EVIDENCE_TAMPER_DETECTED",
                status_code=409,
            )

        audit_log(
            message=f"Extraction job completed: {success_count} artifacts recovered successfully, {fail_count} failed.",
            operation="EVIDENCE_RECOVERY_EXTRACT",
            status="SUCCESS",
            case_id=str(case_id),
            user_id=operator_username,
            extra_payload={
                "job_id": job_id,
                "successful": success_count,
                "failed": fail_count,
                "output_dir": str(custom_output_dir),
            },
        )

        return RecoveryExtractJobResponse(
            job_id=job_id,
            evidence_id=request.evidence_id,
            total_requested=len(target_candidates),
            successfully_extracted=success_count,
            failed_extractions=fail_count,
            extracted_artifacts=extracted_artifacts,
        )
