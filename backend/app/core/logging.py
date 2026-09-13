"""Structured JSON Logging System for ForensicShield.

Emits structured JSON log frames with context parameters:
- request_id: Unique HTTP/task correlation UUID
- case_id: Forensic investigation case context identifier
- user_id: Authenticated operator context identifier
- operation: Action performed (e.g., CASE_CREATE, DEVICE_SCAN)
- status: Action outcome (SUCCESS, SIMULATED, FAILED, BLOCKED)
- timestamp: UTC ISO 8601 string
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONStructuredFormatter(logging.Formatter):
    """Custom logging formatter that outputs log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "N/A"),
            "case_id": getattr(record, "case_id", "N/A"),
            "user_id": getattr(record, "user_id", "ANONYMOUS"),
            "operation": getattr(record, "operation", "SYSTEM_EVENT"),
            "status": getattr(record, "status", "INFO"),
        }

        # Include exception trace data internally if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra payload data if passed in record.__dict__
        if hasattr(record, "extra_payload"):
            log_data["payload"] = getattr(record, "extra_payload")

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures the root logger with the structured JSON formatter."""
    root_logger = logging.getLogger("forensic_shield")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers to prevent duplicate output
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONStructuredFormatter())
    root_logger.addHandler(handler)
    root_logger.propagate = False

    return root_logger


logger = setup_logging()


def audit_log(
    message: str,
    operation: str,
    status: str,
    request_id: str = "N/A",
    case_id: str = "N/A",
    user_id: str = "ANONYMOUS",
    level: int = logging.INFO,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Emits a structured audit log entry with explicit context fields."""
    extra = {
        "request_id": request_id,
        "case_id": case_id,
        "user_id": user_id,
        "operation": operation,
        "status": status,
    }
    if extra_payload:
        extra["extra_payload"] = extra_payload

    logger.log(level, message, extra=extra)
