"""Pydantic Schemas for ForensicShield Blockchain Integrity-Notarization Engine.

Strictly enforces privacy rules: stores ONLY digests, case pseudonyms, event ranges,
timestamps, tool versions, and network identifiers. Raw evidence, recovered files,
passwords, and personal information are NEVER stored on-chain.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NotarizationEntry(BaseModel):
    """Anonymized integrity-notarization entry sent to the blockchain ledger."""

    digest: str = Field(..., description="64-character SHA-256 cryptographic digest of local audit log chain tip or artifact state")
    case_pseudonym: str = Field(..., description="Anonymized case pseudonym hash (SHA-256 salt prefix). NEVER real case title or PII.")
    event_range: str = Field(..., description="Audit event sequence range (e.g. 'AUDIT-0001:AUDIT-0050')")
    timestamp: datetime = Field(..., description="UTC ISO timestamp of notarization request")
    tool_version: str = Field("ForensicShield v1.0.0", description="Tool version string")
    network_id: str = Field("mocknet-local-v1", description="Blockchain network or ledger identifier")


class NotarizationReceipt(BaseModel):
    """Receipt returned upon ledger transaction submission."""

    tx_id: str = Field(..., description="Unique ledger transaction hash or transaction ID")
    digest: str = Field(..., description="Notarized SHA-256 digest")
    status: str = Field(..., description="Submission status ('ANCHORED', 'PENDING', 'FAILED')")
    submitted_at: datetime = Field(..., description="UTC timestamp of transaction submission")
    network_id: str = Field(..., description="Network identifier")


class NotarizationSubmitRequest(BaseModel):
    """Request payload to notarize audit log state or custom digest."""

    case_id: Optional[int] = Field(None, description="Optional case ID to anonymize and notarize")
    custom_digest: Optional[str] = Field(None, description="Optional custom 64-char SHA-256 digest to notarize directly")


class NotarizationVerificationReport(BaseModel):
    """Report comparing local audit digest against notarized blockchain ledger entry."""

    status: str = Field(..., description="Verification status: 'Match', 'Mismatch', 'Pending', or 'Unavailable'")
    local_digest: str = Field(..., description="Cryptographic SHA-256 digest computed from local audit chain")
    ledger_digest: Optional[str] = Field(None, description="SHA-256 digest retrieved from notarization ledger")
    tx_id: Optional[str] = Field(None, description="Ledger transaction ID")
    network_id: str = Field(..., description="Target network or ledger identifier")
    case_pseudonym: str = Field(..., description="Anonymized case pseudonym hash")
    event_range: str = Field(..., description="Notarized audit event range")
    notarized_at: Optional[datetime] = Field(None, description="Original ledger notarization timestamp")
    verified_at: datetime = Field(..., description="Timestamp of verification check")
    reason: str = Field(..., description="Detailed forensic explanation of verification result")


class OfflineQueueItem(BaseModel):
    """Item queued for retry during offline or network failure states."""

    entry: NotarizationEntry
    retry_count: int = 0
    enqueued_at: datetime
    last_error: Optional[str] = None


class OfflineQueueStatus(BaseModel):
    """Status summary of the notarization offline retry queue."""

    pending_count: int = Field(..., description="Total items waiting in offline queue")
    max_retries: int = Field(..., description="Configured maximum retries per entry")
    is_network_available: bool = Field(..., description="Current network availability status")
    queue_items: List[NotarizationEntry] = Field(default_factory=list, description="Pending notarization entries")
