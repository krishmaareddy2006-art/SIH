"""Safe Storage Sanitization Orchestration API Endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import audit_log
from app.core.dependencies import require_roles
from app.models.auth import User
from app.schemas.sanitization import (
    SanitizationExecuteRequest,
    SanitizationPreflightRequest,
    SanitizationPreflightReport,
    SanitizationResultReport,
    SanitizationTokenRequest,
    SanitizationTokenResponse,
)
from app.services.sanitization_orchestrator import SanitizationOrchestrator
from app.services.sanitization_safety_gate import SanitizationSafetyGate

router = APIRouter()


@router.post("/preflight", response_model=SanitizationPreflightReport)
async def get_sanitization_preflight_report(
    preflight_req: SanitizationPreflightRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator"])),
    db: Session = Depends(get_db),
):
    """
    Generates a preflight sanitization inspection report.
    Evaluates 8-Point Safety Gate, target classification (HDD/SSD/NVMe/USB), method recommendation, and dry-run plan.
    (Administrator role required).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    report = SanitizationOrchestrator.generate_preflight_report(
        device_path=preflight_req.device_path,
        case_id=preflight_req.case_id,
        current_user=current_user,
        db=db,
    )

    audit_log(
        message=f"Preflight sanitization inspection requested by '{current_user.username}' for device '{report.canonical_path}' (Passed Gate: {report.safety_gate_passed}).",
        operation="SANITIZATION_PREFLIGHT",
        status="PASSED" if report.safety_gate_passed else "REJECTED",
        request_id=request_id,
        case_id=str(preflight_req.case_id),
        user_id=current_user.username,
    )

    return report


@router.post("/token", response_model=SanitizationTokenResponse)
async def generate_sanitization_token(
    token_req: SanitizationTokenRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator"])),
):
    """
    Generates a unique confirmation token for device sanitization.
    (Administrator role required).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    token_hash, req_str = SanitizationSafetyGate.generate_sanitization_token(
        token_req.device_path, token_req.case_id, current_user.username
    )

    audit_log(
        message=f"Sanitization confirmation token requested for device '{token_req.device_path}' (Case #{token_req.case_id}) by '{current_user.username}'.",
        operation="SANITIZATION_TOKEN_REQUEST",
        status="SUCCESS",
        request_id=request_id,
        case_id=str(token_req.case_id),
        user_id=current_user.username,
    )

    return SanitizationTokenResponse(
        device_path=token_req.device_path,
        case_id=token_req.case_id,
        confirmation_token=token_hash,
        required_confirmation_string=req_str,
        expires_in_seconds=900,
    )


@router.post("/execute", response_model=SanitizationResultReport)
async def execute_storage_sanitization(
    exec_req: SanitizationExecuteRequest,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator"])),
    db: Session = Depends(get_db),
):
    """
    Executes storage device sanitization orchestration pipeline.
    Enforces 8-Point Safety Gate, typed confirmation token check, test-lab allowlist verification,
    isolated hardware adapters, and postflight block sampling.
    (Administrator role required).
    """
    request_id = getattr(request.state, "request_id", "N/A")

    report = SanitizationOrchestrator.execute_sanitization(
        request=exec_req,
        current_user=current_user,
        db=db,
        request_id=request_id,
    )

    audit_log(
        message=f"Sanitization orchestration job '{report.job_id}' completed (Status: {report.status}, Target: {report.device_path}, Method: {report.method_used}).",
        operation="SANITIZATION_EXECUTE",
        status=report.status,
        request_id=request_id,
        case_id=str(exec_req.case_id),
        user_id=current_user.username,
        extra_payload={
            "job_id": report.job_id,
            "target_path": report.device_path,
            "target_class": report.target_class,
            "method_used": report.method_used,
            "status": report.status,
        },
    )

    return report
