"""Permissioned Blockchain Adapter Interface for ForensicShield Audit Logs.

Provides an abstract interface and mock/simulation implementations for anchoring
local SHA-256 audit log block hashes into a permissioned blockchain ledger.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.models.audit import AuditEvent


class BaseBlockchainAdapter(ABC):
    """Abstract base class for permissioned blockchain log anchoring adapters."""

    @abstractmethod
    def submit_block(self, event: AuditEvent) -> bool:
        """Anchors an audit event hash into the permissioned ledger."""
        pass

    @abstractmethod
    def verify_block(self, event: AuditEvent) -> bool:
        """Verifies if an audit event hash matches the remote anchored ledger entry."""
        pass


class DisabledBlockchainAdapter(BaseBlockchainAdapter):
    """Default no-op blockchain adapter used when external anchoring is disabled."""

    def submit_block(self, event: AuditEvent) -> bool:
        return True

    def verify_block(self, event: AuditEvent) -> bool:
        return True


class SimulatedBlockchainAdapter(BaseBlockchainAdapter):
    """In-memory permissioned blockchain ledger simulation for test environments."""

    def __init__(self):
        self._ledger: Dict[str, str] = {}  # Maps event_id -> current_hash

    def submit_block(self, event: AuditEvent) -> bool:
        self._ledger[event.event_id] = event.current_hash
        return True

    def verify_block(self, event: AuditEvent) -> bool:
        anchored_hash = self._ledger.get(event.event_id)
        if anchored_hash is None:
            return False
        return anchored_hash == event.current_hash

    def get_ledger_count(self) -> int:
        return len(self._ledger)
