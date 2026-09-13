"""Global Exception Handlers and Safe Error Sanitization for ForensicShield.

Ensures that unexpected internal exceptions do not leak stack traces or system secrets to API clients.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.logging import audit_log, logger


class ForensicShieldException(Exception):
    """Base class for domain-specific security and operational exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class SafeModeViolationException(ForensicShieldException):
    """Raised when a destructive action is attempted while SAFE_MODE is active."""

    def __init__(
        self,
        message: str = "Destructive execution blocked. SAFE_MODE is active.",
    ):
        super().__init__(
            message=message,
            code="SAFE_MODE_BLOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class RealDeviceOperationBlockedException(ForensicShieldException):
    """Raised when physical device access is attempted while REAL_DEVICE_OPERATIONS=false."""

    def __init__(
        self,
        message: str = "Real hardware device access is disabled by system policy.",
    ):
        super().__init__(
            message=message,
            code="REAL_DEVICE_OPS_DISABLED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFoundException(ForensicShieldException):
    """Raised when requested forensic resource is missing."""

    def __init__(self, message: str = "Requested forensic resource not found."):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


def make_safe_error_payload(
    code: str, message: str, request_id: str = "N/A"
) -> Dict[str, Any]:
    """Generates a standardized safe error response payload."""
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }


async def forensic_exception_handler(
    request: Request, exc: ForensicShieldException
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "N/A")
    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")

    audit_log(
        message=f"Forensic shield exception [{exc.code}]: {exc.message}",
        operation="EXCEPTION_HANDLED",
        status="BLOCKED" if "BLOCKED" in exc.code else "ERROR",
        request_id=request_id,
        case_id=case_id,
        user_id=user_id,
        level=logging.WARNING if exc.status_code < 500 else logging.ERROR,
    )

    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content=make_safe_error_payload(
            code=exc.code, message=exc.message, request_id=request_id
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "N/A")
    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")

    audit_log(
        message="Request payload validation failed.",
        operation="REQUEST_VALIDATION",
        status="FAILED",
        request_id=request_id,
        case_id=case_id,
        user_id=user_id,
        level=logging.WARNING,
    )

    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        headers=headers,
        content=make_safe_error_payload(
            code="VALIDATION_ERROR",
            message="Invalid request parameter or payload format.",
            request_id=request_id,
        ),
    )


async def global_unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "N/A")
    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")

    # Log full trace internally for security engineers
    logger.error(
        f"Unhandled application crash: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "case_id": case_id,
            "user_id": user_id,
            "operation": "UNHANDLED_EXCEPTION",
            "status": "CRITICAL",
        },
    )

    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    # Return safe, non-leaking message to API client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers=headers,
        content=make_safe_error_payload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected system error occurred. System administrators have been notified.",
            request_id=request_id,
        ),
    )

