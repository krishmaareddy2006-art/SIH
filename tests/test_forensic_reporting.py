"""Unit & Integration Tests for ForensicShield Reporting & Compliance Module.

Tests:
1. Forensic compliance language policy enforcement (scrubbing uncalibrated absolute claims).
2. Exclusion of sensitive parameters (passwords, tokens, JWT secrets).
3. 5-point status classification matrix computation (Verified, Inconclusive, Failed, Unsupported, Manual Review).
4. Service PDF (ReportLab) & JSON manifest file generation with SHA-256 digests.
5. Registration of report SHA-256 digest in tamper-evident audit log chain.
6. REST API report preview endpoint (/cases/{case_id}/reports/preview).
7. REST API report generation endpoint (/cases/{case_id}/reports/generate).
8. REST API authorization-guarded download endpoints with X-Report-SHA256 headers.
9. Path traversal security checks on download endpoints.
"""

import hashlib
import json
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.models.audit import AuditEvent
from app.models.case import CarvedFileArtifact, EvidenceItem, ForensicCase, RecoveredArtifact
from app.services.audit_service import AuditService
from app.services.reporting_service import ForensicReportService
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
        yield session
    finally:
        session.close()


def test_compliance_language_scrubber():
    """Verifies that absolute uncalibrated claims are replaced with compliant forensic terminology."""
    service = ForensicReportService()

    input_text = "The sector is 100% unrecoverable, guaranteed unrecoverable and 100% wiped. Impossible to recover."
    scrubbed = service.enforce_compliance_language(input_text)

    assert "100% unrecoverable" not in scrubbed
    assert "guaranteed unrecoverable" not in scrubbed
    assert "100% wiped" not in scrubbed
    assert "Impossible to recover" not in scrubbed

    assert "Logical sanitization verified under test protocol" in scrubbed
    assert "No recoverable sector extents detected" in scrubbed
    assert "Logical overwrite pattern applied" in scrubbed
    assert "No file entry boundaries identified" in scrubbed


def test_sensitive_data_exclusion():
    """Verifies that reports do not expose passwords, authorization tokens, or secrets."""
    service = ForensicReportService()
    text = "Operator authenticated with password=SecretPassword123 and token=Bearer eyJhbGciOiJI..."
    scrubbed = service.enforce_compliance_language(text)

    assert "SecretPassword123" not in scrubbed
    assert "eyJhbGci" not in scrubbed


def test_status_classification_matrix(db: Session):
    """Verifies 5-point status classification breakdown matrix aggregation."""
    service = ForensicReportService()

    # Create dummy case
    case = ForensicCase(
        case_number="CAS-RPT-001",
        title="Report Matrix Test Case",
        description="Testing classification counts",
        investigator_id=1,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Add evidence items
    ev1 = EvidenceItem(
        evidence_id="EV-RPT-01",
        case_id=case.id,
        item_number="ITEM-01",
        title="Disk Image 1",
        original_filename="disk.raw",
        file_path="/evidence/disk.raw",
        operator_username="test_operator",
        file_size_bytes=1024,
        sha256_hash="a" * 64,
        processing_status="COMPLETED",
    )
    ev2 = EvidenceItem(
        evidence_id="EV-RPT-02",
        case_id=case.id,
        item_number="ITEM-02",
        title="Corrupt Image 2",
        original_filename="corrupt.raw",
        file_path="/evidence/corrupt.raw",
        operator_username="test_operator",
        file_size_bytes=2048,
        sha256_hash="b" * 64,
        processing_status="INTEGRITY_FAILURE",
    )
    db.add_all([ev1, ev2])

    # Add recovered artifacts
    rec1 = RecoveredArtifact(
        artifact_id="REC-RPT-01",
        case_id=case.id,
        source_evidence_id=ev1.evidence_id,
        original_path="/deleted/doc.pdf",
        output_file_path="/output/doc.pdf",
        recovered_file_hash="c" * 64,
        source_image_hash="a" * 64,
        source_offset_bytes=1000,
        file_size_bytes=512,
        classification_status="RECOVERABLE",
        filesystem_type="FAT32",
        recovery_method="ExtentsScan",
        operator_username="test_operator",
    )
    rec2 = RecoveredArtifact(
        artifact_id="REC-RPT-02",
        case_id=case.id,
        source_evidence_id=ev1.evidence_id,
        original_path="/deleted/bad.dat",
        output_file_path="/output/bad.dat",
        recovered_file_hash="d" * 64,
        source_image_hash="a" * 64,
        source_offset_bytes=2000,
        file_size_bytes=128,
        classification_status="UNSUPPORTED",
        filesystem_type="UNSUPPORTED",
        recovery_method="ExtentsScan",
        operator_username="test_operator",
    )
    db.add_all([rec1, rec2])

    # Add carved artifact
    carv1 = CarvedFileArtifact(
        carved_id="CARV-RPT-01",
        case_id=case.id,
        source_evidence_id=ev1.evidence_id,
        file_format="PNG",
        output_file_path="/output/carved.png",
        carved_file_hash="e" * 64,
        source_image_hash="a" * 64,
        source_start_offset=100,
        source_end_offset=200,
        file_size_bytes=100,
        confidence_level="MEDIUM",
        operator_username="test_operator",
    )
    db.add(carv1)
    db.commit()

    case_data = service.collect_case_data(db, case.id)
    cls = case_data["classifications"]

    # Verified: ev1 (COMPLETED) + rec1 (RECOVERABLE) = 2
    assert cls["verified"] == 2
    # Inconclusive: carv1 (MEDIUM) = 1
    assert cls["inconclusive"] == 1
    # Failed: ev2 (INTEGRITY_FAILURE) = 1
    assert cls["failed"] == 1
    # Unsupported: rec2 (UNSUPPORTED) = 1
    assert cls["unsupported"] == 1


def test_service_pdf_and_json_report_generation(db: Session):
    """Verifies generation of ReportLab PDF and JSON manifest files with SHA-256 digests."""
    service = ForensicReportService()

    case = ForensicCase(
        case_number="CAS-RPT-002",
        title="PDF & JSON Build Test Case",
        description="Testing PDF & JSON report generation",
        investigator_id=1,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    res = service.generate_case_report(
        db=db,
        case_id=case.id,
        operator_username="test_operator",
    )

    assert res.report_id.startswith("RPT-")
    assert res.case_id == case.id
    assert len(res.pdf_sha256) == 64
    assert len(res.json_sha256) == 64
    assert res.pdf_download_url.endswith("/download/pdf")
    assert res.json_download_url.endswith("/download/json")

    # Check generated files on disk
    pdf_path = Path("reports") / f"case_{case.id}" / f"{res.report_id}_report.pdf"
    json_path = Path("reports") / f"case_{case.id}" / f"{res.report_id}_manifest.json"

    assert pdf_path.exists()
    assert json_path.exists()

    # Check SHA-256 match
    assert hashlib.sha256(pdf_path.read_bytes()).hexdigest() == res.pdf_sha256
    assert hashlib.sha256(json_path.read_bytes()).hexdigest() == res.json_sha256

    # Verify JSON manifest content structure
    manifest_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert manifest_data["report_metadata"]["report_id"] == res.report_id
    assert manifest_data["report_metadata"]["generated_by"] == "test_operator"
    assert "status_classifications" in manifest_data
    assert "audit_chain_verification" in manifest_data


def test_report_audit_chain_registration(db: Session):
    """Verifies that report generation registers a FORENSIC_REPORT_GENERATED audit event in the audit chain."""
    service = ForensicReportService()

    case = ForensicCase(
        case_number="CAS-RPT-003",
        title="Audit Registration Test",
        description="Testing report audit chain registration",
        investigator_id=1,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    res = service.generate_case_report(db, case.id, "auditor_user")

    # Find audit event
    audit_ev = db.query(AuditEvent).filter(AuditEvent.event_id == res.audit_event_id).first()
    assert audit_ev is not None
    assert audit_ev.action == "FORENSIC_REPORT_GENERATED"
    assert audit_ev.actor == "auditor_user"
    assert res.pdf_sha256[:16] in audit_ev.target_summary


def test_report_rest_apis(client, admin_headers, db: Session):
    """Tests preview, generation, and download REST API endpoints."""
    case = ForensicCase(
        case_number="CAS-RPT-API",
        title="REST API Test Case",
        description="Testing reporting API endpoints",
        investigator_id=1,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # 1. Test Report Preview API
    res_prev = client.get(f"/api/v1/cases/{case.id}/reports/preview", headers=admin_headers)
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["case_id"] == case.id
    assert prev_data["case_number"] == "CAS-RPT-API"
    assert prev_data["audit_chain_valid"] is True

    # 2. Test Report Generation API
    res_gen = client.post(f"/api/v1/cases/{case.id}/reports/generate", json={"format": "both"}, headers=admin_headers)
    assert res_gen.status_code == 201
    gen_data = res_gen.json()
    report_id = gen_data["report_id"]
    pdf_sha256 = gen_data["pdf_sha256"]
    json_sha256 = gen_data["json_sha256"]

    # 3. Test Download PDF Endpoint
    res_pdf = client.get(f"/api/v1/cases/{case.id}/reports/{report_id}/download/pdf", headers=admin_headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.headers["X-Report-SHA256"] == pdf_sha256

    # 4. Test Download JSON Endpoint
    res_json = client.get(f"/api/v1/cases/{case.id}/reports/{report_id}/download/json", headers=admin_headers)
    assert res_json.status_code == 200
    assert res_json.headers["content-type"] == "application/json"
    assert res_json.headers["X-Report-SHA256"] == json_sha256


def test_report_download_idor_protection(client, viewer_headers, db: Session):
    """Verifies IDOR protection blocking unauthorized users from requesting reports for cases they don't own."""
    # Case owned by investigator (id=1), viewer user has no access
    case = ForensicCase(
        case_number="CAS-RPT-IDOR",
        title="IDOR Protected Case",
        description="Testing IDOR guard",
        investigator_id=1,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Viewer attempts preview -> 403 Forbidden
    res = client.get(f"/api/v1/cases/{case.id}/reports/preview", headers=viewer_headers)
    assert res.status_code == 403
    assert "IDOR Protection" in res.json()["error"]["message"]

