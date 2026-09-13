"""Blockchain Integrity-Notarization REST API Endpoints for ForensicShield."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.auth import User
from app.schemas.notarization import (
    NotarizationReceipt,
    NotarizationSubmitRequest,
    NotarizationVerificationReport,
    OfflineQueueStatus,
)
from app.services.notarization_service import NotarizationService

router = APIRouter()
notarization_service = NotarizationService()


@router.post("/submit", response_model=NotarizationReceipt, status_code=status.HTTP_200_OK)
def submit_notarization(
    request: NotarizationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Notarizes local audit chain tip digest (or custom digest) on the blockchain ledger:
    - Stores ONLY 64-char SHA-256 digest, case pseudonym, event range, timestamp, and network ID.
    - Zero raw evidence, recovered files, passwords, or PII stored on-chain.
    - If network is offline, automatically enqueues into resilient offline queue.
    """
    return notarization_service.notarize_audit_chain(
        db=db, case_id=request.case_id, custom_digest=request.custom_digest
    )


@router.get("/verify", response_model=NotarizationVerificationReport, status_code=status.HTTP_200_OK)
def verify_notarization(
    case_id: Optional[int] = Query(None, description="Case ID to verify"),
    custom_digest: Optional[str] = Query(None, description="Custom 64-char SHA-256 digest to verify"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compares local audit chain digest against notarized blockchain ledger entry:
    - Returns status: 'Match', 'Mismatch', 'Pending', or 'Unavailable'.
    """
    return notarization_service.verify_audit_chain_notarization(
        db=db, case_id=case_id, custom_digest=custom_digest
    )


@router.get("/queue", response_model=OfflineQueueStatus, status_code=status.HTTP_200_OK)
def get_offline_queue_status(
    current_user: User = Depends(get_current_user),
):
    """Retrieves status summary of the offline notarization retry queue."""
    return notarization_service.get_queue_status()


@router.post("/queue/flush", status_code=status.HTTP_200_OK)
def flush_offline_queue(
    current_user: User = Depends(get_current_user),
):
    """Attempts to flush and retry pending notarization entries in offline queue."""
    flushed, remaining = notarization_service.flush_queue()
    return {"successful_flushes": flushed, "remaining_pending": remaining}
