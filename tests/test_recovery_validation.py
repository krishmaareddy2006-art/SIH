"""Unit Tests for Forensic Recovery Validation & Confidence-Scoring Engine.

Tests:
1. Valid PNG and ZIP payloads (HIGH_CONFIDENCE, CRC verification success)
2. Truncated payloads missing footer markers (LOW/MEDIUM confidence, manual review flag)
3. Corrupted CRC payloads (CRC failure warning, score penalty)
4. Renamed extensions (mismatched extension warning)
5. Maliciously crafted payloads (PDF JS/OpenAction triggers, static safety guarantees)
6. Deterministic scoring output & versioning
7. Recovery validation REST API endpoint
"""

import os
import struct
import tempfile
import zlib
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

import app.models  # Register ORM models
from app.core.database import Base, engine
from app.core.init_db import init_db
from app.schemas.validation import ValidationRequest
from app.services.recovery_validation import RecoveryValidationService, VALIDATION_ENGINE_VERSION
from conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_db(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def create_valid_png_bytes() -> bytes:
    """Helper creating valid PNG binary data with correct chunk CRC32 checksums."""
    magic = b"\x89PNG\r\n\x1a\n"
    ihdr_payload = b"\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00"
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_payload) & 0xFFFFFFFF
    ihdr_chunk = b"\x00\x00\x00\x0D" + b"IHDR" + ihdr_payload + struct.pack(">I", ihdr_crc)

    idat_payload = b"VALID_PNG_RAW_DATA_STREAM"
    idat_crc = zlib.crc32(b"IDAT" + idat_payload) & 0xFFFFFFFF
    idat_chunk = struct.pack(">I", len(idat_payload)) + b"IDAT" + idat_payload + struct.pack(">I", idat_crc)

    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend_chunk = b"\x00\x00\x00\x00" + b"IEND" + struct.pack(">I", iend_crc)

    return magic + ihdr_chunk + idat_chunk + iend_chunk


def create_valid_zip_bytes() -> bytes:
    """Helper creating valid ZIP binary data with correct local header and CRC32 payload."""
    payload = b"Sample uncompressed payload string for ZIP test"
    payload_crc = zlib.crc32(payload) & 0xFFFFFFFF
    comp_size = len(payload)
    uncomp_size = len(payload)
    fn = b"test.txt"

    local_hdr = (
        b"PK\x03\x04"
        + struct.pack("<H", 20)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<I", payload_crc)
        + struct.pack("<I", comp_size)
        + struct.pack("<I", uncomp_size)
        + struct.pack("<H", len(fn))
        + struct.pack("<H", 0)
        + fn
        + payload
    )

    cd_hdr = (
        b"PK\x01\x02"
        + struct.pack("<H", 20)
        + struct.pack("<H", 20)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<I", payload_crc)
        + struct.pack("<I", comp_size)
        + struct.pack("<I", uncomp_size)
        + struct.pack("<H", len(fn))
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<I", 0)
        + struct.pack("<I", 0)
        + fn
    )

    eocd = (
        b"PK\x05\x06"
        + struct.pack("<H", 0)
        + struct.pack("<H", 0)
        + struct.pack("<H", 1)
        + struct.pack("<H", 1)
        + struct.pack("<I", len(cd_hdr))
        + struct.pack("<I", len(local_hdr))
        + struct.pack("<H", 0)
    )

    return local_hdr + cd_hdr + eocd


def test_valid_png_and_zip_high_confidence():
    """Verifies that valid PNG and ZIP payloads achieve HIGH_CONFIDENCE labels and CRC pass."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        png_file = Path(tmpdir) / "sample.png"
        png_file.write_bytes(create_valid_png_bytes())

        req_png = ValidationRequest(
            file_path=str(png_file),
            source_evidence_hash="a"*64,
            source_offset=1024,
        )
        report_png = val_service.validate_file(req_png)

        assert report_png.detected_format == "PNG"
        assert report_png.overall_score >= 85
        assert report_png.confidence_label == "HIGH_CONFIDENCE"
        assert report_png.factors.valid_header.passed is True
        assert report_png.factors.valid_footer.passed is True
        assert report_png.factors.checksum_crc_success.passed is True
        assert report_png.requires_manual_review is False

        zip_file = Path(tmpdir) / "sample.zip"
        zip_file.write_bytes(create_valid_zip_bytes())

        req_zip = ValidationRequest(
            file_path=str(zip_file),
            source_evidence_hash="b"*64,
            source_offset=4096,
        )
        report_zip = val_service.validate_file(req_zip)

        assert report_zip.detected_format == "ZIP"
        assert report_zip.overall_score >= 85
        assert report_zip.confidence_label == "HIGH_CONFIDENCE"
        assert report_zip.factors.checksum_crc_success.passed is True


def test_truncated_file_medium_low_confidence():
    """Verifies that truncated files missing footer markers receive lower scores and manual review flag."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        trunc_file = Path(tmpdir) / "truncated.png"
        png_data = create_valid_png_bytes()
        # Cut off IEND footer chunk
        trunc_file.write_bytes(png_data[: len(png_data) - 20])

        req = ValidationRequest(file_path=str(trunc_file))
        report = val_service.validate_file(req)

        assert report.factors.valid_footer.passed is False
        assert report.overall_score < 75
        assert report.requires_manual_review is True
        assert any("truncated" in w.lower() or "missing" in w.lower() for w in report.warnings)


def test_corrupted_crc_validation_failure():
    """Verifies that payload CRC mismatches trigger validation warnings and score deduction."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        corrupt_zip = Path(tmpdir) / "corrupt_crc.zip"
        zip_bytes = bytearray(create_valid_zip_bytes())
        # Alter one byte inside compressed payload region without updating CRC header
        zip_bytes[40] ^= 0xFF
        corrupt_zip.write_bytes(bytes(zip_bytes))

        req = ValidationRequest(file_path=str(corrupt_zip))
        report = val_service.validate_file(req)

        assert report.factors.checksum_crc_success.passed is False
        assert any("crc32 mismatch" in w.lower() for w in report.warnings)
        assert report.requires_manual_review is True


def test_renamed_file_extension_mismatch():
    """Verifies that files with mismatched extensions (e.g. JPEG saved as .png) trigger extension warning."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        renamed_file = Path(tmpdir) / "fake_image.png"
        # Write valid JPEG payload into .png extension file
        jpeg_payload = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00" + (b"X" * 100) + b"\xFF\xD9"
        renamed_file.write_bytes(jpeg_payload)

        req = ValidationRequest(file_path=str(renamed_file))
        report = val_service.validate_file(req)

        assert report.detected_format == "JPEG"
        assert report.declared_extension == ".png"
        assert report.is_extension_matched is False
        assert report.requires_manual_review is True
        assert any("extension mismatch" in w.lower() for w in report.warnings)


def test_maliciously_crafted_file_security_flags():
    """Verifies that active PDF scripts (/JavaScript, /OpenAction) are flagged safely without execution."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_file = Path(tmpdir) / "malicious_active.pdf"
        pdf_payload = (
            b"%PDF-1.7\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R /OpenAction << /S /JavaScript /JS (app.alert('XSS')) >> >> endobj\n"
            b"2 0 obj << /Type /Pages /Count 1 >> endobj\n"
            b"xref\n0 3\n0000000000 65535 f \ntrailer << /Root 1 0 R >>\nstartxref\n140\n%%EOF\n"
        )
        pdf_file.write_bytes(pdf_payload)

        req = ValidationRequest(file_path=str(pdf_file))
        report = val_service.validate_file(req)

        assert report.detected_format == "PDF"
        assert len(report.security_flags) >= 2
        assert any("javascript" in flag.lower() for flag in report.security_flags)
        assert any("openaction" in flag.lower() for flag in report.security_flags)
        assert report.requires_manual_review is True


def test_validation_determinism_and_versioning():
    """Verifies that validation outputs are 100% deterministic and versioned."""
    val_service = RecoveryValidationService()

    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = Path(tmpdir) / "det_sample.png"
        sample_file.write_bytes(create_valid_png_bytes())

        req = ValidationRequest(file_path=str(sample_file), source_evidence_hash="1"*64, source_offset=0)
        report1 = val_service.validate_file(req)
        report2 = val_service.validate_file(req)

        assert report1.validation_version == VALIDATION_ENGINE_VERSION
        assert report1.overall_score == report2.overall_score
        assert report1.confidence_label == report2.confidence_label
        assert report1.file_sha256 == report2.file_sha256
        assert report1.disclaimer == "Empirical heuristic quality index (0-100). This score is NOT a statistical probability of truth."


def test_validation_api_endpoint(client, admin_headers):
    """Tests POST /api/v1/validation/validate-file HTTP endpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = Path(tmpdir) / "api_test.zip"
        sample_file.write_bytes(create_valid_zip_bytes())

        res = client.post(
            "/api/v1/validation/validate-file",
            json={"file_path": str(sample_file), "expected_format": "ZIP"},
            headers=admin_headers,
        )

        assert res.status_code == 200
        data = res.json()
        assert data["detected_format"] == "ZIP"
        assert data["overall_score"] >= 85
        assert data["confidence_label"] == "HIGH_CONFIDENCE"
        assert "disclaimer" in data
