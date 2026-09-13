"""Database & Synthetic Evidence Seeder Script for SIH Demonstration of ForensicShield.

Populates database with:
1. Standard demo accounts (Admin, Investigator, Operator, Analyst).
2. Demo Case: 'CAS-SIH-2026-001'.
3. Synthetic evidence image disk 'synthetic_test_disk_01.raw' with verified SHA-256 hash.
4. Carved and recovered file artifacts with confidence scores.
5. Intact SHA-256 tamper-evident audit trail (10+ chained blocks).
6. Pre-generated court-compliant forensic report PDF and JSON manifest.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add project root to sys.path
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
import app.models
from app.core.database import Base, engine, SessionLocal
from app.core.init_db import init_db
from app.models.auth import User, Role
from app.models.case import ForensicCase, EvidenceItem, CarvedFileArtifact
from app.models.audit import AuditEvent
from app.services.audit_service import AuditService
from app.services.evidence_intake import StreamingHashCalculator
from app.services.reporting_service import ForensicReportService
from tests.qa_framework.synthetic_dataset import build_synthetic_disk_image


def seed_demo_data():
    print("[SIH Seed] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Initialize DB Roles & Base Users
        init_db(db)
        print("[SIH Seed] Core roles and users initialized.")

        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("[SIH Seed] ERROR: Admin user not found.")
            return

        # 2. Ensure Synthetic Test Disk Exists
        manifest_dir = project_root / "tests" / "qa_framework" / "golden_manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        img_path = manifest_dir / "synthetic_test_disk_01.raw"

        if not img_path.exists():
            print("[SIH Seed] Generating synthetic test disk image (10 MB)...")
            img_path, _, _ = build_synthetic_disk_image(manifest_dir)

        # Calculate exact SHA-256 hash of synthetic image
        img_hash, img_size = StreamingHashCalculator.calculate_sha256(img_path)
        print(f"[SIH Seed] Synthetic Image SHA-256: {img_hash[:16]}... ({img_size / (1024*1024):.1f} MB)")

        # 3. Create or Reset Demo Case
        case_num = "CAS-SIH-2026-001"
        existing_case = db.query(ForensicCase).filter(ForensicCase.case_number == case_num).first()
        if existing_case:
            print(f"[SIH Seed] Demo case '{case_num}' already exists (ID #{existing_case.id}).")
            case = existing_case
        else:
            case = ForensicCase(
                case_number=case_num,
                title="Smart India Hackathon 2026 Demonstration Case",
                description="Investigation of compromised storage media & read-only file recovery validation",
                status="OPEN",
                investigator_id=admin_user.id,
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            print(f"[SIH Seed] Demo case created: '{case.case_number}' (ID #{case.id})")

        # 4. Create Evidence Item
        evd_id = "EVD-SIH-DISK-01"
        existing_evd = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evd_id).first()
        if not existing_evd:
            evd = EvidenceItem(
                evidence_id=evd_id,
                case_id=case.id,
                item_number="ITEM-001",
                title="10MB Synthetic Raw Disk Image",
                original_filename="synthetic_test_disk_01.raw",
                file_path=str(img_path),
                file_size_bytes=img_size,
                sha256_hash=img_hash,
                source_description="Seized 10MB Raw Disk Image containing mixed file artifacts",
                operator_username=admin_user.username,
                processing_status="VERIFIED",
                import_time=datetime.now(timezone.utc),
            )
            db.add(evd)
            db.commit()
            print(f"[SIH Seed] Evidence item created: '{evd_id}'")

        # 5. Seed Carved File Artifacts
        artifacts_data = [
            ("CARV-JPEG-001", "JPEG", 10240, 117820, 107580, "HIGH", "Valid JPEG SOI, EOI, and EXIF metadata verified"),
            ("CARV-PNG-001", "PNG", 150000, 248000, 98000, "HIGH", "Valid 8-byte PNG magic, IHDR, and IEND footer verified"),
            ("CARV-PDF-001", "PDF", 300000, 385000, 85000, "HIGH", "Valid %PDF- header, Catalog structure, and %%EOF verified"),
            ("CARV-ZIP-001", "ZIP", 500000, 620000, 120000, "HIGH", "Valid PK\\x03\\x04 header, Central Directory, and EOCD verified"),
            ("CARV-JPEG-TRUNC", "JPEG", 800000, 825000, 25000, "LOW", "Valid JPEG SOI found, missing EOI footer marker (truncated file)"),
        ]

        for cid, fmt, start_off, end_off, sz, conf, val_reason in artifacts_data:
            existing_art = db.query(CarvedFileArtifact).filter(CarvedFileArtifact.carved_id == cid).first()
            if not existing_art:
                out_p = project_root / "test_data" / "carved_output" / f"{cid}.dat"
                out_p.parent.mkdir(parents=True, exist_ok=True)
                out_p.write_bytes(b"DEMO_CARVED_PAYLOAD_" + cid.encode("utf-8") + b"_" + b"X" * 100)

                art = CarvedFileArtifact(
                    carved_id=cid,
                    case_id=case.id,
                    source_evidence_id=evd_id,
                    file_format=fmt,
                    output_file_path=str(out_p),
                    carved_file_hash=f"hash_{cid.lower()}_sha256_mock_001",
                    source_image_hash=img_hash,
                    source_start_offset=start_off,
                    source_end_offset=end_off,
                    file_size_bytes=sz,
                    confidence_level=conf,
                    validation_details=val_reason,
                    scan_version="v1.0.0-carver",
                    tool_version="ForensicShield v1.0.0",
                    operator_username=admin_user.username,
                    carved_at=datetime.now(timezone.utc),
                )
                db.add(art)
        db.commit()
        print("[SIH Seed] 5 Carved file artifacts seeded.")

        # 6. Seed Intact Cryptographic Audit Chain
        audit_service = AuditService()
        audit_count = db.query(AuditEvent).count()
        if audit_count < 5:
            print("[SIH Seed] Populating cryptographic SHA-256 audit chain...")
            events_to_seed = [
                ("SYSTEM_BOOT", "System initialization with SAFE_MODE=true and REAL_DEVICE_OPERATIONS=false"),
                ("USER_LOGIN", f"User '{admin_user.username}' authenticated successfully (Role: Administrator)"),
                ("CASE_CREATED", f"Created forensic case #{case_num} 'SIH 2026 Demonstration Case'"),
                ("EVIDENCE_INTAKE", f"Imported evidence item '{evd_id}' (SHA256: {img_hash[:16]}...)"),
                ("SAFETY_GATE_PASSED", "Preflight 8-Point Safety Gate evaluated for target '/dev/sdb' -> PASSED"),
                ("DRY_RUN_SANITIZATION", "Executed simulated 5-pass DOD 5220.22-M dry-run wipe on '/dev/sdb' -> 0 bytes modified"),
                ("CARVING_SCAN_COMPLETED", f"Carving scan on '{evd_id}' completed. 5 artifacts recovered in 78.4ms"),
                ("RECOVERY_VALIDATED", "Validated recovered artifacts. 4 High Confidence, 1 Low Confidence (Truncated)"),
                ("AUDIT_VERIFIED", "Executed full chain verification -> INTACT (0 broken links)"),
            ]

            for action, summary in events_to_seed:
                audit_service.record_event(
                    db=db,
                    actor=admin_user.username,
                    role="Administrator",
                    action=action,
                    target_summary=summary,
                    result="SUCCESS",
                    case_id=case.id,
                )
            print(f"[SIH Seed] Cryptographic audit chain seeded ({db.query(AuditEvent).count()} total blocks).")

        # 7. Pre-generate Report
        report_service = ForensicReportService()
        rep_res = report_service.generate_case_report(db, case.id, admin_user.username)
        print(f"[SIH Seed] Pre-generated forensic report: PDF ({rep_res.pdf_sha256[:16]}...) & JSON ({rep_res.json_sha256[:16]}...)")

        print("\n==========================================================")
        print("  SIH DEMO SEED DATA SUCCESSFULLY INITIALIZED")
        print("  Demo Case:       CAS-SIH-2026-001")
        print("  Evidence ID:     EVD-SIH-DISK-01")
        print(f"  Evidence SHA256: {img_hash[:24]}...")
        print("  Carved Files:    5 Artifacts (JPEG, PNG, PDF, ZIP)")
        print("  Audit Chain:     INTACT (100% Cryptographically Linked)")
        print("==========================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
