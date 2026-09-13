"""Safe Storage Sanitization Orchestration Layer for ForensicShield.

Orchestrates preflight inspection, 8-point safety gate evaluation, hardware adapter selection,
intent logging, real-time progress & cancellation hooks, and postflight block sampling verification.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.models.auth import User
from app.schemas.sanitization import (
    SanitizationExecuteRequest,
    SanitizationPreflightReport,
    SanitizationResultReport,
    SanitizationStepResult,
)
from app.services.device_discovery import DeviceDiscoveryService, DevicePathValidator
from app.services.hardware_adapters import (
    BaseHardwareAdapter,
    RealDeviceHardwareAdapter,
    SimulatedHardwareAdapter,
)
from app.services.sanitization_classifier import StorageTargetClassifier
from app.services.sanitization_safety_gate import SanitizationSafetyGate


class SanitizationOrchestrator:
    """Orchestrates safe storage device sanitization preflight and execution pipelines."""

    @staticmethod
    def generate_preflight_report(
        device_path: str,
        case_id: int,
        current_user: User,
        db: Session,
    ) -> SanitizationPreflightReport:
        """Evaluates 8-Point Safety Gate, classifies storage target, and produces dry-run plan."""
        canonical_path = DevicePathValidator.validate_and_canonicalize(device_path) or device_path

        # 1. Evaluate 8-Point Safety Gate
        passed, reasons = SanitizationSafetyGate.evaluate_preflight_gate(
            device_path=canonical_path,
            case_id=case_id,
            current_user=current_user,
            db=db,
        )

        # 2. Inspect device properties (or default mock for unit tests/non-linux)
        discovery_res = DeviceDiscoveryService().discover_devices()
        target_dev = next((d for d in discovery_res.devices if d.canonical_path == canonical_path), None)

        if target_dev:
            target_class = StorageTargetClassifier.classify_target(
                device_path=target_dev.canonical_path,
                transport=target_dev.transport,
                is_rotational=target_dev.is_rotational,
                model=target_dev.model,
                vendor=target_dev.vendor,
            )
            model = target_dev.model
            vendor = target_dev.vendor
            size_bytes = target_dev.size_bytes
            stable_id = target_dev.stable_identifier
            is_boot_disk = target_dev.is_boot_system_disk
            is_mounted = len(target_dev.mount_points) > 0
        else:
            # Fallback classification for direct device path
            target_class = StorageTargetClassifier.classify_target(canonical_path)
            model = "Generic Storage Target"
            vendor = "Generic Vendor"
            size_bytes = 0
            stable_id = f"/dev/disk/by-id/generic_{canonical_path.replace('/', '_')}"
            is_boot_disk = canonical_path in ["/dev/sda", "/dev/nvme0n1"]
            is_mounted = False

        # 3. Method Recommendation & Confidence Level
        rec = StorageTargetClassifier.get_recommendation(target_class)

        planned_steps = [
            "Step 1: 8-Point Safety Gate Verification & Physical Allowlist Check",
            "Step 2: Partition Unmount & Active Swap Lock Audit",
            f"Step 3: Hardware Sanitization Command Sequence Initialization ({rec['recommended_method']})",
            "Step 4: Command Execution & Real-Time Progress Monitoring",
            "Step 5: Postflight Block Sampling & Zero Verification",
        ]

        return SanitizationPreflightReport(
            device_path=device_path,
            canonical_path=canonical_path,
            stable_identifier=stable_id,
            target_class=target_class,
            model=model,
            vendor=vendor,
            size_bytes=size_bytes,
            recommended_method=rec["recommended_method"],
            confidence_level=rec["confidence_level"],
            alternative_methods=rec["alternative_methods"],
            ftl_caveats=rec["ftl_caveats"],
            is_boot_system_disk=is_boot_disk,
            is_mounted=is_mounted,
            safety_gate_passed=passed,
            safety_gate_reasons=reasons,
            planned_steps=planned_steps,
        )

    @staticmethod
    def execute_sanitization(
        request: SanitizationExecuteRequest,
        current_user: User,
        db: Session,
        request_id: str = "N/A",
        check_cancelled: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> SanitizationResultReport:
        """
        Executes sanitization execution pipeline.
        Enforces 8-point safety gate, confirmation token verification,
        test-lab allowlist check, hardware adapter selection, and postflight verification.
        """
        start_time = time.time()
        job_id = f"san-{uuid.uuid4().hex[:8]}"

        # 1. Evaluate Safety Gate Preflight
        preflight = SanitizationOrchestrator.generate_preflight_report(
            device_path=request.device_path,
            case_id=request.case_id,
            current_user=current_user,
            db=db,
        )

        if not preflight.safety_gate_passed:
            reasons_str = "; ".join(preflight.safety_gate_reasons)
            raise ForensicShieldException(
                message=f"Sanitization rejected by 8-Point Safety Gate: {reasons_str}",
                code="SAFETY_GATE_REJECTED",
                status_code=403,
            )

        # 2. Verify Confirmation Token
        if not SanitizationSafetyGate.verify_sanitization_token(
            request.device_path, request.case_id, request.confirmation_token, current_user.username
        ):
            _, expected_req = SanitizationSafetyGate.generate_sanitization_token(
                request.device_path, request.case_id, current_user.username
            )
            raise ForensicShieldException(
                message=f"Confirmation token mismatch. Required string: '{expected_req}'",
                code="INVALID_CONFIRMATION_TOKEN",
                status_code=400,
            )

        # 3. Check Physical Test-Lab Allowlist if REAL_DEVICE_OPERATIONS=true
        if not request.simulate and not settings.SAFE_MODE and settings.REAL_DEVICE_OPERATIONS:
            SanitizationSafetyGate.verify_physical_test_lab_allowlist(preflight.stable_identifier)

        # 4. Select Hardware Adapter
        is_simulated = request.simulate or settings.SAFE_MODE or not settings.REAL_DEVICE_OPERATIONS
        adapter: BaseHardwareAdapter = (
            SimulatedHardwareAdapter() if is_simulated else RealDeviceHardwareAdapter()
        )

        method_used = request.chosen_method or preflight.recommended_method

        # 5. Audit Intent Logging (Sanitized, ZERO secret or payload data logged)
        audit_log(
            message=f"Sanitization intent logged for job '{job_id}' by user '{current_user.username}' on target '{preflight.canonical_path}' (Class: {preflight.target_class}, Method: {method_used}, Simulated: {is_simulated}). Reason: {request.reason}",
            operation="SANITIZATION_INTENT_LOG",
            status="SIMULATED" if is_simulated else "HARDWARE_INTENT",
            request_id=request_id,
            case_id=str(request.case_id),
            user_id=current_user.username,
            extra_payload={
                "job_id": job_id,
                "target_path": preflight.canonical_path,
                "target_class": preflight.target_class,
                "method_used": method_used,
                "simulated": is_simulated,
                "reason": request.reason,
            },
        )

        # 6. Execute Pipeline Steps
        execution_steps: List[SanitizationStepResult] = []
        pipeline_failed = False

        step_names = [
            "Preflight 8-Point Safety Gate Verification",
            "Unmount Partition & Active Swap Lock Check",
            f"Hardware Sequence Prep ({method_used})",
            "Command Execution & Progress Monitoring",
            "Postflight Block Sampling & Zero Verification",
        ]

        for idx, step_name in enumerate(step_names, start=1):
            if check_cancelled and check_cancelled():
                execution_steps.append(
                    SanitizationStepResult(
                        step_number=idx,
                        step_name=step_name,
                        status="ABORTED",
                        progress_percentage=0.0,
                        message="Operation cancelled by user.",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
                pipeline_failed = True
                break

            step_res = adapter.execute_step(
                step_number=idx,
                step_name=step_name,
                device_path=preflight.canonical_path,
                method=method_used,
                progress_callback=progress_callback,
            )
            execution_steps.append(step_res)

        # 7. Postflight Verification
        verified = adapter.verify_postflight_sample(preflight.canonical_path)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        if pipeline_failed:
            final_status = "ABORTED"
        elif is_simulated:
            final_status = "SIMULATED"
        elif verified:
            final_status = "COMPLETED_VERIFIED"
        else:
            final_status = "COMPLETED_INCONCLUSIVE"

        return SanitizationResultReport(
            job_id=job_id,
            device_path=preflight.canonical_path,
            case_id=request.case_id,
            target_class=preflight.target_class,
            method_used=method_used,
            confidence_level=preflight.confidence_level,
            status=final_status,
            safe_mode_active=settings.SAFE_MODE,
            execution_steps=execution_steps,
            postflight_sample_verified=verified,
            execution_time_ms=elapsed_ms,
        )
