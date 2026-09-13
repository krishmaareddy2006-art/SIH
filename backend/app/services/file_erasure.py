"""Controlled Secure File & Folder Erasure Engine for ForensicShield.

Implements sandbox-isolated logical file erasure, fsync-flushed multi-pass overwriting,
path traversal guards, symlink escape prevention, confirmation token validation,
read-only permission recovery, and per-item status audit reports.
"""

import hmac
import os
import stat
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Set

from app.core.config import settings
from app.core.exceptions import ForensicShieldException
from app.schemas.erasure import (
    ErasureExecuteRequest,
    ErasureItemResult,
    ErasureReport,
)

CHUNK_SIZE_BYTES = 65536  # 64 KB chunk size for bounded memory usage

# Hardcoded forbidden system paths to prevent catastrophic system damage
FORBIDDEN_SYSTEM_PATHS = {
    "/",
    "/boot",
    "/etc",
    "/usr",
    "/var",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "C:\\",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
}


class PathSandboxGuard:
    """Validates target paths against approved root sandboxes and prevents path traversal."""

    @staticmethod
    def validate_sandbox_target(target_path: str, approved_root: str) -> Tuple[Path, Path]:
        """
        Ensures that target_path and approved_root exist, canonicalizes them via os.path.realpath,
        verifies target_path is strictly within approved_root, and rejects system roots.
        """
        if not target_path or not approved_root:
            raise ForensicShieldException(
                message="Target path and approved root must be specified.",
                code="INVALID_PATH",
                status_code=400,
            )

        try:
            canonical_target = Path(os.path.realpath(target_path.strip()))
            canonical_root = Path(os.path.realpath(approved_root.strip()))
        except Exception as exc:
            raise ForensicShieldException(
                message=f"Failed to resolve canonical path: {str(exc)}",
                code="INVALID_PATH",
                status_code=400,
            )

        if not canonical_root.exists() or not canonical_root.is_dir():
            raise ForensicShieldException(
                message=f"Approved root directory '{approved_root}' does not exist.",
                code="ROOT_NOT_FOUND",
                status_code=404,
            )

        # Check forbidden system roots
        if str(canonical_root) in FORBIDDEN_SYSTEM_PATHS or str(canonical_target) in FORBIDDEN_SYSTEM_PATHS:
            raise ForensicShieldException(
                message="Security Policy Guard: Target path is a protected system root. Erasure blocked.",
                code="FORBIDDEN_SYSTEM_ROOT",
                status_code=403,
            )

        # Ensure approved root is not project repository root
        project_root = Path(os.path.realpath(__file__)).parent.parent.parent.parent
        if canonical_target == project_root or canonical_root == project_root:
            raise ForensicShieldException(
                message="Security Policy Guard: Source code repository root cannot be targeted for erasure.",
                code="FORBIDDEN_PROJECT_ROOT",
                status_code=403,
            )

        # Path Traversal Check using os.path.commonpath
        try:
            common = os.path.commonpath([str(canonical_target), str(canonical_root)])
            if common != str(canonical_root):
                raise ForensicShieldException(
                    message="Path Traversal Guard: Target path is outside approved root sandbox.",
                    code="PATH_TRAVERSAL_BLOCKED",
                    status_code=403,
                )
        except ValueError:
            # Different drives on Windows (e.g. C: vs D:)
            raise ForensicShieldException(
                message="Path Traversal Guard: Target path resides on a different drive than approved root.",
                code="PATH_TRAVERSAL_BLOCKED",
                status_code=403,
            )

        if not canonical_target.exists() and not os.path.islink(str(canonical_target)):
            raise ForensicShieldException(
                message=f"Target path '{target_path}' does not exist.",
                code="TARGET_NOT_FOUND",
                status_code=404,
            )

        return canonical_target, canonical_root


class ConfirmationTokenManager:
    """Generates and verifies typed confirmation tokens for sensitive file erasures."""

    @staticmethod
    def generate_token(target_path: str, user_id: str = "operator") -> Tuple[str, str]:
        """Generates a unique confirmation token and formatted requirement string."""
        canonical_target = os.path.realpath(target_path.strip())
        token_src = f"{canonical_target}:{user_id}:{settings.SECRET_KEY}"
        token_hash = hmac.new(settings.SECRET_KEY.encode("utf-8"), token_src.encode("utf-8"), "sha256").hexdigest()[:8]
        req_str = f"CONFIRM:{canonical_target}:{token_hash}"
        return token_hash, req_str

    @staticmethod
    def verify_token(target_path: str, user_confirmation: Optional[str], user_id: str = "operator") -> bool:
        """Verifies the typed confirmation string matches CONFIRM:<target>:<hash>."""
        if not user_confirmation:
            return False
        _, expected_req = ConfirmationTokenManager.generate_token(target_path, user_id)
        return hmac.compare_digest(user_confirmation.strip(), expected_req.strip())


class LogicalFileEraser:
    """Performs chunked multi-pass logical file overwriting with fsync disk flushing."""

    @staticmethod
    def overwrite_and_unlink(
        file_path: Path,
        passes: int = 1,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> int:
        """
        Overwrites file data with zero/pattern passes, calls fsync, and unlinks file.
        Recovers read-only permissions if file is write-protected.
        Returns bytes written.
        """
        if not file_path.exists() and not os.path.islink(file_path):
            return 0

        file_size = file_path.stat().st_size

        # Handle read-only files by restoring write permission
        if not os.access(file_path, os.W_OK):
            os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)

        if file_size > 0:
            patterns = [b"\x00"]
            if passes >= 3:
                patterns = [b"\x00", b"\xFF", b"RANDOM"]

            for pass_num, pattern in enumerate(patterns, start=1):
                if check_cancelled and check_cancelled():
                    raise InterruptedError("Erasure process cancelled by user.")

                with open(file_path, "r+b") as f:
                    f.seek(0)
                    bytes_remaining = file_size

                    while bytes_remaining > 0:
                        if check_cancelled and check_cancelled():
                            raise InterruptedError("Erasure process cancelled by user.")

                        chunk_len = min(CHUNK_SIZE_BYTES, bytes_remaining)
                        if pattern == b"RANDOM":
                            chunk = os.urandom(chunk_len)
                        else:
                            chunk = pattern * chunk_len

                        f.write(chunk)
                        bytes_remaining -= chunk_len

                    f.flush()
                    os.fsync(f.fileno())

        # Unlink file after overwrite passes
        os.unlink(file_path)
        return file_size


class ControlledErasureService:
    """High-level service executing dry-run previews or controlled live file/folder erasures."""

    def execute_erasure(
        self,
        request: ErasureExecuteRequest,
        user_id: str = "operator",
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> ErasureReport:
        """Executes dry-run preview or live logical file/folder erasure."""
        start_time = time.time()
        execution_id = f"erase-{uuid.uuid4().hex[:8]}"

        # 1. Validate Target Path against Approved Root Sandbox
        canonical_target, canonical_root = PathSandboxGuard.validate_sandbox_target(
            request.target_path, request.approved_root
        )

        # 2. Token Confirmation Check (Required for live non-dry-run execution)
        if not request.dry_run and not settings.SAFE_MODE:
            if not ConfirmationTokenManager.verify_token(str(canonical_target), request.confirmation_token, user_id):
                _, expected_req = ConfirmationTokenManager.generate_token(str(canonical_target), user_id)
                raise ForensicShieldException(
                    message=f"Typed confirmation token mismatch. Required string: '{expected_req}'",
                    code="INVALID_CONFIRMATION_TOKEN",
                    status_code=400,
                )

        items_results: List[ErasureItemResult] = []
        total_bytes_erased = 0
        erased_count = 0
        skipped_count = 0
        failed_count = 0

        # Collect targets in depth-first order
        targets_to_process: List[Tuple[Path, str]] = []  # (path, item_type)

        if os.path.islink(canonical_target):
            targets_to_process.append((canonical_target, "SYMLINK"))
        elif canonical_target.is_file():
            targets_to_process.append((canonical_target, "FILE"))
        elif canonical_target.is_dir():
            # Recursive directory tree collection without following symlinks
            dirs_to_remove: List[Path] = []
            for root, dirs, files in os.walk(canonical_target, topdown=False, followlinks=False):
                current_root = Path(root)
                for f in files:
                    fp = current_root / f
                    if os.path.islink(fp):
                        targets_to_process.append((fp, "SYMLINK"))
                    else:
                        st = fp.stat(follow_symlinks=False)
                        if stat.S_ISREG(st.st_mode):
                            targets_to_process.append((fp, "FILE"))
                        else:
                            targets_to_process.append((fp, "SPECIAL"))

                for d in dirs:
                    dp = current_root / d
                    if os.path.islink(dp):
                        targets_to_process.append((dp, "SYMLINK"))
                    else:
                        dirs_to_remove.append(dp)

            for d in dirs_to_remove:
                targets_to_process.append((d, "DIRECTORY"))
            targets_to_process.append((canonical_target, "DIRECTORY"))

        # Process collected targets
        is_simulated = request.dry_run or settings.SAFE_MODE

        for item_path, item_type in targets_to_process:
            if check_cancelled and check_cancelled():
                items_results.append(
                    ErasureItemResult(
                        path=str(item_path),
                        item_type=item_type,
                        status="SKIPPED",
                        message="Skipped due to user cancellation request.",
                    )
                )
                skipped_count += 1
                continue

            # Symlink Policy: Do not follow symlinks, unlink as link node
            if item_type == "SYMLINK":
                if is_simulated:
                    items_results.append(
                        ErasureItemResult(
                            path=str(item_path),
                            item_type="SYMLINK",
                            status="PLANNED",
                            message="[DRY-RUN] Symlink node will be unlinked without following target.",
                        )
                    )
                    erased_count += 1
                else:
                    try:
                        os.unlink(item_path)
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="SYMLINK",
                                status="ERASED",
                                message="Symlink node unlinked.",
                            )
                        )
                        erased_count += 1
                    except Exception as exc:
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="SYMLINK",
                                status="FAILED",
                                message=f"Failed to unlink symlink: {str(exc)}",
                            )
                        )
                        failed_count += 1

            elif item_type == "SPECIAL":
                items_results.append(
                    ErasureItemResult(
                        path=str(item_path),
                        item_type="SPECIAL",
                        status="SKIPPED",
                        message="Special IPC/device file skipped for safety.",
                    )
                )
                skipped_count += 1

            elif item_type == "FILE":
                size = item_path.stat(follow_symlinks=False).st_size if item_path.exists() else 0
                if is_simulated:
                    items_results.append(
                        ErasureItemResult(
                            path=str(item_path),
                            item_type="FILE",
                            status="PLANNED",
                            size_bytes=size,
                            passes_completed=0,
                            message=f"[DRY-RUN] Logical overwrite ({request.overwrite_passes} pass) and unlink planned.",
                        )
                    )
                    erased_count += 1
                    total_bytes_erased += size
                else:
                    try:
                        bytes_erased = LogicalFileEraser.overwrite_and_unlink(
                            item_path, passes=request.overwrite_passes, check_cancelled=check_cancelled
                        )
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="FILE",
                                status="ERASED",
                                size_bytes=bytes_erased,
                                passes_completed=request.overwrite_passes,
                                message="Logical overwrite and fsync unlink completed.",
                            )
                        )
                        erased_count += 1
                        total_bytes_erased += bytes_erased
                    except InterruptedError:
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="FILE",
                                status="SKIPPED",
                                size_bytes=size,
                                message="Erasure interrupted by user cancellation.",
                            )
                        )
                        skipped_count += 1
                        break
                    except Exception as exc:
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="FILE",
                                status="FAILED",
                                size_bytes=size,
                                message=f"Failed to erase file: {str(exc)}",
                            )
                        )
                        failed_count += 1

            elif item_type == "DIRECTORY":
                if is_simulated:
                    items_results.append(
                        ErasureItemResult(
                            path=str(item_path),
                            item_type="DIRECTORY",
                            status="PLANNED",
                            message="[DRY-RUN] Directory removal planned after file contents erasure.",
                        )
                    )
                    erased_count += 1
                else:
                    try:
                        if item_path.exists():
                            os.rmdir(item_path)
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="DIRECTORY",
                                status="ERASED",
                                message="Directory removed.",
                            )
                        )
                        erased_count += 1
                    except Exception as exc:
                        items_results.append(
                            ErasureItemResult(
                                path=str(item_path),
                                item_type="DIRECTORY",
                                status="FAILED",
                                message=f"Failed to remove directory: {str(exc)}",
                            )
                        )
                        failed_count += 1

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        report_status = "SIMULATED" if is_simulated else ("COMPLETED" if failed_count == 0 else "PARTIAL_SUCCESS")

        return ErasureReport(
            execution_id=execution_id,
            target_path=str(canonical_target),
            approved_root=str(canonical_root),
            dry_run=is_simulated,
            safe_mode_active=settings.SAFE_MODE,
            overwrite_passes=request.overwrite_passes,
            total_items=len(items_results),
            erased_items=erased_count,
            skipped_items=skipped_count,
            failed_items=failed_count,
            total_bytes_erased=total_bytes_erased,
            execution_time_ms=elapsed_ms,
            status=report_status,
            items=items_results,
        )
