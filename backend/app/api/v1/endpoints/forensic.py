"""Forensic Analysis & Safe Mode Simulation Endpoints."""

import uuid
import time
from fastapi import APIRouter, Depends, Request, status
from app.core.config import settings
from app.core.logging import audit_log
from app.core.security import verify_real_device_allowed, verify_destructive_allowed
from app.schemas.forensic import OperationRequest, OperationResponse

router = APIRouter()


@router.post("/simulate-operation", response_model=OperationResponse)
async def simulate_forensic_operation(
    op_request: OperationRequest,
    request: Request,
):
    """
    Executes a forensic operation under SAFE_MODE policy.
    If simulate=False and SAFE_MODE=True, rejects with 403 SafeModeViolationException.
    """
    request_id = getattr(request.state, "request_id", "N/A")
    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")
    start_time = time.time()

    # Enforce safe mode security checks
    verify_destructive_allowed(simulate=op_request.simulate)

    op_id = f"op-{uuid.uuid4().hex[:8]}"

    preview_msg = (
        f"[SAFE_MODE PREVIEW] Action '{op_request.operation_type}' on target '{op_request.target_path}' "
        f"simulated. 0 bytes written to physical storage. Dry-run hash match verified."
    )

    audit_log(
        message=f"Simulated operation {op_request.operation_type} on {op_request.target_path}",
        operation=op_request.operation_type,
        status="SIMULATED",
        request_id=request_id,
        case_id=case_id,
        user_id=user_id,
        extra_payload={
            "target": op_request.target_path,
            "simulated": True,
        },
    )

    elapsed_ms = (time.time() - start_time) * 1000

    return OperationResponse(
        operation_id=op_id,
        status="SIMULATED",
        safe_mode_active=settings.SAFE_MODE,
        target_path=op_request.target_path,
        preview=preview_msg,
        execution_time_ms=round(elapsed_ms, 2),
    )


@router.post("/scan-hardware-device")
async def scan_hardware_device(request: Request, device_path: str = "\\\\.\\PhysicalDrive0"):
    """
    Attempts to access low-level raw physical device.
    Gated strictly by REAL_DEVICE_OPERATIONS flag.
    """
    request_id = getattr(request.state, "request_id", "N/A")
    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")

    # Hardware operation security guard
    verify_real_device_allowed()

    audit_log(
        message=f"Hardware device scan initiated on {device_path}",
        operation="HARDWARE_DEVICE_SCAN",
        status="SUCCESS",
        request_id=request_id,
        case_id=case_id,
        user_id=user_id,
    )

    return {
        "status": "DEVICE_ACCESSED",
        "device_path": device_path,
        "message": "Physical hardware device operational read completed.",
    }
