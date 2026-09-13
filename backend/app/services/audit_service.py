"""Tamper-Evident Audit Logging Service for ForensicShield.

Provides thread-safe append-only audit event logging, SHA-256 cryptographic hash chaining,
deterministic canonical JSON serialization, chain integrity verification, sensitive data
sanitization, JSON/CSV exports, and permissioned blockchain adapter integration.
"""

import csv
import hashlib
import io
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.models.audit import AuditEvent
from app.schemas.audit import AuditChainVerificationResponse
from app.services.blockchain_adapter import BaseBlockchainAdapter, DisabledBlockchainAdapter

GENESIS_PREVIOUS_HASH = "0" * 64
TOOL_VERSION = "ForensicShield v1.0.0"

_LOCK = threading.Lock()


class AuditService:
    """Core tamper-evident audit logging service."""

    def __init__(self, blockchain_adapter: Optional[BaseBlockchainAdapter] = None):
        self.blockchain_adapter = blockchain_adapter or DisabledBlockchainAdapter()

    @staticmethod
    def sanitize_target_summary(summary: str) -> str:
        """Sanitizes target summary by scrubbing sensitive credentials, tokens, and keys."""
        if not summary:
            return ""
        # Scrub bearer tokens first, then key-value credentials
        scrubbed = re.sub(r"Bearer\s+[\w\.\-]+", "Bearer [REDACTED]", summary)
        scrubbed = re.sub(r"(?i)(password|passwd|secret|authorization|jwt)=[\w\.\-]+", r"\1=[REDACTED]", scrubbed)
        scrubbed = re.sub(r"(?i)token=(?!Bearer\s)[\w\.\-]+", r"token=[REDACTED]", scrubbed)
        return scrubbed[:500]

    @staticmethod
    def format_iso_timestamp(ts) -> str:
        """Formats datetime or string into standardized UTC ISO 8601 string."""
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return ts.isoformat()
        return str(ts)

    @classmethod
    def canonicalize_event(cls, event_dict: Dict) -> str:
        """
        Deterministically serializes event parameters to UTF-8 JSON.
        Keys are sorted alphabetically and whitespace separators are stripped.
        """
        canonical_fields = {
            "event_id": str(event_dict.get("event_id", "")),
            "timestamp": cls.format_iso_timestamp(event_dict.get("timestamp")),
            "clock_source": str(event_dict.get("clock_source", "SERVER_UTC")),
            "actor": str(event_dict.get("actor", "")),
            "role": str(event_dict.get("role", "")),
            "case_id": event_dict.get("case_id"),
            "evidence_id": event_dict.get("evidence_id"),
            "action": str(event_dict.get("action", "")),
            "target_summary": str(event_dict.get("target_summary", "")),
            "result": str(event_dict.get("result", "")),
            "tool_version": str(event_dict.get("tool_version", TOOL_VERSION)),
        }
        return json.dumps(canonical_fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def compute_block_hash(cls, canonical_json: str, previous_hash: str) -> str:
        """Computes current_hash = SHA-256(canonical_event_json + previous_hash)."""
        payload = (canonical_json + previous_hash).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def record_event(
        self,
        db: Session,
        actor: str,
        role: str,
        action: str,
        target_summary: str,
        result: str,
        case_id: Optional[int] = None,
        evidence_id: Optional[str] = None,
    ) -> AuditEvent:
        """
        Thread-safely appends a new AuditEvent to the cryptographic hash chain.
        1. Sanitizes summary string.
        2. Retrieves previous event's current_hash (or GENESIS_PREVIOUS_HASH if empty).
        3. Canonicalizes event parameters and computes SHA-256 block hash.
        4. Persists record and submits block to blockchain adapter.
        """
        with _LOCK:
            now = datetime.now(timezone.utc)

            # Retrieve previous event in chain
            db.expire_all()
            last_event = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
            prev_hash = last_event.current_hash if last_event else GENESIS_PREVIOUS_HASH

            sanitized_summary = self.sanitize_target_summary(target_summary)
            event_id = f"AUDIT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

            event_dict = {
                "event_id": event_id,
                "timestamp": now,
                "clock_source": "SERVER_UTC",
                "actor": actor,
                "role": role,
                "case_id": case_id,
                "evidence_id": evidence_id,
                "action": action,
                "target_summary": sanitized_summary,
                "result": result,
                "tool_version": TOOL_VERSION,
            }

            canonical_json = self.canonicalize_event(event_dict)
            cur_hash = self.compute_block_hash(canonical_json, prev_hash)

            event = AuditEvent(
                event_id=event_id,
                timestamp=now,
                clock_source="SERVER_UTC",
                actor=actor,
                role=role,
                case_id=case_id,
                evidence_id=evidence_id,
                action=action,
                target_summary=sanitized_summary,
                result=result,
                tool_version=TOOL_VERSION,
                previous_hash=prev_hash,
                current_hash=cur_hash,
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            # Submit to optional blockchain ledger adapter
            self.blockchain_adapter.submit_block(event)

            return event

    def verify_chain(self, db: Session) -> AuditChainVerificationResponse:
        """
        Scans all audit events in chronological order (id ASC) and verifies hash chain integrity:
        1. Verifies Genesis block previous_hash == '0'*64.
        2. Verifies previous_hash pointer matches previous event's current_hash.
        3. Recomputes expected SHA-256 block hash for every event.
        4. Reports detailed broken index, first broken event ID, and all affected event IDs if tampered.
        """
        now = datetime.now(timezone.utc)
        db.expire_all()
        events: List[AuditEvent] = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()

        if not events:
            return AuditChainVerificationResponse(
                is_valid=True,
                total_events=0,
                chain_status="INTACT",
                verified_at=now,
            )

        expected_prev = GENESIS_PREVIOUS_HASH

        for idx, event in enumerate(events):
            # 1. Verify previous_hash link match
            if event.previous_hash != expected_prev:
                affected_ids = [e.event_id for e in events[idx:]]
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_events=len(events),
                    chain_status="BROKEN_CHAIN_DETECTED",
                    first_broken_event_id=event.event_id,
                    broken_index=idx,
                    reason=f"Previous hash link broken at sequence index {idx} (Event '{event.event_id}'). Expected previous_hash '{expected_prev}', found '{event.previous_hash}'.",
                    affected_event_ids=affected_ids,
                    verified_at=now,
                )

            # 2. Recompute expected current_hash from canonical event JSON
            event_dict = {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "clock_source": event.clock_source,
                "actor": event.actor,
                "role": event.role,
                "case_id": event.case_id,
                "evidence_id": event.evidence_id,
                "action": event.action,
                "target_summary": event.target_summary,
                "result": event.result,
                "tool_version": event.tool_version,
            }

            canonical_json = self.canonicalize_event(event_dict)
            recalculated_hash = self.compute_block_hash(canonical_json, event.previous_hash)

            if event.current_hash != recalculated_hash:
                affected_ids = [e.event_id for e in events[idx:]]
                return AuditChainVerificationResponse(
                    is_valid=False,
                    total_events=len(events),
                    chain_status="BROKEN_CHAIN_DETECTED",
                    first_broken_event_id=event.event_id,
                    broken_index=idx,
                    reason=f"Field tampering detected at sequence index {idx} (Event '{event.event_id}'). Recalculated block hash '{recalculated_hash}' does not match recorded current_hash '{event.current_hash}'.",
                    affected_event_ids=affected_ids,
                    verified_at=now,
                )

            expected_prev = event.current_hash

        return AuditChainVerificationResponse(
            is_valid=True,
            total_events=len(events),
            chain_status="INTACT",
            verified_at=now,
        )

        return AuditChainVerificationResponse(
            is_valid=True,
            total_events=len(events),
            chain_status="INTACT",
            verified_at=now,
        )

    def export_audit_log(
        self,
        db: Session,
        export_format: str = "json",
        case_id: Optional[int] = None,
        action: Optional[str] = None,
    ) -> Tuple[bytes, str, int]:
        """
        Exports audit events to JSON or CSV format and computes SHA-256 export manifest hash.
        Returns (export_bytes, export_sha256_hash, event_count).
        """
        query = db.query(AuditEvent)
        if case_id is not None:
            query = query.filter(AuditEvent.case_id == case_id)
        if action:
            query = query.filter(AuditEvent.action == action)

        events: List[AuditEvent] = query.order_by(AuditEvent.id.asc()).all()

        if export_format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "id", "event_id", "timestamp", "clock_source", "actor", "role",
                "case_id", "evidence_id", "action", "target_summary", "result",
                "tool_version", "previous_hash", "current_hash"
            ])
            for e in events:
                writer.writerow([
                    e.id, e.event_id, e.timestamp.isoformat(), e.clock_source,
                    e.actor, e.role, e.case_id or "", e.evidence_id or "",
                    e.action, e.target_summary, e.result, e.tool_version,
                    e.previous_hash, e.current_hash
                ])
            export_str = output.getvalue()
            export_bytes = export_str.encode("utf-8")
        else:
            event_dicts = [
                {
                    "id": e.id,
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat(),
                    "clock_source": e.clock_source,
                    "actor": e.actor,
                    "role": e.role,
                    "case_id": e.case_id,
                    "evidence_id": e.evidence_id,
                    "action": e.action,
                    "target_summary": e.target_summary,
                    "result": e.result,
                    "tool_version": e.tool_version,
                    "previous_hash": e.previous_hash,
                    "current_hash": e.current_hash,
                }
                for e in events
            ]
            export_data = {
                "manifest": {
                    "tool_version": TOOL_VERSION,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "event_count": len(events),
                },
                "audit_events": event_dicts,
            }
            export_str = json.dumps(export_data, indent=2)
            export_bytes = export_str.encode("utf-8")

        export_sha256 = hashlib.sha256(export_bytes).hexdigest()
        return export_bytes, export_sha256, len(events)

    @staticmethod
    def prevent_modification():
        """Immutability guard: raises HTTP 403 / Audit log immutable error."""
        raise ForensicShieldException(
            message="Audit events are append-only. Modification or deletion of audit logs is strictly prohibited.",
            code="AUDIT_LOG_IMMUTABLE",
            status_code=403,
        )
