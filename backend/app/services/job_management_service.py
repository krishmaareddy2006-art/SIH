"""Job Management Service for ForensicShield.

Provides state machine transitions (queued, running, cancelling, completed, failed, aborted, manual-review),
duplicate active job prevention, estimated/exact progress updates, cancellation checkpoints,
server restart stale job recovery, and audit log integration.
"""

import threading
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.models.job import JobRecord
from app.schemas.job_management import JobSubmitRequest, JobDetailResponse
from app.services.audit_service import AuditService
from app.services.job_worker import BaseJobWorker, InProcessJobWorker, JobCancelledException

from app.core.database import SessionLocal

VALID_STATUSES = {"queued", "running", "cancelling", "completed", "failed", "aborted", "manual-review"}


class JobManagementService:
    """Core job management service managing state machine transitions and execution."""

    def __init__(
        self,
        worker: Optional[BaseJobWorker] = None,
        audit_service: Optional[AuditService] = None,
        session_factory: Optional[Callable[[], Session]] = None,
    ):
        self.worker = worker or InProcessJobWorker()
        self.audit_service = audit_service or AuditService()
        self.session_factory = session_factory or SessionLocal

    def prevent_duplicate_active_job(self, db: Session, target_identifier: str, job_type: str) -> None:
        """
        Checks if an active job already exists for the target identifier and job type.
        Raises HTTP 409 Conflict if duplicate active job is detected.
        """
        active_statuses = ["queued", "running", "cancelling"]
        existing = (
            db.query(JobRecord)
            .filter(
                JobRecord.target_identifier == target_identifier,
                JobRecord.type == job_type,
                JobRecord.status.in_(active_statuses),
            )
            .first()
        )

        if existing:
            raise ForensicShieldException(
                message=f"Duplicate active job detected: Target '{target_identifier}' already has an active {job_type} job ('{existing.job_id}' in state '{existing.status}').",
                code="DUPLICATE_ACTIVE_JOB",
                status_code=409,
            )

    def submit_job(
        self,
        db: Session,
        request: JobSubmitRequest,
        operator_username: str,
        task_func: Callable,
    ) -> JobRecord:
        """
        Submits a new background job:
        1. Checks duplicate active job prevention.
        2. Persists initial JobRecord in DB (status='queued').
        3. Emits 'JOB_QUEUED' audit log.
        4. Enqueues job into background worker thread pool.
        """
        self.prevent_duplicate_active_job(db, target_identifier=request.target_identifier, job_type=request.type)

        now = datetime.now(timezone.utc)
        job_id = f"JOB-{request.type[:3]}-{now.strftime('%Y%m%d')}-{db.query(JobRecord).count()+1:04d}"

        job_rec = JobRecord(
            job_id=job_id,
            case_id=request.case_id,
            type=request.type.upper(),
            status="queued",
            target_identifier=request.target_identifier,
            progress=0.0,
            progress_stage="Queued for execution",
            is_progress_exact=True,
            created_at=now,
            cancellation_requested=False,
            reason=request.reason,
            operator_username=operator_username,
            worker_node_id="in-process-worker-1",
        )

        db.add(job_rec)
        db.commit()
        db.refresh(job_rec)

        # Audit Event Emission
        self.audit_service.record_event(
            db=db,
            actor=operator_username,
            role="Operator",
            action="JOB_QUEUED",
            target_summary=f"Enqueued {job_rec.type} job '{job_id}' for target '{request.target_identifier}'",
            result="SUCCESS",
            case_id=request.case_id,
        )

        # Enqueue in worker thread pool using exact sessionmaker type of active db session
        db_factory = type(db)
        self.worker.enqueue_job(
            job_id,
            self._task_runner_wrapper,
            db_session_factory=db_factory,
            user_task_func=task_func,
        )

        return job_rec

    def _task_runner_wrapper(self, job_id: str, cancel_event: threading.Event, db_session_factory, user_task_func: Callable):
        """Worker thread wrapper running user_task_func inside dedicated DB transaction."""
        db: Session = db_session_factory()
        try:
            job: Optional[JobRecord] = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if not job:
                return

            # Transition to RUNNING
            now = datetime.now(timezone.utc)
            job.status = "running"
            job.started_at = now
            job.progress_stage = "Execution started"
            db.commit()

            self.audit_service.record_event(
                db=db,
                actor=job.operator_username,
                role="Operator",
                action="JOB_STARTED",
                target_summary=f"Started {job.type} job '{job_id}' on target '{job.target_identifier}'",
                result="SUCCESS",
                case_id=job.case_id,
            )

            # Run actual task function with progress/cancellation helpers
            user_task_func(job_id=job_id, db=db, check_cancellation=lambda: self.worker.check_cancellation(job_id))

            # Transition to COMPLETED
            db.refresh(job)
            now_end = datetime.now(timezone.utc)
            if job.status not in ["aborted", "cancelling", "failed"]:
                job.status = "completed"
                job.progress = 100.0
                job.progress_stage = "Job completed successfully"
                job.finished_at = now_end
                db.commit()

                self.audit_service.record_event(
                    db=db,
                    actor=job.operator_username,
                    role="Operator",
                    action="JOB_COMPLETED",
                    target_summary=f"Completed {job.type} job '{job_id}' on target '{job.target_identifier}'",
                    result="SUCCESS",
                    case_id=job.case_id,
                )

        except JobCancelledException as e:
            # Handle cancellation checkpoint abort
            now_end = datetime.now(timezone.utc)
            job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if job:
                job.status = "aborted"
                job.cancellation_requested = True
                job.progress_stage = "Job cancelled by operator"
                job.finished_at = now_end
                job.error_summary = str(e)
                db.commit()

                self.audit_service.record_event(
                    db=db,
                    actor=job.operator_username,
                    role="Operator",
                    action="JOB_ABORTED",
                    target_summary=f"Aborted {job.type} job '{job_id}' upon cancellation request",
                    result="ABORTED",
                    case_id=job.case_id,
                )
        except Exception as e:
            # Handle execution failure
            now_end = datetime.now(timezone.utc)
            job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if job:
                job.status = "failed"
                job.progress_stage = "Execution failed"
                job.finished_at = now_end
                job.error_summary = str(e)
                db.commit()

                self.audit_service.record_event(
                    db=db,
                    actor=job.operator_username,
                    role="Operator",
                    action="JOB_FAILED",
                    target_summary=f"Failed {job.type} job '{job_id}': {str(e)[:200]}",
                    result="FAILED",
                    case_id=job.case_id,
                )
        finally:
            db.close()

    def update_job_progress(
        self,
        db: Session,
        job_id: str,
        progress: float,
        stage: str,
        is_exact: bool = True,
    ) -> None:
        """Updates progress percentage, stage description, and exactness flag."""
        job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not job:
            return

        job.progress = max(0.0, min(100.0, progress))
        job.progress_stage = stage[:200]
        job.is_progress_exact = is_exact
        db.commit()

    def request_job_cancellation(self, db: Session, job_id: str, operator_username: str) -> JobRecord:
        """
        Requests cancellation of a queued or running job:
        1. Updates DB status to 'cancelling'.
        2. Triggers worker cancellation event.
        3. Emits 'JOB_CANCEL_REQUESTED' audit log.
        """
        job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not job:
            raise ForensicShieldException(
                message=f"Job with ID '{job_id}' not found.",
                code="JOB_NOT_FOUND",
                status_code=404,
            )

        if job.status in ["completed", "failed", "aborted"]:
            raise ForensicShieldException(
                message=f"Job '{job_id}' is already in terminal state '{job.status}' and cannot be cancelled.",
                code="JOB_TERMINAL",
                status_code=400,
            )

        job.status = "cancelling"
        job.cancellation_requested = True
        job.progress_stage = "Cancellation requested..."
        db.commit()

        # Trigger worker thread cancellation
        self.worker.cancel_job(job_id)

        self.audit_service.record_event(
            db=db,
            actor=operator_username,
            role="Operator",
            action="JOB_CANCEL_REQUESTED",
            target_summary=f"Requested cancellation for {job.type} job '{job_id}'",
            result="SUCCESS",
            case_id=job.case_id,
        )

        return job

    def recover_stale_jobs_on_startup(self, db: Session) -> Tuple[int, int]:
        """
        Scans for orphan running/cancelling jobs upon server startup and recovers them:
        Updates status to 'aborted' with explanation and logs audit event.
        Returns (recovered_count, total_aborted).
        """
        now = datetime.now(timezone.utc)
        stale_jobs = db.query(JobRecord).filter(JobRecord.status.in_(["running", "cancelling"])).all()

        count = len(stale_jobs)
        for job in stale_jobs:
            job.status = "aborted"
            job.finished_at = now
            job.error_summary = "Backend server restarted while job was in progress. Job automatically aborted for safety."
            job.progress_stage = "Aborted on backend restart"
            db.commit()

            self.audit_service.record_event(
                db=db,
                actor="SystemRecovery",
                role="System",
                action="JOB_STALE_RECOVERED",
                target_summary=f"Recovered stale job '{job.job_id}' after backend restart -> ABORTED",
                result="ABORTED",
                case_id=job.case_id,
            )

        return count, count
