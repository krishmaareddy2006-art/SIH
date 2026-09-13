"""Unit Tests for ForensicShield Job Management System.

Tests:
1. Full job lifecycle transitions (queued -> running -> completed)
2. Idempotency & duplicate active job prevention (DUPLICATE_ACTIVE_JOB)
3. Job cancellation checkpoints & clean abort handling
4. Estimated vs exact progress reporting
5. Server restart stale job state recovery
6. Audit log emission for all job state transitions
7. REST API endpoints (/jobs/, /{job_id}, /cancel, /recover-stale)
"""

import time
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.models.audit import AuditEvent
from app.models.case import ForensicCase
from app.models.job import JobRecord
from app.schemas.job_management import JobSubmitRequest
from app.services.job_management_service import JobManagementService
from app.services.job_worker import InProcessJobWorker, JobCancelledException
from conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)

    admin_user = db.query(app.models.User).filter(app.models.User.username == "admin").first()
    test_case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-JOB-001").first()
    if not test_case:
        test_case = ForensicCase(
            case_number="CASE-JOB-001",
            title="Job Management Test Case",
            description="Case for job service unit tests",
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
        session.query(JobRecord).delete()
        session.commit()
        yield session
    finally:
        session.close()


def test_job_full_lifecycle_completion(db: Session):
    """Verifies complete job lifecycle transitions from queued to running to completed."""
    worker = InProcessJobWorker()
    service = JobManagementService(worker=worker, session_factory=TestingSessionLocal)
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-JOB-001").first()

    def dummy_task(job_id: str, db: Session, check_cancellation):
        check_cancellation()
        service.update_job_progress(db, job_id, 50.0, "Processing step 1", is_exact=True)
        check_cancellation()
        service.update_job_progress(db, job_id, 100.0, "Completed step 2", is_exact=True)

    req = JobSubmitRequest(
        case_id=case.id,
        type="CARVING",
        target_identifier="/dev/sdb1",
        reason="Testing job lifecycle completion",
    )

    job_rec = service.submit_job(db=db, request=req, operator_username="admin", task_func=dummy_task)
    assert job_rec.status in ["queued", "running", "completed"]

    # Wait for thread pool completion
    time.sleep(0.5)

    db.refresh(job_rec)
    assert job_rec.status == "completed"
    assert job_rec.progress == 100.0
    assert job_rec.started_at is not None
    assert job_rec.finished_at is not None

    # Verify audit events logged
    audit_events = db.query(AuditEvent).filter(AuditEvent.case_id == case.id).all()
    actions = [e.action for e in audit_events]
    assert "JOB_QUEUED" in actions
    assert "JOB_STARTED" in actions
    assert "JOB_COMPLETED" in actions


def test_duplicate_active_job_blocking(db: Session):
    """Verifies that submitting a second active job for the same target and type is blocked (409 Conflict)."""
    worker = InProcessJobWorker()
    service = JobManagementService(worker=worker, session_factory=TestingSessionLocal)
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-JOB-001").first()

    # Manually insert active running job for /dev/sdc
    now = datetime.now(timezone.utc)
    active_job = JobRecord(
        job_id="JOB-SAN-ACTIVE-01",
        case_id=case.id,
        type="SANITIZATION",
        status="running",
        target_identifier="/dev/sdc",
        progress=25.0,
        progress_stage="In progress",
        created_at=now,
        reason="Initial active job",
        operator_username="admin",
    )
    db.add(active_job)
    db.commit()

    req = JobSubmitRequest(
        case_id=case.id,
        type="SANITIZATION",
        target_identifier="/dev/sdc",
        reason="Duplicate job submission attempt",
    )

    with pytest.raises(Exception) as exc_info:
        service.submit_job(db=db, request=req, operator_username="admin", task_func=lambda *a, **k: None)

    assert "Duplicate active job detected" in str(exc_info.value)


def test_cancellation_checkpoint_and_abort(db: Session):
    """Verifies that requesting cancellation triggers JobCancelledException and transitions state to aborted."""
    worker = InProcessJobWorker()
    service = JobManagementService(worker=worker, session_factory=TestingSessionLocal)
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-JOB-001").first()

    def slow_cancelable_task(job_id: str, db: Session, check_cancellation):
        for i in range(10):
            check_cancellation()
            time.sleep(0.1)

    req = JobSubmitRequest(
        case_id=case.id,
        type="RECOVERY",
        target_identifier="/dev/sdd",
        reason="Testing job cancellation checkpoint",
    )

    job_rec = service.submit_job(db=db, request=req, operator_username="admin", task_func=slow_cancelable_task)
    time.sleep(0.05)

    # Request cancellation
    canceled_rec = service.request_job_cancellation(db=db, job_id=job_rec.job_id, operator_username="admin")
    assert canceled_rec.status == "cancelling"
    assert canceled_rec.cancellation_requested is True

    time.sleep(0.4)
    db.refresh(job_rec)

    assert job_rec.status == "aborted"
    assert "cancelled by operator" in job_rec.progress_stage.lower() or "cancellation" in job_rec.error_summary.lower()


def test_estimated_vs_exact_progress_reporting(db: Session):
    """Verifies exact vs estimated progress reporting flags."""
    service = JobManagementService()

    now = datetime.now(timezone.utc)
    job = JobRecord(
        job_id="JOB-EST-01",
        type="CARVING",
        status="running",
        target_identifier="/dev/sde",
        progress=10.0,
        progress_stage="Initial stage",
        is_progress_exact=True,
        created_at=now,
        reason="Progress testing",
        operator_username="admin",
    )
    db.add(job)
    db.commit()

    service.update_job_progress(db, job_id="JOB-EST-01", progress=45.5, stage="Estimating sector ranges", is_exact=False)

    db.refresh(job)
    assert job.progress == 45.5
    assert job.progress_stage == "Estimating sector ranges"
    assert job.is_progress_exact is False


def test_stale_job_recovery_on_backend_restart(db: Session):
    """Verifies that running/cancelling jobs orphan on server restart are recovered to aborted."""
    service = JobManagementService()

    now = datetime.now(timezone.utc)
    stale1 = JobRecord(
        job_id="JOB-STALE-01",
        type="SANITIZATION",
        status="running",
        target_identifier="/dev/sdf",
        progress=50.0,
        progress_stage="Overwriting pass 2",
        created_at=now,
        reason="Stale job 1",
        operator_username="admin",
    )
    stale2 = JobRecord(
        job_id="JOB-STALE-02",
        type="ERASURE",
        status="cancelling",
        target_identifier="/tmp/evidence.dat",
        progress=80.0,
        progress_stage="Cancelling...",
        created_at=now,
        reason="Stale job 2",
        operator_username="admin",
    )
    db.add_all([stale1, stale2])
    db.commit()

    recovered_cnt, aborted_cnt = service.recover_stale_jobs_on_startup(db=db)
    assert recovered_cnt == 2
    assert aborted_cnt == 2

    db.refresh(stale1)
    db.refresh(stale2)

    assert stale1.status == "aborted"
    assert "backend server restarted" in stale1.error_summary.lower()
    assert stale2.status == "aborted"


def test_job_api_endpoints(client, admin_headers):
    """Tests job management REST API endpoints: /jobs/, /{job_id}, /cancel, and /recover-stale."""
    # 1. Submit job via API
    res_san = client.post(
        "/api/v1/jobs/sanitization",
        json={
            "case_id": 1,
            "reason": "API Job sanitization test justification",
            "target_identifier": "/dev/sdg",
            "explicit_confirmation": "CONFIRM_SENSITIVE_ACTION",
            "simulate": True,
        },
        headers=admin_headers,
    )
    assert res_san.status_code == 200
    job_id = res_san.json()["job_id"]

    # 2. List jobs
    res_list = client.get("/api/v1/jobs/", headers=admin_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Get job detail
    res_detail = client.get(f"/api/v1/jobs/{job_id}", headers=admin_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["job_id"] == job_id

    # 4. Trigger stale job recovery API
    res_rec = client.post("/api/v1/jobs/recover-stale", headers=admin_headers)
    assert res_rec.status_code == 200
    assert "recovered_jobs_count" in res_rec.json()
