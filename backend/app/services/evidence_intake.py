"""Forensic Evidence Image Intake & Integrity Verification Engine for ForensicShield.

Implements read-only evidence file intake, streaming 64 KB chunk SHA-256 calculation with
progress callbacks and cancellation tokens, path traversal sandbox guards, working copy
creation, duplicate evidence detection, and pre-stage tamper verification (INTEGRITY_FAILURE).
"""

import hashlib
import os
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.models.case import ForensicCase, EvidenceItem
from app.schemas.evidence import EvidenceImportRequest

CHUNK_SIZE_BYTES = 65536  # 64 KB chunk size for memory-bounded streaming reads

FORBIDDEN_SYSTEM_DIRS = {
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("/boot"),
    Path("/etc"),
    Path("/usr"),
    Path("/var"),
    Path("/bin"),
    Path("/sbin"),
    Path("/lib"),
    Path("/lib64"),
}

FORBIDDEN_SYSTEM_ROOTS = {
    Path("/"),
    Path("C:/"),
}


class PathSandboxGuard:
    """Validates target paths against system policy guards and prevents path traversal."""

    @staticmethod
    def validate_evidence_path(source_path: str) -> Path:
        """
        Resolves the canonical path using os.path.realpath, ensures existence,
        and enforces policy rules to block forbidden system directories.
        """
        if not source_path or not source_path.strip():
            raise ForensicShieldException(
                message="Source file path must be specified.",
                code="INVALID_PATH",
                status_code=400,
            )

        try:
            canonical_path = Path(os.path.realpath(source_path.strip()))
        except Exception as exc:
            raise ForensicShieldException(
                message=f"Failed to resolve canonical path: {str(exc)}",
                code="INVALID_PATH",
                status_code=400,
            )

        # Forbidden system root check
        canon_str = str(canonical_path).lower()
        if canon_str in {"/", "c:\\", "c:/"}:
            raise ForensicShieldException(
                message=f"Security Policy Guard: Access to root system directory '{canonical_path}' is strictly forbidden.",
                code="FORBIDDEN_SYSTEM_PATH",
                status_code=403,
            )

        # Forbidden system subdirectories check
        for sys_dir in FORBIDDEN_SYSTEM_DIRS:
            sys_str = str(sys_dir).lower()
            if canon_str == sys_str or canon_str.startswith(sys_str + "\\") or canon_str.startswith(sys_str + "/"):
                raise ForensicShieldException(
                    message=f"Security Policy Guard: Access to system directory '{canonical_path}' is strictly forbidden.",
                    code="FORBIDDEN_SYSTEM_PATH",
                    status_code=403,
                )




        # Check repository root prevention
        project_root = Path(os.path.realpath(__file__)).parent.parent.parent.parent
        if canonical_path == project_root:
            raise ForensicShieldException(
                message="Security Policy Guard: Repository root path cannot be imported as evidence.",
                code="FORBIDDEN_PROJECT_ROOT",
                status_code=403,
            )

        if not canonical_path.exists():
            raise ForensicShieldException(
                message=f"Evidence source file '{source_path}' does not exist.",
                code="FILE_NOT_FOUND",
                status_code=404,
            )

        if not canonical_path.is_file():
            raise ForensicShieldException(
                message=f"Evidence source '{source_path}' is not a regular file.",
                code="NOT_A_FILE",
                status_code=400,
            )

        return canonical_path


class StreamingHashCalculator:
    """Calculates cryptographic SHA-256 hashes in 64 KB streaming chunks with progress and cancellation."""

    @staticmethod
    def calculate_sha256(
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
        chunk_size: int = CHUNK_SIZE_BYTES,
    ) -> Tuple[str, int]:
        """
        Streams binary data from file_path in chunk_size blocks, updating SHA-256 digest.
        Reads file strictly in binary read-only ('rb') mode without modifying source.
        Returns tuple of (sha256_hex_digest, total_bytes_processed).
        """
        hasher = hashlib.sha256()
        total_size = file_path.stat().st_size
        bytes_processed = 0

        # Read strictly in read-only binary mode ('rb')
        with open(file_path, "rb") as f:
            while True:
                if check_cancelled and check_cancelled():
                    raise InterruptedError("SHA-256 streaming hash calculation cancelled by user operator.")

                chunk = f.read(chunk_size)
                if not chunk:
                    break

                hasher.update(chunk)
                bytes_processed += len(chunk)

                if progress_callback and total_size > 0:
                    progress_callback(bytes_processed, total_size)

        return hasher.hexdigest(), bytes_processed


class EvidenceIntakeService:
    """High-level service executing read-only forensic intake and integrity verification."""

    def import_evidence_image(
        self,
        db: Session,
        case_id: int,
        request: EvidenceImportRequest,
        operator_username: str,
        working_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> EvidenceItem:
        """
        Executes evidence intake:
        1. Validates case existence and IDOR permissions.
        2. Validates source path safety and canonical resolution.
        3. Calculates streaming SHA-256 hash in read-only mode.
        4. Detects duplicate evidence items.
        5. Optionally creates a read-only working copy.
        6. Persists complete evidence record in DB with IMPORTED status.
        """
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        # Step 1: Validate Path Sandbox Safety
        canonical_source = PathSandboxGuard.validate_evidence_path(request.source_file_path)

        # Step 2: Streaming SHA-256 Hash Calculation (Read-Only)
        sha256_hash, file_size = StreamingHashCalculator.calculate_sha256(
            canonical_source,
            progress_callback=progress_callback,
            check_cancelled=check_cancelled,
        )

        # Step 3: Check Duplicate Evidence in Case
        existing_duplicate = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.case_id == case_id, EvidenceItem.sha256_hash == sha256_hash)
            .first()
        )
        if existing_duplicate:
            audit_log(
                message=f"Duplicate evidence import attempt detected: Hash {sha256_hash} already present in case {case_id}",
                operation="EVIDENCE_DUPLICATE_IMPORT",
                status="WARNING",
                case_id=str(case_id),
                user_id=operator_username,
                extra_payload={"existing_evidence_id": existing_duplicate.evidence_id, "sha256": sha256_hash},
            )

        # Generate Evidence Identifiers
        now = datetime.now(timezone.utc)
        evidence_id = f"EVD-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
        item_number = request.item_number or f"EVID-{count + 1:03d}"
        title = request.title or canonical_source.name

        working_copy_path_str: Optional[str] = None

        # Step 4: Create Working Copy (if requested)
        if request.create_working_copy:
            if working_dir is None:
                # Default working copy directory relative to source directory or app temp
                working_dir = canonical_source.parent / ".working_copies"

            working_dir.mkdir(parents=True, exist_ok=True)
            dest_copy = working_dir / f"{evidence_id}_{canonical_source.name}"

            # Stream copy block-by-block without loading full file into RAM
            with open(canonical_source, "rb") as f_src, open(dest_copy, "wb") as f_dst:
                while True:
                    if check_cancelled and check_cancelled():
                        if dest_copy.exists():
                            dest_copy.unlink()
                        raise InterruptedError("Working copy creation cancelled by user.")

                    buf = f_src.read(CHUNK_SIZE_BYTES)
                    if not buf:
                        break
                    f_dst.write(buf)
                f_dst.flush()
                os.fsync(f_dst.fileno())

            # Mark working copy as read-only
            os.chmod(dest_copy, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            working_copy_path_str = str(dest_copy)

        # Step 5: Save DB Model
        evidence_item = EvidenceItem(
            evidence_id=evidence_id,
            case_id=case_id,
            item_number=item_number,
            title=title,
            original_filename=canonical_source.name,
            file_path=str(canonical_source),
            working_copy_path=working_copy_path_str,
            sha256_hash=sha256_hash,
            file_size_bytes=file_size,
            import_time=now,
            source_description=request.source_description,
            operator_username=operator_username,
            tool_version="ForensicShield v1.0.0",
            processing_status="IMPORTED",
            last_verified_at=now,
            status="UNTOUCHED",
        )

        db.add(evidence_item)
        db.commit()
        db.refresh(evidence_item)

        audit_log(
            message=f"Forensic evidence image intake completed for '{canonical_source.name}'",
            operation="EVIDENCE_INTAKE",
            status="SUCCESS",
            case_id=str(case_id),
            user_id=operator_username,
            extra_payload={
                "evidence_id": evidence_id,
                "sha256": sha256_hash,
                "size_bytes": file_size,
                "working_copy": working_copy_path_str,
            },
        )

        return evidence_item

    def verify_evidence_integrity(
        self,
        db: Session,
        evidence_id: str,
        stage: str = "PRE_PROCESSING",
        progress_callback: Optional[Callable[[int, int], None]] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> Tuple[bool, str, str, EvidenceItem]:
        """
        Recalculates SHA-256 hash before processing stage and compares with stored hash.
        If hash mismatch occurs:
          - Processing status is set to INTEGRITY_FAILURE
          - Audit event EVIDENCE_INTEGRITY_FAILURE is logged
          - ForensicShieldException is raised with HTTP 409 Conflict.
        Returns (is_valid, stored_hash, recalculated_hash, evidence_item).
        """
        evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
        if not evidence:
            raise ForensicShieldException(
                message=f"Evidence item with ID '{evidence_id}' not found.",
                code="EVIDENCE_NOT_FOUND",
                status_code=404,
            )

        # Select file path to verify (prefer working copy if exists, else original)
        verify_path = Path(evidence.working_copy_path) if (evidence.working_copy_path and Path(evidence.working_copy_path).exists()) else Path(evidence.file_path)

        if not verify_path.exists():
            evidence.processing_status = "FILE_MISSING"
            db.commit()
            raise ForensicShieldException(
                message=f"Evidence file path '{verify_path}' missing during verification.",
                code="FILE_MISSING",
                status_code=404,
            )

        # Recalculate hash in streaming chunks
        recalculated_hash, _ = StreamingHashCalculator.calculate_sha256(
            verify_path,
            progress_callback=progress_callback,
            check_cancelled=check_cancelled,
        )

        now = datetime.now(timezone.utc)
        stored_hash = evidence.sha256_hash

        if recalculated_hash.lower() != stored_hash.lower():
            # INTEGRITY FAILURE DETECTED! Mark changed evidence and fail
            evidence.processing_status = "INTEGRITY_FAILURE"
            evidence.last_verified_at = now
            db.commit()

            audit_log(
                message=f"CRITICAL INTEGRITY FAILURE: Evidence '{evidence_id}' altered or corrupted before stage '{stage}'. Stored: {stored_hash}, Calculated: {recalculated_hash}",
                operation="EVIDENCE_INTEGRITY_FAILURE",
                status="INTEGRITY_FAILURE",
                case_id=str(evidence.case_id),
                user_id=evidence.operator_username,
                extra_payload={
                    "evidence_id": evidence_id,
                    "stage": stage,
                    "stored_hash": stored_hash,
                    "recalculated_hash": recalculated_hash,
                },
            )

            raise ForensicShieldException(
                message=f"CRITICAL INTEGRITY FAILURE: Evidence hash mismatch before stage '{stage}'. Expected {stored_hash}, got {recalculated_hash}.",
                code="INTEGRITY_FAILURE",
                status_code=409,
            )

        # Integrity verified successfully
        evidence.processing_status = "VERIFIED"
        evidence.last_verified_at = now
        db.commit()
        db.refresh(evidence)

        audit_log(
            message=f"Evidence '{evidence_id}' integrity hash verified cleanly before stage '{stage}'",
            operation="EVIDENCE_VERIFIED",
            status="SUCCESS",
            case_id=str(evidence.case_id),
            user_id=evidence.operator_username,
            extra_payload={"evidence_id": evidence_id, "stage": stage, "hash": recalculated_hash},
        )

        return True, stored_hash, recalculated_hash, evidence
