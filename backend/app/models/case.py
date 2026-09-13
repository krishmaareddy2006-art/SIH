"""SQLAlchemy Database Models for Cases, Access Control, and Evidence Items."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ForensicCase(Base):
    """Forensic Case record tracking evidence metadata, investigator assignment, and status."""

    __tablename__ = "forensic_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="OPEN", index=True)  # OPEN, CLOSED
    investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    investigator = relationship("User", foreign_keys=[investigator_id], lazy="joined")
    evidence_items = relationship("EvidenceItem", back_populates="case", cascade="all, delete-orphan")
    access_grants = relationship("CaseAccess", back_populates="case", cascade="all, delete-orphan")


class CaseAccess(Base):
    """Explicit access mapping granting specific users permission to access a case (IDOR control)."""

    __tablename__ = "case_access"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ForensicCase", back_populates="access_grants")
    user = relationship("User", foreign_keys=[user_id])


class EvidenceItem(Base):
    """Forensic Evidence Item attached to a specific case with strict chain-of-custody tracking."""

    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(100), unique=True, index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    item_number = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Immutable reference to source image
    working_copy_path = Column(String(500), nullable=True)  # Path to read-only working copy
    sha256_hash = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(BigInteger, nullable=False)
    import_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_description = Column(Text, nullable=True)
    operator_username = Column(String(100), nullable=False)
    tool_version = Column(String(50), nullable=False, default="ForensicShield v1.0.0")
    processing_status = Column(String(50), default="IMPORTED", index=True)  # IMPORTED, VERIFIED, INTEGRITY_FAILURE, PROCESSING, COMPLETED
    last_verified_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="UNTOUCHED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ForensicCase", back_populates="evidence_items")


class AuditLogRecord(Base):
    """Structured audit log entry persisted in database for system-wide auditing."""

    __tablename__ = "audit_log_records"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True, nullable=True)
    case_id = Column(String(100), index=True, nullable=True)
    user_id = Column(String(100), index=True, nullable=True)
    operation = Column(String(100), index=True, nullable=False)
    status = Column(String(50), index=True, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class RecoveredArtifact(Base):
    """Forensic Artifact recovered from filesystem scan with complete provenance tracking."""

    __tablename__ = "recovered_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    artifact_id = Column(String(100), unique=True, index=True, nullable=False)
    candidate_id = Column(String(100), nullable=True, index=True)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_evidence_id = Column(String(100), nullable=False, index=True)

    original_path = Column(String(500), nullable=False)
    output_file_path = Column(String(500), nullable=False)
    recovered_file_hash = Column(String(64), nullable=False, index=True)
    source_image_hash = Column(String(64), nullable=False)
    source_offset_bytes = Column(BigInteger, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    classification_status = Column(String(50), nullable=False)  # RECOVERABLE, PARTIALLY_RECOVERABLE, METADATA_ONLY, CORRUPTED, UNSUPPORTED
    filesystem_type = Column(String(50), nullable=False)  # FAT32, NTFS, EXT4, UNSUPPORTED
    recovery_method = Column(String(100), nullable=False)
    tool_version = Column(String(50), nullable=False, default="ForensicShield v1.0.0")
    operator_username = Column(String(100), nullable=False)
    recovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class CarvedFileArtifact(Base):
    """Forensic File Carved Artifact extracted via signature-based carving."""

    __tablename__ = "carved_file_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    carved_id = Column(String(100), unique=True, index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("forensic_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_evidence_id = Column(String(100), nullable=False, index=True)
    file_format = Column(String(20), nullable=False, index=True)  # JPEG, PNG, PDF, ZIP
    output_file_path = Column(String(500), nullable=False)
    carved_file_hash = Column(String(64), nullable=False, index=True)
    source_image_hash = Column(String(64), nullable=False)
    source_start_offset = Column(BigInteger, nullable=False)
    source_end_offset = Column(BigInteger, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    confidence_level = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    validation_details = Column(Text, nullable=True)
    scan_version = Column(String(50), nullable=False, default="v1.0.0-carver")
    tool_version = Column(String(50), nullable=False, default="ForensicShield v1.0.0")
    operator_username = Column(String(100), nullable=False)
    carved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("ForensicCase")




