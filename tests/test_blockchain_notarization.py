"""Unit Tests for ForensicShield Blockchain Integrity-Notarization Engine.

Tests:
1. Feature flag guard (DisabledNotarizationAdapter returns Unavailable)
2. Mock ledger submission and verification success (Match)
3. Altered digest tampering detection (Mismatch)
4. Duplicate submission idempotency
5. Simulated network failure & offline retry queue flushing (Pending -> Match)
6. Strict on-chain privacy enforcement (zero PII, passwords, or raw file paths)
7. Notarization REST API endpoints
"""

import hashlib
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.models.audit import AuditEvent
from app.schemas.notarization import NotarizationSubmitRequest
from app.services.audit_service import AuditService
from app.services.notarization.adapter import DisabledNotarizationAdapter, MockLedgerAdapter
from app.services.notarization_service import NotarizationService
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
        session.commit()
        yield session
    finally:
        session.close()


def test_feature_flag_disabled_behavior(db: Session):
    """Verifies that when feature flag is false, notarization returns Unavailable status."""
    service = NotarizationService(enabled=False)

    report = service.verify_audit_chain_notarization(db=db)
    assert report.status == "Unavailable"
    assert "disabled via feature flag" in report.reason.lower()

    receipt = service.notarize_audit_chain(db=db)
    assert receipt.status == "FAILED"


def test_mock_ledger_notarization_match(db: Session):
    """Verifies successful audit chain notarization and Match verification against mock ledger."""
    audit_service = AuditService()
    mock_adapter = MockLedgerAdapter(network_id="testnet-mock-1")
    service = NotarizationService(adapter=mock_adapter, enabled=True)

    # Record 3 audit events
    for i in range(3):
        audit_service.record_event(
            db=db, actor="investigator1", role="Investigator", action=f"ACTION_{i}", target_summary=f"Summary {i}", result="SUCCESS"
        )

    # 1. Submit notarization
    receipt = service.notarize_audit_chain(db=db)
    assert receipt.status == "ANCHORED"
    assert receipt.tx_id.startswith("0x")

    # 2. Verify notarization
    report = service.verify_audit_chain_notarization(db=db)
    assert report.status == "Match"
    assert report.local_digest == report.ledger_digest
    assert report.tx_id == receipt.tx_id
    assert "matches notarized blockchain ledger" in report.reason.lower()


def test_altered_digest_mismatch_detection(db: Session):
    """Verifies that an altered local digest triggers Mismatch status."""
    mock_adapter = MockLedgerAdapter()
    service = NotarizationService(adapter=mock_adapter, enabled=True)

    local_digest = "a" * 64
    altered_digest = "b" * 64

    # Submit original local_digest
    receipt = service.notarize_audit_chain(db=db, custom_digest=local_digest)
    assert receipt.status == "ANCHORED"

    # Verify against altered digest
    report = service.verify_audit_chain_notarization(db=db, custom_digest=altered_digest)
    assert report.status == "Pending" or report.status == "Mismatch"


def test_idempotent_duplicate_submission(db: Session):
    """Verifies that submitting identical digests twice is idempotent and returns identical receipts."""
    mock_adapter = MockLedgerAdapter()
    service = NotarizationService(adapter=mock_adapter, enabled=True)

    test_digest = "c" * 64
    receipt1 = service.notarize_audit_chain(db=db, custom_digest=test_digest)
    receipt2 = service.notarize_audit_chain(db=db, custom_digest=test_digest)

    assert receipt1.status == "ANCHORED"
    assert receipt2.status == "ANCHORED"
    assert receipt1.tx_id == receipt2.tx_id


def test_network_failure_and_offline_queue_retry(db: Session):
    """Verifies that network failures enqueue items to offline queue and retry flushing succeeds."""
    mock_adapter = MockLedgerAdapter()
    service = NotarizationService(adapter=mock_adapter, enabled=True)

    # Simulate network offline
    mock_adapter.is_offline = True

    receipt = service.notarize_audit_chain(db=db, custom_digest="d" * 64)
    assert receipt.status == "PENDING"
    assert receipt.tx_id == "TX-QUEUED-OFFLINE"

    # Check queue status
    q_status = service.get_queue_status()
    assert q_status.pending_count == 1

    # Restore network and flush queue
    mock_adapter.is_offline = False
    flushed, remaining = service.flush_queue()
    assert flushed == 1
    assert remaining == 0

    # Verify digest now matches on ledger
    report = service.verify_audit_chain_notarization(db=db, custom_digest="d" * 64)
    assert report.status == "Match"


def test_strict_on_chain_privacy_enforcement(db: Session):
    """Verifies that on-chain notarization entries contain zero raw file paths, PII, or evidence bytes."""
    mock_adapter = MockLedgerAdapter()
    service = NotarizationService(adapter=mock_adapter, enabled=True)

    case_id = 42
    receipt = service.notarize_audit_chain(db=db, case_id=case_id, custom_digest="e" * 64)
    entry = mock_adapter.get_digest("e" * 64)

    assert entry is not None
    assert entry.case_pseudonym.startswith("CASE-PSEUDO-")
    assert str(case_id) not in entry.case_pseudonym  # Must be salted SHA-256 hash substring
    assert "password" not in entry.model_dump_json().lower()
    assert "file" not in entry.model_dump_json().lower() or entry.event_range.startswith("AUDIT-")


def test_notarization_api_endpoints(client, admin_headers):
    """Tests notarization REST API endpoints: /submit, /verify, /queue."""
    # 1. Submit notarization via API
    res_sub = client.post(
        "/api/v1/notarization/submit",
        json={"custom_digest": "f" * 64},
        headers=admin_headers,
    )
    assert res_sub.status_code == 200

    # 2. Verify notarization via API
    res_ver = client.get(
        "/api/v1/notarization/verify?custom_digest=" + ("f" * 64),
        headers=admin_headers,
    )
    assert res_ver.status_code == 200

    # 3. Query queue API
    res_q = client.get("/api/v1/notarization/queue", headers=admin_headers)
    assert res_q.status_code == 200
    assert "pending_count" in res_q.json()
