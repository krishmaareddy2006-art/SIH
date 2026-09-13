"""SQLAlchemy Model for ForensicShield Job Management System."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobRecord(Base):
    """
    Persistent Job record tracking long-running forensic tasks (Sanitization, Recovery, Carving, Erasure).
    Supports state machine transitions: queued, running, cancelling, completed, failed, aborted, manual-review.
    """

    __tablename__ = "job_records"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="SET NULL"), nullable=True, index=True)

    type = Column(String(50), nullable=False, index=True)  # SANITIZATION, RECOVERY, CARVING, ERASURE, INTAKE
    status = Column(String(50), nullable=False, index=True)  # queued, running, cancelling, completed, failed, aborted, manual-review
    target_identifier = Column(String(500), nullable=False)

    progress = Column(Float, nullable=False, default=0.0)
    progress_stage = Column(String(200), nullable=False, default="Queued for processing")
    is_progress_exact = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    cancellation_requested = Column(Boolean, nullable=False, default=False)
    error_summary = Column(Text, nullable=True)
    reason = Column(String(500), nullable=False)
    operator_username = Column(String(100), nullable=False)
    worker_node_id = Column(String(100), nullable=False, default="in-process-worker-1")

    case = relationship("ForensicCase")
