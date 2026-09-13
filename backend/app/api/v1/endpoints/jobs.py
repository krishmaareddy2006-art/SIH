"""Forensic Job Management API Endpoints for ForensicShield.

Provides persistent Job submission, status tracking, duplicate active job blocking,
progress reporting, cancellation checkpoints, state machine transitions, and startup recovery.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_roles, verify_case_access
from app.core.exceptions import ForensicShieldException
from app.core.security import verify_destructive_allowed
from app.models.auth import User
from app.models.case import ForensicCase
from app.models.job import JobRecord
from app.schemas.job_management import (
    JobCancelResponse,
    JobDetailResponse,
    JobRecoveryResponse,
    JobSubmitRequest,
)
from app.schemas.jobs import JobResponse, SensitiveJobRequest
from app.services.job_management_service import JobManagementService

router = APIRouter()
job_service = JobManagementService()

EXPLICIT_CONFIRMATION_STRING = "CONFIRM_SENSITIVE_ACTION"


def validate_sensitive_action_payload(job_req: SensitiveJobRequest) -> None:
    """Server-side validation enforcing reason length and explicit confirmation string match."""
    if job_req.explicit_confirmation != EXPLICIT_CONFIRMATION_STRING:
        raise ForensicShieldException(
            message=f"Invalid confirmation string. You must pass explicit_confirmation='{EXPLICIT_CONFIRMATION_STRING}'.",
            code="INVALID_CONFIRMATION",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(job_req.reason.strip()) < 5:
        raise ForensicShieldException(
            message="Audit compliance failure: Justification reason must be at least 5 characters long.",
            code="INVALID_REASON",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/", response_model=List[JobDetailResponse], status_code=status.HTTP_200_OK)
def list_jobs(
    case_id: Optional[int] = Query(None, description="Filter jobs by forensic case ID"),
    job_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    job_type: Optional[str] = Query(None, alias="type", description="Filter by job type"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves paginated Job records with case/status/type filtering."""
    query = db.query(JobRecord)
    if case_id is not None:
        query = query.filter(JobRecord.case_id == case_id)
    if job_status:
        query = query.filter(JobRecord.status == job_status)
    if job_type:
        query = query.filter(JobRecord.type == job_type.upper())

    jobs = query.order_by(JobRecord.id.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobDetailResponse, status_code=status.HTTP_200_OK)
def get_job_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves detailed Job record status by job_id."""
    job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
    if not job:
        raise ForensicShieldException(
            message=f"Job with ID '{job_id}' not found.",
            code="JOB_NOT_FOUND",
            status_code=404,
        )
    return job


@router.post("/{job_id}/cancel", response_model=JobCancelResponse, status_code=status.HTTP_200_OK)
def cancel_job(
    job_id: str,
    current_user: User = Depends(require_roles(["Administrator", "Operator"])),
    db: Session = Depends(get_db),
):
    """Requests cancellation of a queued or running background job."""
    job = job_service.request_job_cancellation(db=db, job_id=job_id, operator_username=current_user.username)
    return JobCancelResponse(
        job_id=job.job_id,
        status=job.status,
        message=f"Cancellation requested for job '{job_id}'. Execution will abort at next checkpoint.",
    )


@router.post("/recover-stale", response_model=JobRecoveryResponse, status_code=status.HTTP_200_OK)
def recover_stale_jobs(
    current_user: User = Depends(require_roles(["Administrator"])),
    db: Session = Depends(get_db),
):
    """Triggers server startup state recovery for interrupted running or cancelling jobs."""
    recovered, aborted = job_service.recover_stale_jobs_on_startup(db=db)
    return JobRecoveryResponse(
        recovered_jobs_count=recovered,
        aborted_jobs_count=aborted,
        message=f"State recovery complete. {recovered} stale jobs recovered and transitioned to ABORTED.",
    )


# ---------------------------------------------------------
# Legacy Endpoint Adaptations
# ---------------------------------------------------------

@router.post("/sanitization", response_model=JobResponse)
async def start_sanitization_job(
    job_req: SensitiveJobRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Operator"])),
    db: Session = Depends(get_db),
):
    """Executes drive/partition sanitization job under SAFE_MODE policy."""
    validate_sensitive_action_payload(job_req)
    case: ForensicCase = verify_case_access(job_req.case_id, request, current_user, db)
    verify_destructive_allowed(simulate=job_req.simulate)

    # Check duplicate active job prevention
    job_service.prevent_duplicate_active_job(db, target_identifier=job_req.target_identifier, job_type="SANITIZATION")

    def mock_sanitization_task(job_id: str, db: Session, check_cancellation):
        check_cancellation()
        job_service.update_job_progress(db, job_id, 25.0, "Preflight safety gate inspection", is_exact=True)
        check_cancellation()
        job_service.update_job_progress(db, job_id, 50.0, "Simulating overwrite passes", is_exact=False)
        check_cancellation()
        job_service.update_job_progress(db, job_id, 100.0, "Dry-run sanitization completed", is_exact=True)

    submit_req = JobSubmitRequest(
        case_id=case.id,
        type="SANITIZATION",
        target_identifier=job_req.target_identifier,
        reason=job_req.reason,
        explicit_confirmation=job_req.explicit_confirmation,
        simulate=job_req.simulate,
    )

    job_rec = job_service.submit_job(
        db=db, request=submit_req, operator_username=current_user.username, task_func=mock_sanitization_task
    )

    return JobResponse(
        job_id=job_rec.job_id,
        job_type="SANITIZATION",
        case_id=case.id,
        target_identifier=job_req.target_identifier,
        status="SIMULATED" if settings.SAFE_MODE else "COMPLETED",
        safe_mode_active=settings.SAFE_MODE,
        preview=f"[SAFE_MODE PREVIEW] Drive sanitization dry-run on '{job_req.target_identifier}' queued ({job_rec.job_id}). Zero bytes overwritten.",
        execution_details=f"Job queued for Case #{case.case_number} by operator '{current_user.username}'. Justification: '{job_req.reason}'.",
    )


@router.post("/recovery", response_model=JobResponse)
async def start_recovery_job(
    job_req: SensitiveJobRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Investigator", "Operator"])),
    db: Session = Depends(get_db),
):
    """Executes evidence recovery job."""
    validate_sensitive_action_payload(job_req)
    case: ForensicCase = verify_case_access(job_req.case_id, request, current_user, db)
    verify_destructive_allowed(simulate=job_req.simulate)

    # Check duplicate active job prevention
    job_service.prevent_duplicate_active_job(db, target_identifier=job_req.target_identifier, job_type="RECOVERY")

    def mock_recovery_task(job_id: str, db: Session, check_cancellation):
        check_cancellation()
        job_service.update_job_progress(db, job_id, 30.0, "Parsing directory extents", is_exact=False)
        check_cancellation()
        job_service.update_job_progress(db, job_id, 75.0, "Extracting candidate entries", is_exact=False)
        check_cancellation()
        job_service.update_job_progress(db, job_id, 100.0, "Recovery completed", is_exact=True)

    submit_req = JobSubmitRequest(
        case_id=case.id,
        type="RECOVERY",
        target_identifier=job_req.target_identifier,
        reason=job_req.reason,
        explicit_confirmation=job_req.explicit_confirmation,
        simulate=job_req.simulate,
    )

    job_rec = job_service.submit_job(
        db=db, request=submit_req, operator_username=current_user.username, task_func=mock_recovery_task
    )

    return JobResponse(
        job_id=job_rec.job_id,
        job_type="RECOVERY",
        case_id=case.id,
        target_identifier=job_req.target_identifier,
        status="SIMULATED" if settings.SAFE_MODE else "COMPLETED",
        safe_mode_active=settings.SAFE_MODE,
        preview=f"[SAFE_MODE PREVIEW] Evidence recovery dry-run on '{job_req.target_identifier}' queued ({job_rec.job_id}).",
        execution_details=f"Recovery job queued for Case #{case.case_number} by investigator '{current_user.username}'. Justification: '{job_req.reason}'.",
    )
