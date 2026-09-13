"""Unit Tests for ForensicShield Tamper-Evident Audit Logging Engine & REST API.

Tests:
1. Genesis block initialization & cryptographic SHA-256 hash chaining
2. Intact chain integrity verification
3. Field modification tampering attack detection & affected event listing
4. Record deletion tampering attack detection
5. Record reordering tampering attack detection
6. Sensitive data scrubbing & sanitization
7. Concurrent multi-threaded write safety
8. JSON & CSV export with SHA-256 export manifest digest
9. Audit REST API endpoints and immutability guards
"""

import hashlib
import json
import threading
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.models.audit import AuditEvent
from app.services.audit_service import AuditService, GENESIS_PREVIOUS_HASH
from app.services.blockchain_adapter import SimulatedBlockchainAdapter
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
        # Clear audit_events before each test
        session.query(AuditEvent).delete()
        session.commit()
        yield session
    finally:
        session.close()


def test_genesis_and_intact_hash_chain(db: Session):
    """Verifies Genesis block creation and sequential SHA-256 hash chaining."""
    audit_service = AuditService()

    # Append 5 events
    events = []
    for i in range(5):
        ev = audit_service.record_event(
            db=db,
            actor=f"user_{i}",
            role="Investigator",
            action=f"ACTION_{i}",
            target_summary=f"Target summary for item {i}",
            result="SUCCESS",
        )
        events.append(ev)

    # 1. Genesis check
    assert events[0].previous_hash == GENESIS_PREVIOUS_HASH

    # 2. Sequential link check
    for i in range(1, 5):
        assert events[i].previous_hash == events[i - 1].current_hash

    # 3. Chain verification
    res = audit_service.verify_chain(db)
    assert res.is_valid is True
    assert res.total_events == 5
    assert res.chain_status == "INTACT"
    assert res.first_broken_event_id is None


def test_field_modification_tampering_detection(db: Session):
    """Verifies that tampering with a field in an existing event breaks the hash chain."""
    audit_service = AuditService()

    events = [
        audit_service.record_event(db=db, actor="admin", role="Administrator", action="CASE_CREATE", target_summary=f"Case #{i}", result="SUCCESS")
        for i in range(5)
    ]

    # Tamper with actor field of event 2 directly in DB
    events[2].actor = "MALICIOUS_ATTACKER"
    db.commit()

    res = audit_service.verify_chain(db)
    assert res.is_valid is False
    assert res.chain_status == "BROKEN_CHAIN_DETECTED"
    assert res.broken_index == 2
    assert res.first_broken_event_id == events[2].event_id
    assert "field tampering detected" in res.reason.lower()
    # Affected downstream event list includes event 2, 3, 4
    assert res.affected_event_ids == [events[2].event_id, events[3].event_id, events[4].event_id]


def test_deletion_tampering_detection(db: Session):
    """Verifies that deleting an audit event from the middle of the chain breaks verification."""
    audit_service = AuditService()

    events = [
        audit_service.record_event(db=db, actor="operator1", role="Operator", action="FILE_ERASURE", target_summary=f"File #{i}", result="SUCCESS")
        for i in range(4)
    ]

    # Delete event at index 1 from DB
    deleted_id = events[1].event_id
    db.delete(events[1])
    db.commit()

    res = audit_service.verify_chain(db)
    assert res.is_valid is False
    assert res.broken_index == 1
    assert res.first_broken_event_id == events[2].event_id
    assert "previous hash link broken" in res.reason.lower()


def test_reordering_tampering_detection(db: Session):
    """Verifies that reordering events in the database invalidates the hash chain."""
    audit_service = AuditService()

    e0 = audit_service.record_event(db=db, actor="admin", role="Administrator", action="LOGIN", target_summary="System login", result="SUCCESS")
    e1 = audit_service.record_event(db=db, actor="admin", role="Administrator", action="CASE_CREATE", target_summary="Case #101", result="SUCCESS")
    e2 = audit_service.record_event(db=db, actor="admin", role="Administrator", action="EVIDENCE_INTAKE", target_summary="Evidence #1", result="SUCCESS")

    # Swap sequence positions of e1 and e2
    e1_hash = e1.current_hash
    e1.current_hash = e2.current_hash
    e2.current_hash = e1_hash
    db.commit()

    res = audit_service.verify_chain(db)
    assert res.is_valid is False


def test_sensitive_data_sanitization(db: Session):
    """Verifies that sensitive parameters (passwords, tokens) are scrubbed before logging."""
    audit_service = AuditService()

    raw_summary = "User login attempt with password=MySecret123 and auth Token=Bearer eyJhbGciOiJIUzI1NiIn..."
    event = audit_service.record_event(
        db=db,
        actor="admin",
        role="Administrator",
        action="LOGIN",
        target_summary=raw_summary,
        result="SUCCESS",
    )

    assert "MySecret123" not in event.target_summary
    assert "password=[REDACTED]" in event.target_summary
    assert "Bearer [REDACTED]" in event.target_summary


def test_concurrent_writes_thread_safety(db: Session):
    """Verifies thread-safety when multiple concurrent threads append audit events simultaneously."""
    audit_service = AuditService()
    threads = []

    def log_worker(idx: int):
        # Create separate DB session per thread
        thread_db = TestingSessionLocal()
        try:
            audit_service.record_event(
                db=thread_db,
                actor=f"worker_{idx}",
                role="Operator",
                action="CONCURRENT_TASK",
                target_summary=f"Concurrent task payload {idx}",
                result="SUCCESS",
            )
        finally:
            thread_db.close()

    for i in range(20):
        t = threading.Thread(target=log_worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    res = audit_service.verify_chain(db)
    assert res.is_valid is True
    assert res.total_events == 20


def test_blockchain_adapter_integration(db: Session):
    """Verifies that audit events are submitted and verifiable against permissioned blockchain adapter."""
    sim_blockchain = SimulatedBlockchainAdapter()
    audit_service = AuditService(blockchain_adapter=sim_blockchain)

    ev = audit_service.record_event(
        db=db,
        actor="admin",
        role="Administrator",
        action="BLOCKCHAIN_TEST",
        target_summary="Ledger anchor test",
        result="SUCCESS",
    )

    assert sim_blockchain.get_ledger_count() == 1
    assert sim_blockchain.verify_block(ev) is True


def test_export_json_and_csv_with_sha256(db: Session):
    """Verifies audit log export to JSON and CSV with SHA-256 export manifest hash."""
    audit_service = AuditService()

    for i in range(3):
        audit_service.record_event(
            db=db, actor="investigator", role="Investigator", action=f"EXPORT_ACTION_{i}", target_summary=f"Target {i}", result="SUCCESS"
        )

    # JSON Export
    json_bytes, json_hash, json_count = audit_service.export_audit_log(db, export_format="json")
    assert json_count == 3
    assert json_hash == hashlib.sha256(json_bytes).hexdigest()
    parsed_json = json.loads(json_bytes.decode("utf-8"))
    assert len(parsed_json["audit_events"]) == 3

    # CSV Export
    csv_bytes, csv_hash, csv_count = audit_service.export_audit_log(db, export_format="csv")
    assert csv_count == 3
    assert csv_hash == hashlib.sha256(csv_bytes).hexdigest()
    assert b"EXPORT_ACTION_0" in csv_bytes


def test_audit_api_endpoints(client, admin_headers):
    """Tests audit REST API endpoints: /logs, /verify, /export, and immutability guard."""
    # 1. Fetch audit logs
    res_logs = client.get("/api/v1/audit/logs", headers=admin_headers)
    assert res_logs.status_code == 200

    # 2. Verify hash chain API
    res_verify = client.get("/api/v1/audit/verify", headers=admin_headers)
    assert res_verify.status_code == 200
    assert res_verify.json()["is_valid"] is True

    # 3. Export JSON API
    res_export = client.get("/api/v1/audit/export/json", headers=admin_headers)
    assert res_export.status_code == 200
    assert "X-Export-SHA256" in res_export.headers

    # 4. Immutability guard test (PUT/DELETE return 403 Forbidden)
    res_put = client.put("/api/v1/audit/logs/AUDIT-12345", json={"actor": "hacker"}, headers=admin_headers)
    assert res_put.status_code == 403
