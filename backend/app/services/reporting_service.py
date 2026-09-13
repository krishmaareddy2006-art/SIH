"""Forensic Report Generation & Compliance Service for ForensicShield.

Generates court-compliant PDF reports (using ReportLab) and machine-readable JSON manifests.
Enforces forensic language compliance, status classification (Verified, Inconclusive, Failed, Unsupported,
Manual Review), mandatory technical limitations disclaimers, report SHA-256 digests, and tamper-evident audit logging.
"""

import hashlib
import io
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings
from app.core.exceptions import ForensicShieldException
from app.models.audit import AuditEvent
from app.models.case import CarvedFileArtifact, EvidenceItem, ForensicCase, RecoveredArtifact
from app.models.job import JobRecord
from app.schemas.reporting import (
    ForensicReportRequest,
    ForensicReportResponse,
    ReportMetadata,
    ReportSummary,
    StatusClassificationCounts,
)
from app.services.audit_service import AuditService

REPORT_ENGINE_VERSION = "v1.0.0-reporter"
TOOL_VERSION = "ForensicShield v1.0.0"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for adding running footers with 'Page X of Y' and UTC timestamps."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Footer Line
        self.setLineWidth(0.5)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.line(36, 36, 576, 36)

        # Footer Text
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        footer_text = f"ForensicShield Evidence Report | Generated {now_str} | CONFIDENTIAL"
        page_text = f"Page {self._pageNumber} of {page_count}"

        self.drawString(36, 24, footer_text)
        self.drawRightString(576, 24, page_text)
        self.restoreState()


class ForensicReportService:
    """Core service for generating PDF reports, JSON manifests, and report auditing."""

    def __init__(self, audit_service: Optional[AuditService] = None):
        self.audit_service = audit_service or AuditService()

    @staticmethod
    def enforce_compliance_language(text: str) -> str:
        """
        Enforces forensic language compliance policy:
        Prohibits absolute uncalibrated claims such as '100% unrecoverable' or 'impossible to recover'.
        Replaces them with compliant forensic terminology.
        """
        if not text:
            return ""

        replacements = [
            (r"(?i)100%\s+unrecoverable", "Logical sanitization verified under test protocol"),
            (r"(?i)guaranteed\s+unrecoverable", "No recoverable sector extents detected"),
            (r"(?i)impossible\s+to\s+recover", "No file entry boundaries identified"),
            (r"(?i)100%\s+wiped", "Logical overwrite pattern applied"),
            (r"(?i)perfect\s+erasure", "Verified file unlink and cluster release"),
            # Sensitive Data Redaction
            (r"(?i)password\s*=\s*[^\s,;]+", "password=[REDACTED]"),
            (r"(?i)token\s*=\s*Bearer\s+[^\s,;]+", "token=Bearer [REDACTED]"),
            (r"(?i)Bearer\s+eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_=]*", "Bearer [REDACTED]"),
            (r"(?i)secret\s*=\s*[^\s,;]+", "secret=[REDACTED]"),
        ]

        cleaned = text
        for pattern, repl in replacements:
            cleaned = re.sub(pattern, repl, cleaned)
        return cleaned

    def collect_case_data(self, db: Session, case_id: int) -> Dict:
        """Collects all case evidence, recovery artifacts, carving artifacts, and audit chain details."""
        case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
        if not case:
            raise ForensicShieldException(
                message=f"Forensic Case with ID {case_id} not found.",
                code="CASE_NOT_FOUND",
                status_code=404,
            )

        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
        recovered_artifacts = db.query(RecoveredArtifact).filter(RecoveredArtifact.case_id == case_id).all()
        carved_artifacts = db.query(CarvedFileArtifact).filter(CarvedFileArtifact.case_id == case_id).all()
        audit_events = db.query(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.id.asc()).all()

        # Audit Chain Verification
        chain_verification = self.audit_service.verify_chain(db)

        # Status Classification Matrix
        verified_cnt = 0
        inconclusive_cnt = 0
        failed_cnt = 0
        unsupported_cnt = 0
        manual_review_cnt = 0

        # Classify Evidence
        for ev in evidence_items:
            if ev.processing_status == "COMPLETED":
                verified_cnt += 1
            elif ev.processing_status == "INTEGRITY_FAILURE":
                failed_cnt += 1
            else:
                inconclusive_cnt += 1

        # Classify Recovered Files
        for rec in recovered_artifacts:
            if rec.classification_status == "RECOVERABLE":
                verified_cnt += 1
            elif rec.classification_status == "PARTIALLY_RECOVERABLE":
                inconclusive_cnt += 1
            elif rec.classification_status == "CORRUPTED":
                failed_cnt += 1
            elif rec.classification_status == "UNSUPPORTED":
                unsupported_cnt += 1
            else:
                manual_review_cnt += 1

        # Classify Carved Files
        for carv in carved_artifacts:
            if carv.confidence_level == "HIGH":
                verified_cnt += 1
            elif carv.confidence_level == "MEDIUM":
                inconclusive_cnt += 1
            else:
                manual_review_cnt += 1

        total_evidence_bytes = sum(e.file_size_bytes or 0 for e in evidence_items)

        return {
            "case": case,
            "evidence_items": evidence_items,
            "recovered_artifacts": recovered_artifacts,
            "carved_artifacts": carved_artifacts,
            "audit_events": audit_events,
            "chain_verification": chain_verification,
            "summary": {
                "evidence_count": len(evidence_items),
                "total_evidence_bytes": total_evidence_bytes,
                "carved_artifacts_count": len(carved_artifacts),
                "recovered_artifacts_count": len(recovered_artifacts),
                "audit_events_count": len(audit_events),
                "audit_chain_status": "INTACT" if chain_verification.is_valid else "BROKEN_CHAIN_DETECTED",
            },
            "classifications": {
                "verified": verified_cnt,
                "inconclusive": inconclusive_cnt,
                "failed": failed_cnt,
                "unsupported": unsupported_cnt,
                "manual_review": manual_review_cnt,
            },
        }

    def generate_json_manifest(self, case_data: Dict, report_id: str, operator_username: str) -> Tuple[bytes, str]:
        """Generates machine-readable JSON manifest and returns (json_bytes, sha256_hash)."""
        case: ForensicCase = case_data["case"]
        now = datetime.now(timezone.utc)

        manifest = {
            "report_metadata": {
                "report_id": report_id,
                "case_id": case.id,
                "case_number": case.case_number,
                "case_title": self.enforce_compliance_language(case.title),
                "generated_at": now.isoformat(),
                "generated_by": operator_username,
                "tool_version": TOOL_VERSION,
                "environment": settings.ENVIRONMENT,
            },
            "summary_statistics": case_data["summary"],
            "status_classifications": case_data["classifications"],
            "evidence_inventory": [
                {
                    "evidence_id": e.evidence_id,
                    "item_number": e.item_number,
                    "original_name": getattr(e, "original_filename", getattr(e, "original_name", "")),
                    "size_bytes": e.file_size_bytes,
                    "sha256": e.sha256_hash,
                    "import_time": e.import_time.isoformat() if e.import_time else None,
                    "status": e.processing_status,
                }
                for e in case_data["evidence_items"]
            ],
            "recovered_artifacts": [
                {
                    "artifact_id": r.artifact_id,
                    "original_path": r.original_path,
                    "recovered_hash": r.recovered_file_hash,
                    "source_offset": r.source_offset_bytes,
                    "size_bytes": r.file_size_bytes,
                    "status": r.classification_status,
                    "filesystem": r.filesystem_type,
                }
                for r in case_data["recovered_artifacts"]
            ],
            "carved_artifacts": [
                {
                    "carved_id": c.carved_id,
                    "format": c.file_format,
                    "carved_hash": c.carved_file_hash,
                    "start_offset": c.source_start_offset,
                    "end_offset": c.source_end_offset,
                    "confidence_level": c.confidence_level,
                    "validation_details": self.enforce_compliance_language(c.validation_details or ""),
                }
                for c in case_data["carved_artifacts"]
            ],
            "audit_chain_verification": {
                "is_valid": case_data["chain_verification"].is_valid,
                "total_events": case_data["chain_verification"].total_events,
                "chain_status": case_data["chain_verification"].chain_status,
                "first_broken_event_id": case_data["chain_verification"].first_broken_event_id,
            },
        }

        json_str = json.dumps(manifest, indent=2, ensure_ascii=False)
        json_bytes = json_str.encode("utf-8")
        json_sha256 = hashlib.sha256(json_bytes).hexdigest()
        return json_bytes, json_sha256

    def generate_pdf_report(self, case_data: Dict, report_id: str, operator_username: str) -> Tuple[bytes, str]:
        """Generates professional ReportLab PDF report and returns (pdf_bytes, sha256_hash)."""
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
        )

        limitation_style = ParagraphStyle(
            "LimitationText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#451a03"),
        )

        story = []
        case: ForensicCase = case_data["case"]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # ---------------------------------------------------------
        # Header Banner
        # ---------------------------------------------------------
        header_data = [
            [
                Paragraph("<font color='white'><b>FORENSICSHIELD COMPLIANCE REPORT</b></font>", title_style),
                Paragraph(f"<font color='white'><b>Report ID:</b> {report_id}<br/><b>Case #:</b> {case.case_number}</font>", ParagraphStyle("HRight", parent=body_style, alignment=2)),
            ]
        ]
        header_table = Table(header_data, colWidths=[340, 200])
        header_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 14))

        # ---------------------------------------------------------
        # Section 1: Case & Metadata Summary
        # ---------------------------------------------------------
        story.append(Paragraph("1. Executive & Metadata Summary", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        meta_data = [
            [Paragraph("<b>Case Title:</b>", body_style), Paragraph(self.enforce_compliance_language(case.title), body_style), Paragraph("<b>Generated At:</b>", body_style), Paragraph(now_str, body_style)],
            [Paragraph("<b>Case Number:</b>", body_style), Paragraph(case.case_number, body_style), Paragraph("<b>Generated By:</b>", body_style), Paragraph(operator_username, body_style)],
            [Paragraph("<b>Tool Version:</b>", body_style), Paragraph(TOOL_VERSION, body_style), Paragraph("<b>Audit Chain Status:</b>", body_style), Paragraph(f"<b>{case_data['summary']['audit_chain_status']}</b>", body_style)],
        ]
        meta_table = Table(meta_data, colWidths=[100, 170, 110, 160])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # ---------------------------------------------------------
        # Section 2: 5-Point Status Classification Matrix
        # ---------------------------------------------------------
        story.append(Paragraph("2. Forensic Status Classification Breakdown", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        cls = case_data["classifications"]
        cls_data = [
            [
                Paragraph("Status Category", table_header_style),
                Paragraph("Verified", table_header_style),
                Paragraph("Inconclusive", table_header_style),
                Paragraph("Failed", table_header_style),
                Paragraph("Unsupported", table_header_style),
                Paragraph("Manual Review", table_header_style),
            ],
            [
                Paragraph("<b>Item Count</b>", table_cell_style),
                Paragraph(str(cls["verified"]), table_cell_style),
                Paragraph(str(cls["inconclusive"]), table_cell_style),
                Paragraph(str(cls["failed"]), table_cell_style),
                Paragraph(str(cls["unsupported"]), table_cell_style),
                Paragraph(str(cls["manual_review"]), table_cell_style),
            ],
        ]
        cls_table = Table(cls_data, colWidths=[110, 85, 85, 85, 87, 88])
        cls_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(cls_table)
        story.append(Spacer(1, 14))

        # ---------------------------------------------------------
        # Section 3: Evidence Inventory
        # ---------------------------------------------------------
        story.append(Paragraph("3. Read-Only Evidence Image Inventory", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        ev_rows = [
            [
                Paragraph("Evidence ID", table_header_style),
                Paragraph("Item #", table_header_style),
                Paragraph("Original Name", table_header_style),
                Paragraph("Size (Bytes)", table_header_style),
                Paragraph("SHA-256 Digest", table_header_style),
                Paragraph("Status", table_header_style),
            ]
        ]
        for e in case_data["evidence_items"]:
            ev_rows.append([
                Paragraph(e.evidence_id, table_cell_style),
                Paragraph(e.item_number, table_cell_style),
                Paragraph(getattr(e, "original_filename", getattr(e, "original_name", ""))[:20], table_cell_style),
                Paragraph(f"{e.file_size_bytes:,}", table_cell_style),
                Paragraph(f"{e.sha256_hash[:16]}...", table_cell_style),
                Paragraph(e.processing_status, table_cell_style),
            ])

        if len(ev_rows) == 1:
            ev_rows.append([Paragraph("No evidence items registered for this case.", table_cell_style)] + [Paragraph("", table_cell_style)]*5)

        ev_table = Table(ev_rows, colWidths=[95, 65, 110, 70, 110, 90])
        ev_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(ev_table)
        story.append(Spacer(1, 14))

        # ---------------------------------------------------------
        # Section 4: Carved & Recovered Artifacts
        # ---------------------------------------------------------
        story.append(Paragraph("4. Recovered & Carved Forensic Artifacts", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        art_rows = [
            [
                Paragraph("Artifact ID", table_header_style),
                Paragraph("Type / Format", table_header_style),
                Paragraph("Source Offset", table_header_style),
                Paragraph("SHA-256 Digest", table_header_style),
                Paragraph("Confidence / Status", table_header_style),
            ]
        ]
        for c in case_data["carved_artifacts"]:
            art_rows.append([
                Paragraph(c.carved_id, table_cell_style),
                Paragraph(f"Carved {c.file_format}", table_cell_style),
                Paragraph(f"{c.source_start_offset:,}", table_cell_style),
                Paragraph(f"{c.carved_file_hash[:16]}...", table_cell_style),
                Paragraph(f"Confidence: {c.confidence_level}", table_cell_style),
            ])
        for r in case_data["recovered_artifacts"]:
            art_rows.append([
                Paragraph(r.artifact_id, table_cell_style),
                Paragraph(f"Rec ({r.filesystem_type})", table_cell_style),
                Paragraph(f"{r.source_offset_bytes:,}", table_cell_style),
                Paragraph(f"{r.recovered_file_hash[:16]}...", table_cell_style),
                Paragraph(r.classification_status, table_cell_style),
            ])

        if len(art_rows) == 1:
            art_rows.append([Paragraph("No extracted artifacts recorded for this case.", table_cell_style)] + [Paragraph("", table_cell_style)]*4)

        art_table = Table(art_rows, colWidths=[110, 95, 85, 130, 120])
        art_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(art_table)
        story.append(Spacer(1, 14))

        # ---------------------------------------------------------
        # Section 5: Mandatory Technical Limitations & Boundaries
        # ---------------------------------------------------------
        story.append(KeepTogether([
            Paragraph("5. Technical Limitations & Forensic Scope", h2_style),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8),
            Table([
                [
                    Paragraph(
                        "<b>MANDATORY FORENSIC BOUNDARIES & TECHNICAL DISCLAIMERS:</b><br/>"
                        "1. <b>Storage Media Differences:</b> Magnetic HDDs support direct block overwriting. SSDs and NVMe drives utilize Flash Translation Layers (FTL), wear-leveling algorithms, and over-provisioned blocks. Logical sector overwriting does not guarantee sanitization of unmapped physical NAND blocks.<br/>"
                        "2. <b>Filesystem Boundaries:</b> Filesystem recovery is restricted to supported structures (FAT32, NTFS, Ext4). Damaged or unknown volumes require manual review.<br/>"
                        "3. <b>Signature Carving & Fragmentation:</b> Pure signature carving assumes contiguous block allocation. Carving non-contiguous fragmented files without allocation metadata produces corrupt byte streams.<br/>"
                        "4. <b>Validation Scoring Heuristics:</b> Validation scores (0-100) represent an empirical heuristic structural index and are NOT statistical probabilities of truth.<br/>"
                        "5. <b>Compliance Phrasing Notice:</b> Absolute claims ('100% unrecoverable') are excluded under ISO/IEC 27037 standards.",
                        limitation_style,
                    )
                ]
            ], colWidths=[540], style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fdba74")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]),
        ]))

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        return pdf_bytes, pdf_sha256

    def generate_case_report(
        self,
        db: Session,
        case_id: int,
        operator_username: str,
        request_params: Optional[ForensicReportRequest] = None,
    ) -> ForensicReportResponse:
        """
        Orchestrates forensic report generation:
        1. Collects case evidence data & runs compliance scrubber.
        2. Generates JSON manifest & computes json_sha256.
        3. Generates PDF report & computes pdf_sha256.
        4. Registers FORENSIC_REPORT_GENERATED audit event in audit log chain.
        5. Saves output files to reports/case_{case_id}/.
        6. Returns ForensicReportResponse.
        """
        case_data = self.collect_case_data(db, case_id=case_id)

        now = datetime.now(timezone.utc)
        report_id = f"RPT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        # Setup output directory
        reports_dir = Path("reports") / f"case_{case_id}"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate JSON Manifest
        json_bytes, json_sha256 = self.generate_json_manifest(case_data, report_id, operator_username)
        json_file_path = reports_dir / f"{report_id}_manifest.json"
        json_file_path.write_bytes(json_bytes)

        # 2. Generate PDF Report
        pdf_bytes, pdf_sha256 = self.generate_pdf_report(case_data, report_id, operator_username)
        pdf_file_path = reports_dir / f"{report_id}_report.pdf"
        pdf_file_path.write_bytes(pdf_bytes)

        # 3. Register Report Hash in Tamper-Evident Audit Chain
        audit_event = self.audit_service.record_event(
            db=db,
            actor=operator_username,
            role="Operator",
            action="FORENSIC_REPORT_GENERATED",
            target_summary=f"Generated Forensic PDF ({pdf_sha256[:16]}...) & JSON Manifest ({json_sha256[:16]}...) for Report '{report_id}'",
            result="SUCCESS",
            case_id=case_id,
        )

        summary_obj = ReportSummary(**case_data["summary"])
        class_obj = StatusClassificationCounts(**case_data["classifications"])

        return ForensicReportResponse(
            report_id=report_id,
            case_id=case_id,
            generated_at=now,
            pdf_sha256=pdf_sha256,
            json_sha256=json_sha256,
            audit_event_id=audit_event.event_id,
            pdf_download_url=f"/api/v1/cases/{case_id}/reports/{report_id}/download/pdf",
            json_download_url=f"/api/v1/cases/{case_id}/reports/{report_id}/download/json",
            summary=summary_obj,
            classifications=class_obj,
        )
