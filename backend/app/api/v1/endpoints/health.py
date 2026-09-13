"""System Status & Health Check API Endpoint."""

from fastapi import APIRouter, Request
from app.core.config import settings
from app.core.logging import audit_log
from app.schemas.forensic import SystemStatusResponse

router = APIRouter()


@router.get("/health", response_model=SystemStatusResponse)
async def get_system_health(request: Request):
    """Returns platform health status and security feature flag states."""
    request_id = getattr(request.state, "request_id", "N/A")

    audit_log(
        message="Health status query",
        operation="SYSTEM_HEALTH_CHECK",
        status="SUCCESS",
        request_id=request_id,
    )

    return SystemStatusResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        safe_mode=settings.SAFE_MODE,
        real_device_operations=settings.REAL_DEVICE_OPERATIONS,
        environment=settings.ENVIRONMENT,
        status="HEALTHY",
    )
