"""Evidence Management API Endpoints with IDOR Protection, Stream Verification, and Manifest Exports."""

from typing import List
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import audit_log
from app.core.dependencies import (
    get_current_user,
    require_roles,
    verify_case_access,
    verify_evidence_access,
)
from app.models.auth import User
from app.models.case import ForensicCase, EvidenceItem
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceImportRequest,
    EvidenceIntakeResponse,
    EvidenceVerificationRequest,
    EvidenceVerificationResponse,
    EvidenceManifestJSON,
)
from app.services.evidence_intake import EvidenceIntakeService
from app.services.manifest_exporter import EvidenceManifestExporter

router = APIRouter()
intake_service = EvidenceIntakeService()


@router.post(
    "/cases/{case_id}/evidence/import",
    response_model=EvidenceIntakeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_evidence_image(
    import_req: EvidenceImportRequest,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """
    Executes controlled, read-only forensic image intake:
    1. Validates path traversal guard and forbidden system directories.
    2. Opens source image in binary read-only ('rb') mode.
    3. Calculates SHA-256 in 64 KB streaming chunks.
    4. Creates an immutable read-only working copy.
    5. Stores metadata and audit records.
    (IDOR & RBAC Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    evidence_item = intake_service.import_evidence_image(
        db=db,
        case_id=case.id,
        request=import_req,
        operator_username=current_user.username,
    )

    audit_log(
        message=f"Evidence Image '{evidence_item.evidence_id}' imported into Case #{case.case_number} by '{current_user.username}'.",
        operation="EVIDENCE_IMPORT",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return evidence_item


@router.post(
    "/evidence/{evidence_id}/verify",
    response_model=EvidenceVerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_evidence_integrity(
    verify_req: EvidenceVerificationRequest,
    request: Request,
    evidence: EvidenceItem = Depends(verify_evidence_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recalculates streaming SHA-256 hash before processing stage and compares with stored hash.
    Marks evidence as INTEGRITY_FAILURE and raises 409 Conflict if altered or corrupted.
    (IDOR Protected).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    is_valid, stored_hash, recalculated_hash, updated_item = intake_service.verify_evidence_integrity(
        db=db,
        evidence_id=evidence.evidence_id,
        stage=verify_req.stage,
    )

    return EvidenceVerificationResponse(
        evidence_id=updated_item.evidence_id,
        case_id=updated_item.case_id,
        stage=verify_req.stage,
        is_valid=is_valid,
        expected_hash=stored_hash,
        calculated_hash=recalculated_hash,
        processing_status=updated_item.processing_status,
        verified_at=updated_item.last_verified_at,
        message=f"Integrity check passed cleanly for stage '{verify_req.stage}'.",
    )


@router.get(
    "/cases/{case_id}/evidence/manifest/json",
    response_model=EvidenceManifestJSON,
    status_code=status.HTTP_200_OK,
)
async def export_evidence_manifest_json(
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports structured chain-of-custody evidence manifest in JSON format. (IDOR Protected)."""
    return EvidenceManifestExporter.export_json_manifest(
        db=db,
        case_id=case.id,
        operator_username=current_user.username,
    )


@router.get(
    "/cases/{case_id}/evidence/manifest/csv",
    status_code=status.HTTP_200_OK,
)
async def export_evidence_manifest_csv(
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports RFC 4180 compliant evidence manifest in CSV format. (IDOR Protected)."""
    csv_content = EvidenceManifestExporter.export_csv_manifest(
        db=db,
        case_id=case.id,
    )
    filename = f"evidence_manifest_case_{case.case_number}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post(
    "/cases/{case_id}/evidence",
    response_model=EvidenceIntakeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evidence_item(
    evidence_in: EvidenceCreate,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """Legacy endpoint attaching an evidence metadata reference to a case context. (IDOR Protected)."""
    request_id = getattr(request.state, "request_id", "N/A")
    import_req = EvidenceImportRequest(
        source_file_path=evidence_in.file_path,
        item_number=evidence_in.item_number,
        title=evidence_in.title,
        create_working_copy=False,
    )
    return intake_service.import_evidence_image(
        db=db,
        case_id=case.id,
        request=import_req,
        operator_username=current_user.username,
    )


@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceIntakeResponse])
async def list_case_evidence(
    case: ForensicCase = Depends(verify_case_access),
    db: Session = Depends(get_db),
):
    """Lists evidence items attached to an accessible case context. (IDOR Protected)."""
    return db.query(EvidenceItem).filter(EvidenceItem.case_id == case.id).all()


@router.get("/evidence/{evidence_id}", response_model=EvidenceIntakeResponse)
async def get_evidence_item(
    evidence: EvidenceItem = Depends(verify_evidence_access),
):
    """Gets specific evidence item details. (IDOR Protected)."""
    return evidence
