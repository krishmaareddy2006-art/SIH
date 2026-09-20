import os
from typing import List
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForensicShieldException
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
) -> RecoveryScanResponse:
    """
    Executes read-only filesystem-aware recovery scan on evidence image or storage device:
    1. Detects filesystem signature and parses candidate deleted entries.
    2. Validates offset bounds and classifies candidates.
    3. Performs verification and provenance auditing.
    (IDOR & RBAC Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    if scan_req.device_path:
        scan_response = recovery_service.scan_device_recovery(
            db=db,
            case_id=case.id,
            device_path=scan_req.device_path,
            operator_username=current_user.username,
        )
        target_name = scan_req.device_path
    else:
        scan_response = recovery_service.scan_evidence_recovery(
            db=db,
            case_id=case.id,
            evidence_id=scan_req.evidence_id,
            operator_username=current_user.username,
        )
        target_name = scan_req.evidence_id

    audit_log(
        message=f"Filesystem recovery scan executed on '{target_name}' for Case #{case.case_number} by '{current_user.username}'.",
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
) -> RecoveryExtractJobResponse:
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

    target_name = extract_req.device_path or extract_req.evidence_id
    audit_log(
        message=f"Extracted {job_response.successfully_extracted} artifacts from target '{target_name}' into output folder.",
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
) -> List[ExtractedArtifactResponse]:
    """Lists all recovered artifacts attached to an accessible case context. (IDOR Protected)."""
    artifacts = db.query(RecoveredArtifact).filter(RecoveredArtifact.case_id == case.id).all()
    results = []
    for a in artifacts:
        resp = ExtractedArtifactResponse.model_validate(a)
        resp.download_url = f"http://127.0.0.1:8000/api/v1/recovery/{a.artifact_id}/download"
        results.append(resp)
    return results


@router.get("/cases/{case_id}/recovery/artifacts/{artifact_id}/download")
@router.get("/recovery/{artifact_id}/download")
async def download_recovered_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Downloads the physical extracted recovered file with exact original filename and MIME type."""
    import mimetypes
    from urllib.parse import quote

    artifact = db.query(RecoveredArtifact).filter(RecoveredArtifact.artifact_id == artifact_id).first()
    if not artifact or not artifact.output_file_path or not os.path.exists(artifact.output_file_path):
        raise ForensicShieldException("Recovered file not found on disk", code="FILE_NOT_FOUND", status_code=404)

    raw_filename = os.path.basename(artifact.original_path) if artifact.original_path else os.path.basename(artifact.output_file_path)
    clean_filename = raw_filename.replace('"', '').strip()
    media_type = mimetypes.guess_type(clean_filename)[0] or "application/octet-stream"

    encoded_filename = quote(clean_filename)
    headers = {
        "Content-Disposition": f'attachment; filename="{clean_filename}"; filename*=UTF-8\'\'{encoded_filename}',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return FileResponse(
        path=artifact.output_file_path,
        filename=clean_filename,
        media_type=media_type,
        headers=headers,
    )


