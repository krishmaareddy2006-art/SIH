"""Unit tests for structured JSON logger."""

import json
import logging
from app.core.logging import JSONStructuredFormatter

def test_json_structured_formatter_output():
    formatter = JSONStructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=42,
        msg="Test audit log entry",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-test-12345"
    record.case_id = "CASE-999"
    record.user_id = "Analyst-Test"
    record.operation = "TEST_OP"
    record.status = "SUCCESS"

    formatted_str = formatter.format(record)
    log_json = json.loads(formatted_str)

    assert log_json["request_id"] == "req-test-12345"
    assert log_json["case_id"] == "CASE-999"
    assert log_json["user_id"] == "Analyst-Test"
    assert log_json["operation"] == "TEST_OP"
    assert log_json["status"] == "SUCCESS"
    assert "timestamp" in log_json
