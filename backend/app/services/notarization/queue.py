"""Resilient Offline Queue for Blockchain Notarization Engine.

Queues notarization entries during network timeouts, offline states, or ledger connection
failures. Supports retry flushing with configurable retry bounds.
"""

from datetime import datetime, timezone
from typing import List, Tuple
from app.schemas.notarization import NotarizationEntry, OfflineQueueItem, OfflineQueueStatus
from app.services.notarization.adapter import BaseNotarizationAdapter


class NotarizationOfflineQueue:
    """In-memory offline queue for pending notarization submissions."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._queue: List[OfflineQueueItem] = []

    def enqueue(self, entry: NotarizationEntry, error_msg: str = "") -> None:
        """Enqueues an entry if not already present in pending queue."""
        for item in self._queue:
            if item.entry.digest == entry.digest:
                item.last_error = error_msg
                return

        now = datetime.now(timezone.utc)
        self._queue.append(
            OfflineQueueItem(
                entry=entry,
                retry_count=0,
                enqueued_at=now,
                last_error=error_msg,
            )
        )

    def flush_queue(self, adapter: BaseNotarizationAdapter) -> Tuple[int, int]:
        """
        Attempts to resubmit all pending queue items to the ledger adapter:
        - Successful submissions are removed from queue.
        - Failed attempts increment retry_count; items exceeding max_retries are discarded.
        - Returns (successful_count, remaining_pending_count).
        """
        successful = 0
        remaining: List[OfflineQueueItem] = []

        for item in self._queue:
            try:
                adapter.submit_digest(item.entry)
                successful += 1
            except Exception as e:
                item.retry_count += 1
                item.last_error = str(e)
                if item.retry_count < self.max_retries:
                    remaining.append(item)

        self._queue = remaining
        return successful, len(self._queue)

    def get_status(self, is_network_available: bool = True) -> OfflineQueueStatus:
        """Returns status summary of the offline queue."""
        entries = [item.entry for item in self._queue]
        return OfflineQueueStatus(
            pending_count=len(self._queue),
            max_retries=self.max_retries,
            is_network_available=is_network_available,
            queue_items=entries,
        )

    def clear(self) -> None:
        """Clears the offline queue."""
        self._queue.clear()
