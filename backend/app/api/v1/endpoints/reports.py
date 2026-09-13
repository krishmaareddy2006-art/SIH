"""Forensic Reporting & Compliance REST API Endpoints for ForensicShield.

Provides endpoints for:
1. Report generation (PDF & JSON manifest)
2. Case report preview data
3. Authorization-guarded report download endpoints (PDF and JSON) with IDOR protection & path safety.
"""

import hashlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    require_roles,
    verify_case_access,
)
from app.core.logging import audit_log
from app.models.auth import User
from app.models.case import ForensicCase
from app.schemas.reporting import (
    ForensicReportRequest,
    ForensicReportResponse,
    ReportPreviewResponse,
    ReportSummary,
    StatusClassificationCounts,
)
from app.services.reporting_service import ForensicReportService

router = APIRouter()
reporting_service = ForensicReportService()


@router.post(
    "/cases/{case_id}/reports/generate",
    response_model=ForensicReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_forensic_report(
    case_id: int,
    request: Request,
    report_req: Optional[ForensicReportRequest] = None,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """
    Generates court-compliant PDF report and machine-readable JSON manifest for a case.
    Protected with RBAC & IDOR guards. Calculates report SHA-256 digests and appends
    event into tamper-evident audit log chain.
    """
    request_id = getattr(request.state, "request_id", "N/A")

    report_response = reporting_service.generate_case_report(
        db=db,
        case_id=case.id,
        operator_username=current_user.username,
        request_params=report_req,
    )

    audit_log(
        message=f"Forensic Report '{report_response.report_id}' generated for Case #{case.case_number} by '{current_user.username}'.",
        operation="REPORT_GENERATION",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return report_response


@router.get(
    "/cases/{case_id}/reports/preview",
    response_model=ReportPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_forensic_report(
    case_id: int,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves summary preview data for case report generation without building files.
    Protected with IDOR guard.
    """
    case_data = reporting_service.collect_case_data(db, case_id=case.id)

    summary_obj = ReportSummary(**case_data["summary"])
    class_obj = StatusClassificationCounts(**case_data["classifications"])

    return ReportPreviewResponse(
        case_id=case.id,
        case_number=case.case_number,
        case_title=reporting_service.enforce_compliance_language(case.title),
        summary=summary_obj,
        classifications=class_obj,
        audit_chain_valid=case_data["chain_verification"].is_valid,
        evidence_count=len(case_data["evidence_items"]),
        artifact_count=len(case_data["recovered_artifacts"]) + len(case_data["carved_artifacts"]),
    )


@router.get(
    "/cases/{case_id}/reports/{report_id}/download/pdf",
    status_code=status.HTTP_200_OK,
)
async def download_report_pdf(
    case_id: int,
    report_id: str,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Downloads the PDF report for a specified case and report ID.
    Enforces IDOR case authorization and path traversal prevention.
    Attaches X-Report-SHA256 digest header.
    """
    # Sanitize report_id against path traversal
    safe_report_id = Path(report_id).name
    pdf_path = Path("reports") / f"case_{case.id}" / f"{safe_report_id}_report.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report '{report_id}' for Case #{case_id} not found.",
        )

    pdf_bytes = pdf_path.read_bytes()
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()

    headers = {
        "Content-Disposition": f'attachment; filename="{safe_report_id}_report.pdf"',
        "X-Report-SHA256": sha256_hash,
    }

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


@router.get(
    "/cases/{case_id}/reports/{report_id}/download/json",
    status_code=status.HTTP_200_OK,
)
async def download_report_json(
    case_id: int,
    report_id: str,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Downloads the machine-readable JSON manifest for a specified case and report ID.
    Enforces IDOR case authorization and path traversal prevention.
    Attaches X-Report-SHA256 digest header.
    """
    safe_report_id = Path(report_id).name
    json_path = Path("reports") / f"case_{case.id}" / f"{safe_report_id}_manifest.json"

    if not json_path.exists() or not json_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JSON manifest '{report_id}' for Case #{case_id} not found.",
        )

    json_bytes = json_path.read_bytes()
    sha256_hash = hashlib.sha256(json_bytes).hexdigest()

    headers = {
        "Content-Disposition": f'attachment; filename="{safe_report_id}_manifest.json"',
        "X-Report-SHA256": sha256_hash,
    }

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers=headers,
    )
