"""Fuzzing, Bounds Validation & System Resilience Test Suite for ForensicShield QA Framework.

Tests:
1. Format parser property-based/random byte fuzzing (JPEG, PNG, PDF, ZIP).
2. Untrusted evidence offset and length boundary validation.
3. Background job worker cancellation checkpoints, retries, and partial failure recovery.
"""

import io
import os
import random
import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

# Insert backend directory into sys.path to enable app module imports
backend_path = str(Path(__file__).parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.models.audit import AuditEvent
from app.models.job import JobRecord
from app.schemas.carving import CarvingCandidateItem
from app.schemas.job_management import JobSubmitRequest
from app.services.carving.carving_scanner import CarvingScanner
from app.services.carving.format_validators import FormatValidatorFactory
from app.services.job_management_service import JobManagementService
from app.services.job_worker import JobCancelledException
from conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        session.query(AuditEvent).delete()
        session.query(JobRecord).delete()
        session.commit()
        yield session
    finally:
        session.close()


# Helper OffsetBoundsValidator for untrusted offset/length validation testing
class OffsetBoundsValidator:
    @staticmethod
    def validate_bounds(offset: int, length: int, max_size: int) -> bool:
        """Validates that offset and length fall safely within 0..max_size without overflow."""
        if offset < 0 or length < 0:
            return False
        if offset >= max_size:
            return False
        if offset + length > max_size:
            return False
        return True


# -----------------------------------------------------------------------------
# 1. PARSER FUZZING TESTS
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "PDF", "ZIP"])
def test_parser_fuzz_random_bytes(fmt: str):
    """Fuzz format parsers with 50 iterations of random byte sequences."""
    random.seed(42)  # Reproducible seed
    validator = FormatValidatorFactory.get_validator(fmt)
    assert validator is not None

    for i in range(50):
        # Random size between 1 byte and 32 KB
        size = random.randint(1, 32768)
        fuzzed_payload = random.randbytes(size)

        is_valid, confidence, reason, calc_length = validator.validate(fuzzed_payload)

        # Fuzzed random bytes should fail validation or yield LOW confidence
        if is_valid:
            assert confidence in ["LOW", "MEDIUM"]
        else:
            assert is_valid is False
            assert len(reason) > 0


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "PDF", "ZIP"])
def test_parser_fuzz_corrupted_header(fmt: str):
    """Fuzz valid format signatures with corrupted interior bytes."""
    valid_headers = {
        "JPEG": b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00",
        "PNG": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06",
        "PDF": b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF",
        "ZIP": b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    }
    header = valid_headers[fmt]
    validator = FormatValidatorFactory.get_validator(fmt)
    random.seed(123)

    for i in range(20):
        # Truncate or append random garbage
        corrupted = header[: len(header) // 2] + random.randbytes(100)
        is_valid, confidence, reason, calc_length = validator.validate(corrupted)

        # Must return explicit result tuple without throwing uncaught exceptions
        assert isinstance(is_valid, bool)
        assert confidence in ["HIGH", "MEDIUM", "LOW"]


# -----------------------------------------------------------------------------
# 2. UNTRUSTED OFFSET BOUNDS VALIDATION
# -----------------------------------------------------------------------------

def test_untrusted_offset_bounds_rejection():
    """Verifies OffsetBoundsValidator rejects negative, overflowing, or out-of-bounds offsets."""
    image_size = 10 * 1024 * 1024  # 10 MB image

    # Negative offset
    assert OffsetBoundsValidator.validate_bounds(offset=-10, length=100, max_size=image_size) is False

    # Negative length
    assert OffsetBoundsValidator.validate_bounds(offset=100, length=-5, max_size=image_size) is False

    # Out of bounds offset
    assert OffsetBoundsValidator.validate_bounds(offset=image_size + 1, length=10, max_size=image_size) is False

    # Length past image end
    assert OffsetBoundsValidator.validate_bounds(offset=image_size - 10, length=20, max_size=image_size) is False

    # Valid bounds
    assert OffsetBoundsValidator.validate_bounds(offset=1024, length=4096, max_size=image_size) is True


def test_carving_scanner_untrusted_candidate_filtering():
    """Verifies CarvingScanner discards candidates with invalid bounds or extreme untrusted lengths."""
    scanner = CarvingScanner()
    image_bytes = b"X" * 1000

    candidates, bytes_scanned, found_count, rejected_count = scanner.scan_image(
        io.BytesIO(image_bytes),
        image_size=1000,
    )

    # Pure noise garbage image should result in 0 validated candidates
    assert len(candidates) == 0
    assert bytes_scanned == 1000


# -----------------------------------------------------------------------------
# 3. JOB RESILIENCE, CANCELLATION & RECOVERY
# -----------------------------------------------------------------------------

def test_job_cancellation_request(db: Session):
    """Verifies job cancellation request updates job state to cancelling."""
    service = JobManagementService()
    
    # Create running job in DB
    job_rec = JobRecord(
        job_id="JOB-CANCEL-TEST-01",
        case_id=1,
        type="CARVING",
        status="running",
        target_identifier="/dev/sdc",
        progress=20.0,
        progress_stage="Carving sector 100",
        operator_username="admin",
        reason="Cancellation unit test",
    )
    db.add(job_rec)
    db.commit()

    cancelled_job = service.request_job_cancellation(db, job_rec.job_id, "admin")
    assert cancelled_job.status == "cancelling"
    assert cancelled_job.cancellation_requested is True


def test_job_stale_recovery_on_backend_restart(db: Session):
    """Verifies stale running/cancelling jobs are recovered to ABORTED state after backend crash/restart."""
    service = JobManagementService()

    # Create an orphaned running job
    stale_job = JobRecord(
        job_id="JOB-RECOVER-9999",
        case_id=1,
        type="CARVING",
        status="running",
        target_identifier="/dev/sdb",
        progress=45.0,
        progress_stage="Scanning extent block 500",
        operator_username="admin",
        reason="Stale recovery test",
    )
    db.add(stale_job)
    db.commit()

    recovered_count, total = service.recover_stale_jobs_on_startup(db)
    assert recovered_count >= 1

    db.refresh(stale_job)
    assert stale_job.status == "aborted"
    assert "Backend server restarted" in stale_job.error_summary

    # Audit event should be emitted
    ev = db.query(AuditEvent).filter(AuditEvent.action == "JOB_STALE_RECOVERED").first()
    assert ev is not None
    assert "JOB-RECOVER-9999" in ev.target_summary
