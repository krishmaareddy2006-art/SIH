"""Hardware Command Adapters and Simulation Mock Engine for ForensicShield.

Places real hardware execution adapters (NVMe Format, ATA Secure Erase) behind a separate disabled interface.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import ForensicShieldException, RealDeviceOperationBlockedException
from app.schemas.sanitization import SanitizationStepResult


class BaseHardwareAdapter(ABC):
    """Abstract interface for storage hardware sanitization adapters."""

    @abstractmethod
    def execute_step(
        self,
        step_number: int,
        step_name: str,
        device_path: str,
        method: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> SanitizationStepResult:
        pass

    @abstractmethod
    def verify_postflight_sample(self, device_path: str, sample_count: int = 100) -> bool:
        pass


class RealDeviceHardwareAdapter(BaseHardwareAdapter):
    """
    Disabled real hardware command adapter.
    Interface for real ATA Secure Erase and NVMe Format binaries (hdparm, nvme-cli).
    """

    def execute_step(
        self,
        step_number: int,
        step_name: str,
        device_path: str,
        method: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> SanitizationStepResult:
        if not settings.REAL_DEVICE_OPERATIONS:
            raise RealDeviceOperationBlockedException(
                "Hardware Adapter Disabled: Real device operations are blocked by system configuration (REAL_DEVICE_OPERATIONS=false)."
            )
        raise ForensicShieldException(
            message=f"Live physical drive destruction on '{device_path}' is protected by safety policy. Direct ATA/NVMe block wiping is blocked on this workstation to prevent accidental host system destruction. To test real permanent data deletion, use Secure File Erasure on a test file.",
            code="REAL_HARDWARE_PROTECTION_GUARD",
            status_code=403,
        )

    def verify_postflight_sample(self, device_path: str, sample_count: int = 100) -> bool:
        if not settings.REAL_DEVICE_OPERATIONS:
            raise RealDeviceOperationBlockedException(
                "Hardware Adapter Disabled: Real device operations are blocked by system configuration (REAL_DEVICE_OPERATIONS=false)."
            )
        return False


class SimulatedHardwareAdapter(BaseHardwareAdapter):
    """
    Simulated mock hardware adapter generating safe dry-run steps and progress callbacks.
    Zero hardware bytes are modified.
    """

    def execute_step(
        self,
        step_number: int,
        step_name: str,
        device_path: str,
        method: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> SanitizationStepResult:
        timestamp = datetime.now(timezone.utc).isoformat()

        # Emit simulated progress callbacks
        if progress_callback:
            progress_callback(100.0, f"Simulated execution of '{step_name}' on '{device_path}' completed.")

        return SanitizationStepResult(
            step_number=step_number,
            step_name=step_name,
            status="SIMULATED",
            progress_percentage=100.0,
            message=f"[DRY-RUN SIMULATION] Step {step_number} '{step_name}' for method '{method}' completed. 0 hardware bytes modified.",
            timestamp=timestamp,
        )

    def verify_postflight_sample(self, device_path: str, sample_count: int = 100) -> bool:
        """Simulates postflight block sampling verification."""
        # Return True for simulated verification
        return True
