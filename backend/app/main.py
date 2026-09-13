"""ForensicShield FastAPI Application Entrypoint.

Initializes security middleware, request tracking, global exception handlers,
API v1 versioned routing, and database tables.
"""


import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.logging import audit_log, setup_logging

from app.core.exceptions import (
    ForensicShieldException,
    forensic_exception_handler,
    validation_exception_handler,
    global_unhandled_exception_handler,
)
from app.api.v1.router import api_v1_router

# Initialize structured JSON logger
setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema and seed default roles/users
    db = SessionLocal()
    try:
        from app.core.init_db import init_db
        init_db(db)
    finally:
        db.close()

    audit_log(
        message=f"{settings.PROJECT_NAME} v{settings.VERSION} starting up.",
        operation="SERVER_STARTUP",
        status="SUCCESS",
        extra_payload={
            "safe_mode": settings.SAFE_MODE,
            "real_device_operations": settings.REAL_DEVICE_OPERATIONS,
            "api_version": settings.API_V1_STR,
        },
    )
    yield
    audit_log(
        message=f"{settings.PROJECT_NAME} shutting down.",
        operation="SERVER_SHUTDOWN",
        status="SUCCESS",
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Digital Forensics & Incident Response Platform Foundation",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Context Tracking & Audit Middleware
@app.middleware("http")
async def context_audit_middleware(request: Request, call_next):
    # Generate or extract request correlation ID
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id

    case_id = request.headers.get("X-Case-ID", "N/A")
    user_id = request.headers.get("X-User-ID", "ANONYMOUS")

    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    # Attach trace header to client response
    response.headers["X-Request-ID"] = request_id

    # Emit structured JSON audit log for HTTP request
    audit_log(
        message=f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
        operation=f"HTTP_{request.method}",
        status="SUCCESS" if response.status_code < 400 else "WARNING",
        request_id=request_id,
        case_id=case_id,
        user_id=user_id,
        extra_payload={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


# Register Exception Handlers
app.add_exception_handler(ForensicShieldException, forensic_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_unhandled_exception_handler)

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
