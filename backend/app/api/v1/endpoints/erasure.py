"""Controlled File & Folder Erasure API Endpoints."""

from fastapi import APIRouter, Depends, Request
from app.core.logging import audit_log
from app.core.dependencies import require_roles
from app.models.auth import User
from app.schemas.erasure import (
    ErasureExecuteRequest,
    ErasureReport,
    ErasureTokenRequest,
    ErasureTokenResponse,
)
from app.services.file_erasure import (
    ConfirmationTokenManager,
    ControlledErasureService,
    PathSandboxGuard,
)

from fastapi import APIRouter, Depends, Request, Query
import os
import hashlib
from pathlib import Path
from app.core.exceptions import ForensicShieldException

router = APIRouter()


@router.get("/analyze")
async def analyze_file_erasure(
    path: str = Query(..., description="Target file or folder path to analyze"),
    current_user: User = Depends(require_roles(["Administrator", "Operator"])),
):
    """Analyzes target path size and computes pre-erasure SHA-256 for audit tracking."""
    if not path or not path.strip():
        raise ForensicShieldException("Path must be specified", code="INVALID_PATH", status_code=400)

    try:
        canonical_target = Path(os.path.realpath(path.strip()))
    except Exception as exc:
        raise ForensicShieldException(f"Invalid path syntax: {str(exc)}", code="INVALID_PATH", status_code=400)

    if not canonical_target.exists():
        raise ForensicShieldException(
            f"Target file or folder '{path}' does not exist on disk.",
            code="FILE_NOT_FOUND",
            status_code=404,
        )

    is_file = canonical_target.is_file()
    pre_hash = "DIRECTORY_COLLECTION"

    if is_file:
        size = canonical_target.stat().st_size
        h = hashlib.sha256()
        with open(canonical_target, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        pre_hash = h.hexdigest()
    else:
        size = sum(f.stat().st_size for f in canonical_target.rglob("*") if f.is_file())

    _, req_str = ConfirmationTokenManager.generate_token(str(canonical_target), current_user.username)

    return {
        "target_path": str(canonical_target),
        "size_bytes": size,
        "is_file": is_file,
        "pre_erasure_sha256": pre_hash,
        "pre_hash": pre_hash,
        "confirmation_token_required": f"CONFIRM ERASE {path.strip()}",
        "status": "ANALYZE_SUCCESS",
    }


@router.post("/token", response_model=ErasureTokenResponse)
async def generate_erasure_confirmation_token(
    token_req: ErasureTokenRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Operator"])),
):
    """
    Validates target sandbox path and generates a unique confirmation token for sensitive file erasure.
    """
    request_id = getattr(request.state, "request_id", "N/A")

    # Validate sandbox bounds first
    canonical_target, canonical_root = PathSandboxGuard.validate_sandbox_target(
        token_req.target_path, token_req.approved_root
    )

    token_hash, req_str = ConfirmationTokenManager.generate_token(
        str(canonical_target), current_user.username
    )

    audit_log(
        message=f"Erasure confirmation token generated for target '{canonical_target}' by user '{current_user.username}'.",
        operation="ERASURE_TOKEN_REQUEST",
        status="SUCCESS",
        request_id=request_id,
        user_id=current_user.username,
        extra_payload={
            "target_path": str(canonical_target),
            "approved_root": str(canonical_root),
        },
    )

    return ErasureTokenResponse(
        target_path=str(canonical_target),
        approved_root=str(canonical_root),
        confirmation_token=token_hash,
        required_confirmation_string=req_str,
        expires_in_seconds=900,
    )


@router.post("/execute", response_model=ErasureReport)
async def execute_file_erasure(
    erasure_req: ErasureExecuteRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Operator"])),
):
    """
    Executes dry-run preview or controlled live logical file/folder erasure.
    Requires Administrator or Operator role, sandbox path validation,
    and matching confirmation token string for live execution.
    """
    request_id = getattr(request.state, "request_id", "N/A")

    erasure_service = ControlledErasureService()
    report = erasure_service.execute_erasure(
        erasure_req, user_id=current_user.username
    )

    audit_log(
        message=f"File erasure operation '{report.execution_id}' executed by '{current_user.username}' (Dry-Run: {report.dry_run}, Status: {report.status}, Items: {report.total_items}, Erased: {report.erased_items}). Reason: {erasure_req.reason}",
        operation="FILE_ERASURE_EXECUTE",
        status=report.status,
        request_id=request_id,
        user_id=current_user.username,
        extra_payload={
            "execution_id": report.execution_id,
            "dry_run": report.dry_run,
            "target_path": report.target_path,
            "approved_root": report.approved_root,
            "total_bytes_erased": report.total_bytes_erased,
            "reason": erasure_req.reason,
        },
    )

    return report
