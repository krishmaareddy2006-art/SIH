"""Tamper-Evident Audit Logging REST API Endpoints for ForensicShield."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.audit import AuditEvent
from app.models.auth import User
from app.schemas.audit import AuditChainVerificationResponse, AuditEventResponse, AuditExportResponse
from app.services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()


@router.get("/logs", response_model=List[AuditEventResponse], status_code=status.HTTP_200_OK)
def list_audit_events(
    case_id: Optional[int] = Query(None, description="Filter audit events by forensic case ID"),
    action: Optional[str] = Query(None, description="Filter by action category"),
    actor: Optional[str] = Query(None, description="Filter by actor username"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves paginated audit events with optional case/action/actor filtering."""
    query = db.query(AuditEvent)
    if case_id is not None:
        query = query.filter(AuditEvent.case_id == case_id)
    if action:
        query = query.filter(AuditEvent.action == action)
    if actor:
        query = query.filter(AuditEvent.actor == actor)

    events = query.order_by(AuditEvent.id.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/verify", response_model=AuditChainVerificationResponse, status_code=status.HTTP_200_OK)
def verify_audit_hash_chain(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes cryptographic hash chain integrity verification scan from Genesis to tip.
    Recomputes SHA-256 block digests and checks link integrity. Reports any broken links
    and lists all affected downstream event IDs.
    """
    return audit_service.verify_chain(db)


@router.get("/export/json")
def export_audit_log_json(
    case_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports audit log to JSON format and attaches X-Export-SHA256 header digest."""
    export_bytes, export_hash, count = audit_service.export_audit_log(
        db, export_format="json", case_id=case_id, action=action
    )
    headers = {
        "Content-Disposition": f'attachment; filename="forensic_audit_export_{case_id or "all"}.json"',
        "X-Export-SHA256": export_hash,
    }
    return Response(content=export_bytes, media_type="application/json", headers=headers)


@router.get("/export/csv")
def export_audit_log_csv(
    case_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports audit log to CSV format and attaches X-Export-SHA256 header digest."""
    export_bytes, export_hash, count = audit_service.export_audit_log(
        db, export_format="csv", case_id=case_id, action=action
    )
    headers = {
        "Content-Disposition": f'attachment; filename="forensic_audit_export_{case_id or "all"}.csv"',
        "X-Export-SHA256": export_hash,
    }
    return Response(content=export_bytes, media_type="text/csv", headers=headers)


@router.put("/logs/{event_id}")
@router.delete("/logs/{event_id}")
def prevent_audit_log_modification(event_id: str):
    """Immutability endpoint guard prohibiting modification or deletion of audit events."""
    audit_service.prevent_modification()
