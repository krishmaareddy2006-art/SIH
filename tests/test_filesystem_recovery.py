"""Unit Tests for Read-Only Filesystem-Aware Recovery Service & Provenance Tracking.

Tests:
1. Synthetic FAT32 disk image scanning & 0xE5 deleted entry carving
2. Synthetic NTFS disk image scanning & MFT record carving
3. Corrupted metadata bounds rejection (offset + length > image_size)
4. Unsupported filesystem manual-review recommendation (never guess policy)
5. Pre/post scan SHA-256 evidence integrity verification (proof of untouched evidence)
6. Candidate classification into RECOVERABLE, PARTIALLY_RECOVERABLE, METADATA_ONLY, CORRUPTED, UNSUPPORTED
7. Recovered file export & provenance tracking DB persistence
8. Recovery REST API endpoints
"""

import os
import struct
import tempfile
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.exceptions import ForensicShieldException
from app.core.init_db import init_db
from app.models.auth import User
from app.models.case import ForensicCase, EvidenceItem, RecoveredArtifact
from app.schemas.evidence import EvidenceImportRequest
from app.schemas.recovery import RecoveryExtractRequest, RecoveryScanRequest
from app.services.evidence_intake import EvidenceIntakeService
from app.services.filesystem_recovery import FilesystemRecoveryService
from conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)

    admin_user = db.query(User).filter(User.username == "admin").first()

    test_case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()
    if not test_case:
        test_case = ForensicCase(
            case_number="CASE-REC-001",
            title="Filesystem Recovery Test Case",
            description="Case for recovery service tests",
            investigator_id=admin_user.id,
            status="OPEN",
        )
        db.add(test_case)
        db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_synthetic_fat32_image(path: Path) -> int:
    """Creates a synthetic FAT32 disk image with boot sector and 0xE5 deleted entry."""
    image_size = 65536 * 4  # 256 KB synthetic image
    data = bytearray(image_size)

    # 1. Boot sector signature 0xAA55 at offset 510
    struct.pack_into("<H", data, 510, 0xAA55)
    # FAT32 label at offset 82
    data[82:87] = b"FAT32"
    # Basic geometry
    struct.pack_into("<H", data, 11, 512)  # Bytes per sector
    data[13] = 8  # Sectors per cluster
    struct.pack_into("<H", data, 14, 32)  # Reserved sectors
    data[16] = 2  # Num FATs

    # 2. Place a deleted directory entry at offset 32768 (32 KB)
    entry_offset = 32768
    data[entry_offset] = 0xE5  # Deleted marker
    data[entry_offset + 1 : entry_offset + 11] = b"INVOICE TXT"  # Filename
    struct.pack_into("<H", data, entry_offset + 20, 0)  # High cluster
    struct.pack_into("<H", data, entry_offset + 26, 2)  # Low cluster
    struct.pack_into("<I", data, entry_offset + 28, 4096)  # Declared size = 4 KB

    # 3. Write payload data at cluster 2 offset (32 reserved * 512 + 2 * 4096 = 24576)
    cluster_offset = 32 * 512 + 2 * 4096
    payload = b"SYNTHETIC_FAT32_RECOVERED_INVOICE_DATA_" * 100
    data[cluster_offset : cluster_offset + len(payload)] = payload

    path.write_bytes(bytes(data))
    return image_size


def create_synthetic_ntfs_image(path: Path) -> int:
    """Creates a synthetic NTFS disk image with VBR and unallocated MFT record."""
    image_size = 65536 * 4
    data = bytearray(image_size)

    # NTFS VBR signature at offset 3
    data[3:7] = b"NTFS"
    struct.pack_into("<H", data, 11, 512)
    data[13] = 8

    # Unallocated MFT record at offset 4096
    mft_offset = 4096
    data[mft_offset : mft_offset + 4] = b"FILE"  # Signature
    struct.pack_into("<H", data, mft_offset + 22, 0x00)  # Flags: 0x00 = deleted/unallocated

    # Write payload data after MFT record
    data[mft_offset + 1024 : mft_offset + 1024 + 100] = b"NTFS_UNALLOCATED_MFT_PAYLOAD_TEST_" * 3

    path.write_bytes(bytes(data))
    return image_size


def test_fat32_synthetic_image_recovery(db: Session):
    """Verifies FAT32 detection, deleted 0xE5 entry carving, and RECOVERABLE status classification."""
    intake_service = EvidenceIntakeService()
    recovery_service = FilesystemRecoveryService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "fat32_test.raw"
        create_synthetic_fat32_image(img_path)

        import_req = EvidenceImportRequest(
            source_file_path=str(img_path),
            item_number="EVID-FAT32-01",
            title="Synthetic FAT32 Evidence Image",
            create_working_copy=True,
        )

        item = intake_service.import_evidence_image(
            db=db, case_id=case.id, request=import_req, operator_username="admin"
        )

        scan_res = recovery_service.scan_evidence_recovery(
            db=db, case_id=case.id, evidence_id=item.evidence_id, operator_username="admin"
        )

        assert scan_res.filesystem_detected == "FAT32"
        assert scan_res.is_evidence_untouched is True
        assert scan_res.pre_scan_sha256 == scan_res.post_scan_sha256
        assert scan_res.total_candidates_found >= 1

        cand = scan_res.candidates[0]
        assert cand.classification_status == "RECOVERABLE"
        assert cand.filesystem_type == "FAT32"
        assert cand.declared_size_bytes == 4096


def test_ntfs_synthetic_image_recovery(db: Session):
    """Verifies NTFS detection and MFT record carving."""
    intake_service = EvidenceIntakeService()
    recovery_service = FilesystemRecoveryService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "ntfs_test.raw"
        create_synthetic_ntfs_image(img_path)

        import_req = EvidenceImportRequest(
            source_file_path=str(img_path),
            item_number="EVID-NTFS-01",
            title="Synthetic NTFS Evidence Image",
            create_working_copy=False,
        )

        item = intake_service.import_evidence_image(
            db=db, case_id=case.id, request=import_req, operator_username="admin"
        )

        scan_res = recovery_service.scan_evidence_recovery(
            db=db, case_id=case.id, evidence_id=item.evidence_id, operator_username="admin"
        )

        assert scan_res.filesystem_detected == "NTFS"
        assert scan_res.total_candidates_found >= 1
        assert scan_res.candidates[0].classification_status == "RECOVERABLE"


def test_corrupted_metadata_bounds_rejection(db: Session):
    """Verifies that candidate records with offsets exceeding image boundaries are classified as CORRUPTED."""
    intake_service = EvidenceIntakeService()
    recovery_service = FilesystemRecoveryService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "corrupt_bounds_test.raw"
        image_size = 65536
        data = bytearray(image_size)

        # Boot sector
        struct.pack_into("<H", data, 510, 0xAA55)
        data[82:87] = b"FAT32"
        struct.pack_into("<H", data, 11, 512)
        data[13] = 8
        struct.pack_into("<H", data, 14, 32)
        data[16] = 2

        # Corrupted entry pointing way beyond image size (cluster 999999)
        entry_offset = 32768
        data[entry_offset] = 0xE5
        data[entry_offset + 1 : entry_offset + 11] = b"CORRUPT TXT"
        struct.pack_into("<H", data, entry_offset + 20, 0x0F)
        struct.pack_into("<H", data, entry_offset + 26, 0x4240)  # Cluster 1,000,000
        struct.pack_into("<I", data, entry_offset + 28, 5000000)  # Declared size 5 MB

        img_path.write_bytes(bytes(data))

        import_req = EvidenceImportRequest(
            source_file_path=str(img_path),
            item_number="EVID-CORRUPT-BOUNDS-01",
            title="Corrupted Bounds Image",
            create_working_copy=False,
        )

        item = intake_service.import_evidence_image(db=db, case_id=case.id, request=import_req, operator_username="admin")

        scan_res = recovery_service.scan_evidence_recovery(db=db, case_id=case.id, evidence_id=item.evidence_id, operator_username="admin")

        assert scan_res.total_candidates_found >= 1
        corrupt_cand = scan_res.candidates[0]
        assert corrupt_cand.classification_status == "CORRUPTED"
        assert corrupt_cand.extents[0].is_valid_bounds is False


def test_unsupported_filesystem_manual_review(db: Session):
    """Verifies that unknown/corrupted filesystems return a clear UNSUPPORTED manual review message."""
    intake_service = EvidenceIntakeService()
    recovery_service = FilesystemRecoveryService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "unsupported_junk.raw"
        # Write random noise with no valid filesystem header
        img_path.write_bytes(os.urandom(65536))

        import_req = EvidenceImportRequest(
            source_file_path=str(img_path),
            item_number="EVID-UNSUP-01",
            title="Unsupported Disk Format Image",
            create_working_copy=False,
        )

        item = intake_service.import_evidence_image(db=db, case_id=case.id, request=import_req, operator_username="admin")

        scan_res = recovery_service.scan_evidence_recovery(db=db, case_id=case.id, evidence_id=item.evidence_id, operator_username="admin")

        assert scan_res.filesystem_detected == "UNSUPPORTED"
        assert scan_res.manual_review_message is not None
        assert "UNSUPPORTED_FILESYSTEM_MANUAL_REVIEW_REQUIRED" in scan_res.manual_review_message
        assert len(scan_res.candidates) == 1
        assert scan_res.candidates[0].classification_status == "UNSUPPORTED"


def test_recovery_export_and_provenance_tracking(db: Session):
    """Verifies candidate extraction to output directory and RecoveredArtifact provenance persistence."""
    intake_service = EvidenceIntakeService()
    recovery_service = FilesystemRecoveryService()
    case = db.query(ForensicCase).filter(ForensicCase.case_number == "CASE-REC-001").first()

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "export_test.raw"
        create_synthetic_fat32_image(img_path)

        import_req = EvidenceImportRequest(
            source_file_path=str(img_path),
            item_number="EVID-EXPORT-01",
            title="Export Provenance Test Image",
            create_working_copy=True,
        )

        item = intake_service.import_evidence_image(db=db, case_id=case.id, request=import_req, operator_username="admin")

        # Scan to get candidate IDs
        scan_res = recovery_service.scan_evidence_recovery(db=db, case_id=case.id, evidence_id=item.evidence_id, operator_username="admin")
        cand_id = scan_res.candidates[0].candidate_id

        # Extract candidate
        out_dir = Path(tmpdir) / "extracted_output"
        extract_req = RecoveryExtractRequest(
            evidence_id=item.evidence_id,
            candidate_ids=[cand_id],
            custom_output_dir=str(out_dir),
        )

        job_res = recovery_service.extract_recovery_candidates(
            db=db, case_id=case.id, request=extract_req, operator_username="admin"
        )

        assert job_res.successfully_extracted == 1
        assert len(job_res.extracted_artifacts) == 1

        artifact = job_res.extracted_artifacts[0]
        assert artifact.candidate_id == cand_id
        assert Path(artifact.output_file_path).exists()
        assert artifact.recovered_file_hash is not None
        assert artifact.source_evidence_id == item.evidence_id

        # Verify database provenance record
        db_art = db.query(RecoveredArtifact).filter(RecoveredArtifact.artifact_id == artifact.artifact_id).first()
        assert db_art is not None
        assert db_art.case_id == case.id
        assert db_art.recovered_file_hash == artifact.recovered_file_hash


def test_recovery_api_endpoints(client, admin_headers):
    """Tests recovery HTTP endpoints: scan, extract, and list results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "api_recovery.raw"
        create_synthetic_fat32_image(img_path)

        # 1. Import evidence image via API
        res_import = client.post(
            "/api/v1/cases/1/evidence/import",
            json={
                "source_file_path": str(img_path),
                "item_number": "EVID-API-REC-1",
                "title": "API Recovery Image",
            },
            headers=admin_headers,
        )
        assert res_import.status_code == 201
        ev_id = res_import.json()["evidence_id"]

        # 2. Trigger Scan API
        res_scan = client.post(
            "/api/v1/cases/1/recovery/scan",
            json={"evidence_id": ev_id},
            headers=admin_headers,
        )
        assert res_scan.status_code == 200
        scan_data = res_scan.json()
        assert scan_data["filesystem_detected"] == "FAT32"
        assert scan_data["total_candidates_found"] >= 1
        cand_id = scan_data["candidates"][0]["candidate_id"]

        # 3. Trigger Extract API
        out_folder = Path(tmpdir) / "api_out"
        res_extract = client.post(
            "/api/v1/cases/1/recovery/extract",
            json={
                "evidence_id": ev_id,
                "candidate_ids": [cand_id],
                "custom_output_dir": str(out_folder),
            },
            headers=admin_headers,
        )
        assert res_extract.status_code == 200
        extract_data = res_extract.json()
        assert extract_data["successfully_extracted"] == 1

        # 4. List Results API
        res_list = client.get("/api/v1/cases/1/recovery/results", headers=admin_headers)
        assert res_list.status_code == 200
        artifacts_list = res_list.json()
        assert len(artifacts_list) >= 1
