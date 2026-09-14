"""Forensic Signature-Based File Carving API Endpoints with IDOR & RBAC Controls."""

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
from app.models.case import ForensicCase, CarvedFileArtifact
from app.schemas.carving import (
    CarvingScanRequest,
    CarvingScanResponse,
    CarvedArtifactResponse,
)
from app.services.file_carving import FileCarvingService

router = APIRouter()
carving_service = FileCarvingService()


@router.post(
    "/cases/{case_id}/carving/scan",
    response_model=CarvingScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_file_carving(
    scan_req: CarvingScanRequest,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
) -> CarvingScanResponse:
    """
    Executes signature-based file carving scan:
    1. Computes pre-scan SHA-256 evidence hash.
    2. Scans evidence image in 1 MB bounded overlapping chunks for JPEG, PNG, PDF, ZIP.
    3. Validates format structure and assigns confidence levels (HIGH, MEDIUM, LOW).
    4. Extracts files to output directory and deduplicates identical SHA-256 hashes.
    5. Computes post-scan SHA-256 evidence hash and verifies zero evidence alteration.
    6. Returns performance metrics (bytes_scanned, candidates_found, validated_files, elapsed_time_ms).
    (IDOR & RBAC Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    scan_response = carving_service.execute_carving_scan(
        db=db,
        case_id=case.id,
        request=scan_req,
        operator_username=current_user.username,
    )

    target_name = scan_req.device_path or scan_req.evidence_id
    audit_log(
        message=f"File carving scan executed on '{target_name}' for Case #{case.case_number} by '{current_user.username}'.",
        operation="CARVING_SCAN_API",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return scan_response


@router.get(
    "/cases/{case_id}/carving/results",
    response_model=List[CarvedArtifactResponse],
    status_code=status.HTTP_200_OK,
)
async def list_carved_artifacts(
    case: ForensicCase = Depends(verify_case_access),
    db: Session = Depends(get_db),
) -> List[CarvedArtifactResponse]:
    """Lists all carved file artifacts attached to an accessible case context. (IDOR Protected)."""
    return db.query(CarvedFileArtifact).filter(CarvedFileArtifact.case_id == case.id).all()


@router.get("/carving/{carved_id}/download")
async def download_carved_artifact(
    carved_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Downloads the physical extracted carved file with exact filename and MIME type."""
    import mimetypes
    from urllib.parse import quote

    artifact = db.query(CarvedFileArtifact).filter(CarvedFileArtifact.carved_id == carved_id).first()
    if not artifact or not artifact.output_file_path or not os.path.exists(artifact.output_file_path):
        raise ForensicShieldException("Carved file not found on disk", code="FILE_NOT_FOUND", status_code=404)

    raw_filename = os.path.basename(artifact.output_file_path)
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



