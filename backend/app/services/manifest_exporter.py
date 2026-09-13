"""Evidence Manifest Exporter for ForensicShield.

Generates standardized chain-of-custody evidence manifests in JSON and RFC 4180 CSV formats
for court compliance, audit reporting, and offline verification.
"""

import csv
import io
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ForensicShieldException
from app.models.case import ForensicCase, EvidenceItem
from app.schemas.evidence import EvidenceManifestJSON, EvidenceIntakeResponse


class EvidenceManifestExporter:
    """Exports structured chain-of-custody evidence manifests for a forensic case."""

    @staticmethod
    def export_json_manifest(db: Session, case_id: int, operator_username: str = "operator") -> EvidenceManifestJSON:
        """Generates a structured JSON evidence manifest for a case."""
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
        evidence_responses = [EvidenceIntakeResponse.model_validate(item) for item in items]

        return EvidenceManifestJSON(
            manifest_version="1.0.0",
            exported_at=datetime.now(timezone.utc),
            exported_by=operator_username,
            case_id=case.id,
            case_number=case.case_number,
            total_evidence_items=len(evidence_responses),
            evidence_items=evidence_responses,
        )

    @staticmethod
    def export_csv_manifest(db: Session, case_id: int) -> str:
        """Generates an RFC 4180 compliant CSV manifest string for a case."""
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write CSV Header
        writer.writerow([
            "evidence_id",
            "case_id",
            "item_number",
            "title",
            "original_filename",
            "file_path",
            "working_copy_path",
            "file_size_bytes",
            "sha256_hash",
            "import_time",
            "source_description",
            "operator_username",
            "tool_version",
            "processing_status",
            "last_verified_at",
        ])

        # Write Data Rows
        for item in items:
            writer.writerow([
                item.evidence_id,
                item.case_id,
                item.item_number,
                item.title,
                item.original_filename,
                item.file_path,
                item.working_copy_path or "",
                item.file_size_bytes,
                item.sha256_hash,
                item.import_time.isoformat() if item.import_time else "",
                item.source_description or "",
                item.operator_username,
                item.tool_version,
                item.processing_status,
                item.last_verified_at.isoformat() if item.last_verified_at else "",
            ])

        return output.getvalue()
