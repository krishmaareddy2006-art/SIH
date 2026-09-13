"""Forensic Integrity-Notarization Service for ForensicShield.

Orchestrates privacy-preserving blockchain notarization, case pseudonym generation,
local audit chain tip digest submission, status verification (Match, Mismatch, Pending, Unavailable),
and offline queue flushing.
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AuditEvent
from app.schemas.notarization import (
    NotarizationEntry,
    NotarizationReceipt,
    NotarizationVerificationReport,
    OfflineQueueStatus,
)
from app.services.notarization.adapter import (
    BaseNotarizationAdapter,
    DisabledNotarizationAdapter,
    MockLedgerAdapter,
)
from app.services.notarization.queue import NotarizationOfflineQueue

PSEUDO_SALT = "FORENSIC_SHIELD_PSEUDONYM_SALT_V1"


class NotarizationService:
    """High-level service for blockchain integrity notarization."""

    def __init__(
        self,
        adapter: Optional[BaseNotarizationAdapter] = None,
        enabled: Optional[bool] = None,
    ):
        self.enabled = enabled if enabled is not None else settings.ENABLE_BLOCKCHAIN_NOTARIZATION
        if not self.enabled:
            self.adapter = DisabledNotarizationAdapter()
        else:
            self.adapter = adapter or MockLedgerAdapter(network_id=settings.BLOCKCHAIN_NETWORK_ID)
        self.queue = NotarizationOfflineQueue(max_retries=settings.BLOCKCHAIN_MAX_RETRIES)

    @staticmethod
    def generate_case_pseudonym(case_id: Optional[int]) -> str:
        """Generates anonymized case pseudonym hash (zero real case titles or PII)."""
        if case_id is None:
            return "CASE-PSEUDO-GLOBAL"
        raw = f"{PSEUDO_SALT}:{case_id}"
        pseudo_hex = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
        return f"CASE-PSEUDO-{pseudo_hex}"

    def get_local_chain_tip_info(self, db: Session, case_id: Optional[int] = None) -> Tuple[str, str]:
        """
        Retrieves the latest current_hash and event range from local audit_events table:
        Returns (tip_digest, event_range).
        """
        query = db.query(AuditEvent)
        if case_id is not None:
            query = query.filter(AuditEvent.case_id == case_id)

        first_event = query.order_by(AuditEvent.id.asc()).first()
        last_event = query.order_by(AuditEvent.id.desc()).first()

        if not last_event or not first_event:
            return "0" * 64, "AUDIT-EMPTY"

        tip_digest = last_event.current_hash
        event_range = f"{first_event.event_id}:{last_event.event_id}"
        return tip_digest, event_range

    def notarize_audit_chain(
        self,
        db: Session,
        case_id: Optional[int] = None,
        custom_digest: Optional[str] = None,
    ) -> NotarizationReceipt:
        """
        Notarizes local audit chain tip digest (or custom digest) on the ledger:
        1. Checks feature flag.
        2. Generates case pseudonym and event range.
        3. Attempts ledger submission via adapter.
        4. If network fails/offline, enqueues item into offline queue and returns PENDING status.
        """
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return self.adapter.submit_digest(
                NotarizationEntry(
                    digest=custom_digest or "0" * 64,
                    case_pseudonym=self.generate_case_pseudonym(case_id),
                    event_range="AUDIT-DISABLED",
                    timestamp=now,
                    network_id="disabled",
                )
            )

        if custom_digest:
            tip_digest = custom_digest
            event_range = "CUSTOM-DIGEST"
        else:
            tip_digest, event_range = self.get_local_chain_tip_info(db, case_id=case_id)

        case_pseudonym = self.generate_case_pseudonym(case_id)
        entry = NotarizationEntry(
            digest=tip_digest,
            case_pseudonym=case_pseudonym,
            event_range=event_range,
            timestamp=now,
            tool_version="ForensicShield v1.0.0",
            network_id=settings.BLOCKCHAIN_NETWORK_ID,
        )

        try:
            receipt = self.adapter.submit_digest(entry)
            return receipt
        except (ConnectionError, Exception) as e:
            # Resilient fallback: enqueue for retry flushing
            self.queue.enqueue(entry, error_msg=str(e))
            return NotarizationReceipt(
                tx_id="TX-QUEUED-OFFLINE",
                digest=tip_digest,
                status="PENDING",
                submitted_at=now,
                network_id=settings.BLOCKCHAIN_NETWORK_ID,
            )

    def verify_audit_chain_notarization(
        self,
        db: Session,
        case_id: Optional[int] = None,
        custom_digest: Optional[str] = None,
    ) -> NotarizationVerificationReport:
        """
        Compares local audit chain tip digest against notarized ledger:
        Returns status: Match, Mismatch, Pending, or Unavailable.
        """
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return NotarizationVerificationReport(
                status="Unavailable",
                local_digest=custom_digest or "0" * 64,
                ledger_digest=None,
                tx_id=None,
                network_id="disabled",
                case_pseudonym=self.generate_case_pseudonym(case_id),
                event_range="AUDIT-DISABLED",
                verified_at=now,
                reason="Blockchain notarization is disabled via feature flag (ENABLE_BLOCKCHAIN_NOTARIZATION=False).",
            )

        if custom_digest:
            tip_digest = custom_digest
            event_range = "CUSTOM-DIGEST"
        else:
            tip_digest, event_range = self.get_local_chain_tip_info(db, case_id=case_id)

        case_pseudonym = self.generate_case_pseudonym(case_id)

        return self.adapter.verify_digest(
            local_digest=tip_digest,
            case_pseudonym=case_pseudonym,
            event_range=event_range,
        )

    def flush_queue(self) -> Tuple[int, int]:
        """Flushes pending offline queue items."""
        return self.queue.flush_queue(self.adapter)

    def get_queue_status(self) -> OfflineQueueStatus:
        """Returns pending offline queue status."""
        return self.queue.get_status(is_network_available=self.enabled)
