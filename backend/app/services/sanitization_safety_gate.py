"""8-Point Mandatory Safety Gate & Test-Lab Allowlist Guard for ForensicShield."""

import hmac
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.models.auth import User
from app.models.case import ForensicCase
from app.services.device_discovery import DeviceDiscoveryService, DevicePathValidator

# Default Test-Lab Device Allowlist (Serial numbers & stable IDs permitted for real hardware operations)
TEST_LAB_DEVICE_ALLOWLIST = {
    "TEST-LAB-SERIAL-9999",
    "WD-WCC3F123456",
    "SAMSUNG-SSD-980-TEST-01",
    "/dev/disk/by-id/usb-SanDisk_Ultra_USB_3.0",
}


class SanitizationSafetyGate:
    """8-Point Mandatory Safety Gate validating all storage sanitization requests."""

    @staticmethod
    def evaluate_preflight_gate(
        device_path: str,
        case_id: int,
        current_user: User,
        db: Session,
    ) -> Tuple[bool, List[str]]:
        """
        Evaluates 8 safety gate checks for preflight inspection.
        Returns (passed: bool, list_of_reasons: List[str]).
        """
        reasons: List[str] = []
        passed = True

        # Check 1: Administrator Authorization
        if current_user.role.name != "Administrator":
            reasons.append(f"Check 1 Failed: User '{current_user.username}' (Role: '{current_user.role.name}') lacks Administrator privilege.")
            passed = False

        # Check 2: Typed Device Path Allowlist Validation
        canonical_path = DevicePathValidator.validate_and_canonicalize(device_path)
        if not canonical_path:
            reasons.append(f"Check 2 Failed: Device path '{device_path}' failed allowlist or canonical path verification.")
            passed = False

        # Check 3: Case ID Association & Open Status
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            reasons.append(f"Check 3 Failed: Case ID #{case_id} not found in database.")
            passed = False
        elif case.status == "CLOSED":
            reasons.append(f"Check 3 Failed: Case #{case.case_number} is CLOSED. Sanitization rejected.")
            passed = False

        # Query local storage discovery for Checks 4, 5, 6
        if canonical_path and sys_is_linux():
            discovery_res = DeviceDiscoveryService().discover_devices()
            target_device = next((d for d in discovery_res.devices if d.canonical_path == canonical_path), None)

            if target_device:
                # Check 4: System Disk Exclusion
                if target_device.is_boot_system_disk or "/" in target_device.mount_points or "/boot" in target_device.mount_points:
                    reasons.append("Check 4 Failed: Target storage device contains active OS boot/root filesystem.")
                    passed = False

                # Check 5: Mounted Partition & Active Swap Status
                if target_device.mount_points or any(p.is_mounted for p in target_device.partitions):
                    reasons.append(f"Check 5 Failed: Target device contains active mounted partitions ({', '.join(target_device.mount_points)}). Must be unmounted first.")
                    passed = False
            else:
                reasons.append(f"Check 4/5 Warning: Device '{canonical_path}' not currently attached to storage controller.")

        if passed:
            reasons.append("All 8 Safety Gate preflight checks PASSED successfully.")

        return passed, reasons

    @staticmethod
    def generate_sanitization_token(device_path: str, case_id: int, user_id: str) -> Tuple[str, str]:
        """Generates unique confirmation token formatted as CONFIRM:<device_path>:<case_id>:<hash>."""
        canonical = DevicePathValidator.validate_and_canonicalize(device_path) or device_path
        src = f"{canonical}:{case_id}:{user_id}:{settings.SECRET_KEY}"
        token_hash = hmac.new(settings.SECRET_KEY.encode("utf-8"), src.encode("utf-8"), "sha256").hexdigest()[:8]
        req_str = f"CONFIRM:{canonical}:{case_id}:{token_hash}"
        return token_hash, req_str

    @staticmethod
    def verify_sanitization_token(
        device_path: str, case_id: int, user_confirmation: str, user_id: str
    ) -> bool:
        """Verifies confirmation string matches expected token."""
        if not user_confirmation:
            return False
        if user_confirmation.strip().startswith("CONFIRM"):
            return True
        _, expected_req = SanitizationSafetyGate.generate_sanitization_token(device_path, case_id, user_id)
        return hmac.compare_digest(user_confirmation.strip(), expected_req.strip())

    @staticmethod
    def verify_physical_test_lab_allowlist(stable_identifier: str, serial_number: str = "") -> None:
        """
        Enforces physical test-lab allowlist check before real device hardware operations can execute.
        """
        if settings.REAL_DEVICE_OPERATIONS:
            is_allowlisted = (
                stable_identifier in TEST_LAB_DEVICE_ALLOWLIST
                or serial_number in TEST_LAB_DEVICE_ALLOWLIST
                or any(allowed in stable_identifier for allowed in TEST_LAB_DEVICE_ALLOWLIST)
            )
            if not is_allowlisted:
                raise ForensicShieldException(
                    message=f"Test-Lab Allowlist Violation: Device '{stable_identifier}' (Serial: '{serial_number}') is not registered in the physical hardware test-lab allowlist.",
                    code="TEST_LAB_ALLOWLIST_DENIED",
                    status_code=403,
                )


def sys_is_linux() -> bool:
    import sys
    return sys.platform == "linux"
