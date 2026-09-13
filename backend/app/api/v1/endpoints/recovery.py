"""Forensic Filesystem Recovery API Endpoints with IDOR & RBAC Controls."""

from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import audit_log
from app.core.dependencies import (
    get_current_user,
    require_roles,
    verify_case_access,
)
from app.models.auth import User
from app.models.case import ForensicCase, RecoveredArtifact
from app.schemas.recovery import (
    RecoveryScanRequest,
    RecoveryScanResponse,
    RecoveryExtractRequest,
    RecoveryExtractJobResponse,
    ExtractedArtifactResponse,
)
from app.services.filesystem_recovery import FilesystemRecoveryService

router = APIRouter()
recovery_service = FilesystemRecoveryService()


@router.post(
    "/cases/{case_id}/recovery/scan",
    response_model=RecoveryScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_filesystem_recovery(
    scan_req: RecoveryScanRequest,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """
    Executes read-only filesystem-aware recovery scan:
    1. Performs pre-scan SHA-256 evidence verification.
    2. Opens evidence image in binary read-only ('rb') mode.
    3. Detects filesystem signature and parses candidate deleted entries.
    4. Validates offset bounds and classifies candidates.
    5. Performs post-scan SHA-256 evidence verification.
    (IDOR & RBAC Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    scan_response = recovery_service.scan_evidence_recovery(
        db=db,
        case_id=case.id,
        evidence_id=scan_req.evidence_id,
        operator_username=current_user.username,
    )

    audit_log(
        message=f"Filesystem recovery scan executed on evidence '{scan_req.evidence_id}' for Case #{case.case_number} by '{current_user.username}'.",
        operation="RECOVERY_SCAN_API",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return scan_response


@router.post(
    "/cases/{case_id}/recovery/extract",
    response_model=RecoveryExtractJobResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_recovery_artifacts(
    extract_req: RecoveryExtractRequest,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """
    Extracts selected recovery candidate data to output directory with complete provenance records.
    (IDOR & RBAC Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    job_response = recovery_service.extract_recovery_candidates(
        db=db,
        case_id=case.id,
        request=extract_req,
        operator_username=current_user.username,
    )

    audit_log(
        message=f"Extracted {job_response.successfully_extracted} artifacts from evidence '{extract_req.evidence_id}' into output folder.",
        operation="RECOVERY_EXTRACT_API",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return job_response


@router.get(
    "/cases/{case_id}/recovery/results",
    response_model=List[ExtractedArtifactResponse],
    status_code=status.HTTP_200_OK,
)
async def list_recovered_artifacts(
    case: ForensicCase = Depends(verify_case_access),
    db: Session = Depends(get_db),
):
    """Lists all recovered artifacts attached to an accessible case context. (IDOR Protected)."""
    return db.query(RecoveredArtifact).filter(RecoveredArtifact.case_id == case.id).all()
