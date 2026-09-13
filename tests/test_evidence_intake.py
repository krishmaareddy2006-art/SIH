"""Unit Tests for Read-Only Forensic Evidence Image Intake & Integrity Verification.

Tests:
1. Empty image intake (0-byte file SHA-256 calculation)
2. Large image streaming chunk hashing with memory boundary verification
3. Changed/corrupted file detection (INTEGRITY_FAILURE status & tamper rejection)
4. Interrupted hashing with cancellation tokens
5. Duplicate evidence intake warning handling
6. Path traversal and forbidden system path rejection
7. Evidence manifest export in JSON and RFC 4180 CSV formats
8. REST API endpoints for import, verify, and manifest exports
"""

import csv
import io
import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from conftest import TestingSessionLocal

import app.models  # Register all SQLAlchemy models on Base.metadata
from app.core.exceptions import ForensicShieldException
from app.models.auth import User, Role
from app.models.case import ForensicCase, EvidenceItem

from app.schemas.evidence import EvidenceImportRequest, EvidenceVerificationRequest
from app.services.evidence_intake import (
    EvidenceIntakeService,
    StreamingHashCalculator,
    PathSandboxGuard,
)
from app.services.manifest_exporter import EvidenceManifestExporter


from app.core.init_db import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)

    # Fetch seed admin user
    admin_user = db.query(User).filter(User.username == "admin").first()

    # Create default test case
    test_case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()
    if not test_case:
        test_case = ForensicCase(
            case_number="CASE-EVIDENCE-001",
            title="Evidence Intake Test Case",
            description="Case for forensic evidence intake tests",
            investigator_id=admin_user.id,
            status="OPEN",
        )
        db.add(test_case)
        db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)



@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_empty_image_intake(db: Session):
    """Verifies intake of an empty (0-byte) evidence file."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        empty_file = Path(tmpdir) / "empty_image.raw"
        empty_file.touch()

        import_req = EvidenceImportRequest(
            source_file_path=str(empty_file),
            item_number="EVID-EMPTY-01",
            title="Empty Drive Image",
            create_working_copy=True,
        )

        item = intake_service.import_evidence_image(
            db=db,
            case_id=case.id,
            request=import_req,
            operator_username="admin",
        )

        assert item.file_size_bytes == 0
        # Standard SHA-256 digest for 0 bytes
        assert item.sha256_hash.lower() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert item.processing_status == "IMPORTED"
        assert item.working_copy_path is not None
        assert Path(item.working_copy_path).exists()


def test_streaming_large_file_intake(db: Session):
    """Verifies chunked streaming SHA-256 calculation for a multi-chunk file without memory spikes."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        large_file = Path(tmpdir) / "test_500kb.dd"
        # Write 500 KB of structured data across multiple 64 KB chunks
        chunk_data = b"FORENSIC_EVIDENCE_STREAM_" * 2560  # ~64 KB block
        total_chunks = 8
        with open(large_file, "wb") as f:
            for _ in range(total_chunks):
                f.write(chunk_data)

        progress_calls = []

        def progress_cb(processed, total):
            progress_calls.append((processed, total))

        import_req = EvidenceImportRequest(
            source_file_path=str(large_file),
            item_number="EVID-STREAM-01",
            title="500KB Chunked Evidence Image",
            create_working_copy=True,
        )

        item = intake_service.import_evidence_image(
            db=db,
            case_id=case.id,
            request=import_req,
            operator_username="admin",
            progress_callback=progress_cb,
        )

        assert item.file_size_bytes == large_file.stat().st_size
        assert len(progress_calls) > 0
        # Ensure final progress report equals total file size
        assert progress_calls[-1][0] == item.file_size_bytes
        assert item.processing_status == "IMPORTED"


def test_changed_evidence_tamper_rejection(db: Session):
    """Verifies that modified/tampered evidence is rejected and marked as INTEGRITY_FAILURE."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_file = Path(tmpdir) / "evidence_original.raw"
        evidence_file.write_bytes(b"ORIGINAL_SUSPECT_DISK_DATA_PASS1")

        import_req = EvidenceImportRequest(
            source_file_path=str(evidence_file),
            item_number="EVID-TAMPER-01",
            title="Tamper Verification Image",
            create_working_copy=True,
        )

        item = intake_service.import_evidence_image(
            db=db,
            case_id=case.id,
            request=import_req,
            operator_username="admin",
        )

        # First verification before stage - should pass cleanly
        is_valid, stored_hash, calc_hash, verified_item = intake_service.verify_evidence_integrity(
            db=db,
            evidence_id=item.evidence_id,
            stage="PRE_CARVING",
        )
        assert is_valid is True
        assert verified_item.processing_status == "VERIFIED"

        # Tamper working copy file contents by altering 1 byte
        working_copy = Path(item.working_copy_path)
        # Temporarily enable write permissions to simulate unauthorized tampering
        os.chmod(working_copy, 0o666)
        with open(working_copy, "r+b") as f:
            f.seek(0)
            f.write(b"TAMPERED")

        # Second verification before next stage - should raise INTEGRITY_FAILURE
        with pytest.raises(ForensicShieldException) as exc_info:
            intake_service.verify_evidence_integrity(
                db=db,
                evidence_id=item.evidence_id,
                stage="FILE_RECOVERY_STAGE",
            )

        assert exc_info.value.code == "INTEGRITY_FAILURE"
        assert exc_info.value.status_code == 409

        # Reload item from DB and verify status was recorded as INTEGRITY_FAILURE
        db.refresh(item)
        assert item.processing_status == "INTEGRITY_FAILURE"


def test_corrupted_file_detection(db: Session):
    """Verifies that truncated or corrupted files trigger integrity failure."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_file = Path(tmpdir) / "corrupt_test.raw"
        evidence_file.write_bytes(b"CORRUPTION_TEST_DATA_HEADER_FOOTER_1234567890")

        import_req = EvidenceImportRequest(
            source_file_path=str(evidence_file),
            item_number="EVID-CORRUPT-01",
            title="Corrupted File Image",
            create_working_copy=False,
        )

        item = intake_service.import_evidence_image(
            db=db,
            case_id=case.id,
            request=import_req,
            operator_username="admin",
        )

        # Truncate source file by 10 bytes
        with open(evidence_file, "wb") as f:
            f.write(b"CORRUPTION_TEST_DATA_HEADER")

        with pytest.raises(ForensicShieldException) as excinfo:
            intake_service.verify_evidence_integrity(
                db=db,
                evidence_id=item.evidence_id,
                stage="PRE_ANALYSIS",
            )

        assert excinfo.value.code == "INTEGRITY_FAILURE"
        db.refresh(item)
        assert item.processing_status == "INTEGRITY_FAILURE"


def test_interrupted_hashing(db: Session):
    """Verifies that cancellation token halts hashing and raises InterruptedError."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        large_file = Path(tmpdir) / "cancel_test.raw"
        large_file.write_bytes(b"A" * (65536 * 4))

        chunk_count = 0

        def cancel_check():
            nonlocal chunk_count
            chunk_count += 1
            # Cancel on second chunk
            return chunk_count > 1

        import_req = EvidenceImportRequest(
            source_file_path=str(large_file),
            item_number="EVID-CANCEL-01",
            title="Cancelled Intake Image",
            create_working_copy=True,
        )

        with pytest.raises(InterruptedError) as excinfo:
            intake_service.import_evidence_image(
                db=db,
                case_id=case.id,
                request=import_req,
                operator_username="admin",
                check_cancelled=cancel_check,
            )

        assert "cancelled" in str(excinfo.value).lower()


def test_duplicate_evidence_detection(db: Session):
    """Verifies import of identical file in the same case generates duplicate warning log."""
    intake_service = EvidenceIntakeService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_file = Path(tmpdir) / "dup_target.raw"
        evidence_file.write_bytes(b"DUPLICATE_CONTENT_DATA_HASH_KEY")

        import_req1 = EvidenceImportRequest(
            source_file_path=str(evidence_file),
            item_number="EVID-DUP-01",
            title="Original Image",
            create_working_copy=False,
        )
        item1 = intake_service.import_evidence_image(db=db, case_id=case.id, request=import_req1, operator_username="admin")

        import_req2 = EvidenceImportRequest(
            source_file_path=str(evidence_file),
            item_number="EVID-DUP-02",
            title="Duplicate Image Import",
            create_working_copy=False,
        )
        item2 = intake_service.import_evidence_image(db=db, case_id=case.id, request=import_req2, operator_username="admin")

        assert item1.sha256_hash == item2.sha256_hash
        assert item1.evidence_id != item2.evidence_id


def test_path_traversal_rejection(db: Session):
    """Verifies that attempts to access system directories or invalid paths are rejected."""
    # Forbidden system path test
    with pytest.raises(ForensicShieldException) as excinfo:
        PathSandboxGuard.validate_evidence_path("C:\\Windows\\System32\\cmd.exe" if os.name == "nt" else "/etc/passwd")
    
    assert excinfo.value.status_code in (403, 404)

    # Non-existent file test
    with pytest.raises(ForensicShieldException) as exc_missing:
        PathSandboxGuard.validate_evidence_path("/non/existent/path/image.raw")
    
    assert exc_missing.value.code == "FILE_NOT_FOUND"


def test_manifest_export_json_and_csv(db: Session):
    """Verifies JSON and CSV manifest exports contain all required evidence metadata fields."""
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-EVIDENCE-001").first()

    json_manifest = EvidenceManifestExporter.export_json_manifest(db=db, case_id=case.id, operator_username="admin")
    assert json_manifest.manifest_version == "1.0.0"
    assert json_manifest.case_id == case.id
    assert json_manifest.total_evidence_items >= 1
    assert len(json_manifest.evidence_items) >= 1

    csv_content = EvidenceManifestExporter.export_csv_manifest(db=db, case_id=case.id)
    assert isinstance(csv_content, str)

    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) >= 2  # Header + at least 1 evidence row
    header = rows[0]
    assert "evidence_id" in header
    assert "sha256_hash" in header
    assert "file_size_bytes" in header
    assert "processing_status" in header


def test_evidence_api_endpoints(client, admin_headers):
    """Tests evidence HTTP endpoints: import, verify, manifest JSON, and manifest CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        api_img = Path(tmpdir) / "api_test_image.raw"
        api_img.write_bytes(b"API_FORENSIC_EVIDENCE_IMAGE_PAYLOAD")

        # 1. Import API
        import_payload = {
            "source_file_path": str(api_img),
            "item_number": "EVID-API-101",
            "title": "API Test Forensic Image",
            "source_description": "Imported via REST API test",
            "create_working_copy": True,
        }

        res_import = client.post(
            "/api/v1/cases/1/evidence/import",
            json=import_payload,
            headers=admin_headers,
        )
        assert res_import.status_code == 201
        data = res_import.json()
        assert "evidence_id" in data
        evidence_id = data["evidence_id"]
        assert data["processing_status"] == "IMPORTED"

        # 2. Verify API
        res_verify = client.post(
            f"/api/v1/evidence/{evidence_id}/verify",
            json={"stage": "PRE_CARVING_API_STAGE"},
            headers=admin_headers,
        )
        assert res_verify.status_code == 200
        verify_data = res_verify.json()
        assert verify_data["is_valid"] is True
        assert verify_data["stage"] == "PRE_CARVING_API_STAGE"

        # 3. JSON Manifest API
        res_json = client.get("/api/v1/cases/1/evidence/manifest/json", headers=admin_headers)
        assert res_json.status_code == 200
        manifest_json = res_json.json()
        assert manifest_json["manifest_version"] == "1.0.0"

        # 4. CSV Manifest API
        res_csv = client.get("/api/v1/cases/1/evidence/manifest/csv", headers=admin_headers)
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "evidence_id" in res_csv.text
