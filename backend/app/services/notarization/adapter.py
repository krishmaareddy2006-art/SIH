"""Notarization Adapter Interfaces & Mock Implementations for ForensicShield.

Provides abstract BaseNotarizationAdapter, DisabledNotarizationAdapter (feature flag disabled),
and MockLedgerAdapter (offline-first local mock ledger with network failure simulation).
"""

import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Optional

from app.schemas.notarization import (
    NotarizationEntry,
    NotarizationReceipt,
    NotarizationVerificationReport,
)


class BaseNotarizationAdapter(ABC):
    """Abstract base class for integrity-notarization adapters."""

    @abstractmethod
    def submit_digest(self, entry: NotarizationEntry) -> NotarizationReceipt:
        """Submits an anonymized integrity digest to the notarization ledger."""
        pass

    @abstractmethod
    def get_digest(self, digest_or_tx: str) -> Optional[NotarizationEntry]:
        """Retrieves a notarized entry by digest string or transaction ID."""
        pass

    @abstractmethod
    def verify_digest(
        self,
        local_digest: str,
        case_pseudonym: str,
        event_range: str,
    ) -> NotarizationVerificationReport:
        """Compares local digest against notarized ledger record and returns status."""
        pass


class DisabledNotarizationAdapter(BaseNotarizationAdapter):
    """Default adapter returned when ENABLE_BLOCKCHAIN_NOTARIZATION is false."""

    def submit_digest(self, entry: NotarizationEntry) -> NotarizationReceipt:
        now = datetime.now(timezone.utc)
        return NotarizationReceipt(
            tx_id="TX-DISABLED",
            digest=entry.digest,
            status="FAILED",
            submitted_at=now,
            network_id=entry.network_id,
        )

    def get_digest(self, digest_or_tx: str) -> Optional[NotarizationEntry]:
        return None

    def verify_digest(
        self,
        local_digest: str,
        case_pseudonym: str,
        event_range: str,
    ) -> NotarizationVerificationReport:
        now = datetime.now(timezone.utc)
        return NotarizationVerificationReport(
            status="Unavailable",
            local_digest=local_digest,
            ledger_digest=None,
            tx_id=None,
            network_id="disabled",
            case_pseudonym=case_pseudonym,
            event_range=event_range,
            verified_at=now,
            reason="Blockchain notarization is disabled via feature flag (ENABLE_BLOCKCHAIN_NOTARIZATION=False).",
        )


class MockLedgerAdapter(BaseNotarizationAdapter):
    """
    Offline-first in-memory mock ledger simulating a permissioned blockchain node.
    Supports network failure toggles, offline mode, and idempotency.
    """

    def __init__(self, network_id: str = "mocknet-local-v1"):
        self.network_id = network_id
        self._ledger_by_digest: Dict[str, NotarizationEntry] = {}
        self._ledger_by_tx: Dict[str, NotarizationEntry] = {}
        self._receipts: Dict[str, NotarizationReceipt] = {}
        
        # Test simulation flags
        self.is_offline: bool = False
        self.simulate_network_error: bool = False

    def submit_digest(self, entry: NotarizationEntry) -> NotarizationReceipt:
        """
        Idempotently submits notarization entry to mock ledger:
        - If offline / network error set, raises ConnectionError.
        - If digest already exists, returns existing receipt (Idempotency guarantee).
        - Else registers block in ledger.
        """
        if self.is_offline or self.simulate_network_error:
            raise ConnectionError("Blockchain ledger network is offline or unreachable.")

        # Idempotency check: return existing receipt if digest already notarized
        if entry.digest in self._ledger_by_digest:
            return self._receipts[entry.digest]

        now = datetime.now(timezone.utc)
        tx_hash = f"0x{hashlib.sha256((entry.digest + str(now.timestamp())).encode('utf-8')).hexdigest()[:40]}"

        receipt = NotarizationReceipt(
            tx_id=tx_hash,
            digest=entry.digest,
            status="ANCHORED",
            submitted_at=now,
            network_id=self.network_id,
        )

        self._ledger_by_digest[entry.digest] = entry
        self._ledger_by_tx[tx_hash] = entry
        self._receipts[entry.digest] = receipt

        return receipt

    def get_digest(self, digest_or_tx: str) -> Optional[NotarizationEntry]:
        """Retrieves notarized entry by digest or tx_id."""
        if self.is_offline or self.simulate_network_error:
            raise ConnectionError("Blockchain ledger network is offline or unreachable.")

        if digest_or_tx in self._ledger_by_digest:
            return self._ledger_by_digest[digest_or_tx]
        if digest_or_tx in self._ledger_by_tx:
            return self._ledger_by_tx[digest_or_tx]
        return None

    def verify_digest(
        self,
        local_digest: str,
        case_pseudonym: str,
        event_range: str,
    ) -> NotarizationVerificationReport:
        """
        Compares local chain tip digest against mock ledger:
        - Returns 'Unavailable' if network is offline.
        - Returns 'Pending' if digest not found.
        - Returns 'Match' if local_digest == ledger_digest.
        - Returns 'Mismatch' if local_digest != ledger_digest.
        """
        now = datetime.now(timezone.utc)
        if self.is_offline or self.simulate_network_error:
            return NotarizationVerificationReport(
                status="Unavailable",
                local_digest=local_digest,
                ledger_digest=None,
                tx_id=None,
                network_id=self.network_id,
                case_pseudonym=case_pseudonym,
                event_range=event_range,
                verified_at=now,
                reason="Blockchain notarization ledger is currently offline or unreachable.",
            )

        entry = self.get_digest(local_digest)
        if not entry:
            return NotarizationVerificationReport(
                status="Pending",
                local_digest=local_digest,
                ledger_digest=None,
                tx_id=None,
                network_id=self.network_id,
                case_pseudonym=case_pseudonym,
                event_range=event_range,
                verified_at=now,
                reason="Local digest has not yet been notarized on the blockchain ledger (Status: Pending).",
            )

        receipt = self._receipts.get(local_digest)
        tx_id = receipt.tx_id if receipt else None

        if entry.digest == local_digest:
            return NotarizationVerificationReport(
                status="Match",
                local_digest=local_digest,
                ledger_digest=entry.digest,
                tx_id=tx_id,
                network_id=self.network_id,
                case_pseudonym=case_pseudonym,
                event_range=event_range,
                notarized_at=entry.timestamp,
                verified_at=now,
                reason="Local audit chain digest matches notarized blockchain ledger entry exactly.",
            )

        return NotarizationVerificationReport(
            status="Mismatch",
            local_digest=local_digest,
            ledger_digest=entry.digest,
            tx_id=tx_id,
            network_id=self.network_id,
            case_pseudonym=case_pseudonym,
            event_range=event_range,
            notarized_at=entry.timestamp,
            verified_at=now,
            reason=f"CRITICAL DISCREPANCY: Local digest '{local_digest[:16]}...' does NOT match ledger digest '{entry.digest[:16]}...'. Possible local chain tampering or divergence.",
        )
