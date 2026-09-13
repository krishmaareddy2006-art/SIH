"""SQLAlchemy Model for ForensicShield Tamper-Evident Cryptographic Audit Logging."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditEvent(Base):
    """
    Append-only tamper-evident audit event log record.
    Forms a cryptographically linked SHA-256 hash chain from Genesis.
    """

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    clock_source = Column(String(50), nullable=False, default="SERVER_UTC")

    actor = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_id = Column(String(100), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)
    target_summary = Column(String(500), nullable=False)
    result = Column(String(50), nullable=False)
    tool_version = Column(String(50), nullable=False, default="ForensicShield v1.0.0")

    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)

    case = relationship("ForensicCase")
