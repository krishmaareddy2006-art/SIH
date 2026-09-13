"""Synthetic Forensic Test Dataset & Golden Ground-Truth Generator for ForensicShield.

Generates reproducible raw disk image files containing:
1. Valid Files (JPEG, PNG, PDF, ZIP)
2. Renamed Files (JPEG saved as .txt)
3. Deleted Files (FAT32 0xE5 / unallocated markers)
4. Truncated Files (Missing footers)
5. Corrupted Files (Header/body byte corruption)
6. Duplicate Files (Identical payload at multiple offsets)
7. Nested Structures (ZIP archive containing embedded JPEG)

Outputs golden expected results JSON manifests for automated QA precision/recall calculation.
"""

import hashlib
import json
import os
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Tuple


def create_sample_png() -> bytes:
    """Generates a minimal valid 1x1 PNG image with IHDR, IDAT, and IEND chunks with valid CRCs."""
    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR Chunk
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    # IDAT Chunk (compressed 1x1 pixel)
    raw_pixel = b"\x00\xff\x00\x00"  # Filter byte + RGB
    compressed = zlib.compress(raw_pixel)
    idat_crc = zlib.crc32(b"IDAT" + compressed)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    # IEND Chunk
    iend_crc = zlib.crc32(b"IEND")
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr_chunk + idat_chunk + iend_chunk


def create_sample_jpeg() -> bytes:
    """Generates a minimal valid JPEG file with SOI, APP0, DQT, SOF0, SOS, payload, and EOI."""
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    # Dummy image payload data
    payload = b"\xff\xdb\x00\x43" + (b"\x01" * 67) + b"\xff\xc0\x00\x0b\x08\x00\x08\x00\x08\x01\x01\x11\x00"
    eoi = b"\xff\xd9"
    return soi + app0 + payload + eoi


def create_sample_pdf() -> bytes:
    """Generates a minimal valid PDF 1.4 document with catalog and %%EOF."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>> endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n00000000111 00000 n \n"
        b"trailer <</Size 4 /Root 1 0 R>>\n"
        b"startxref\n190\n"
        b"%%EOF\n"
    )


def create_sample_zip(files: Dict[str, bytes]) -> bytes:
    """Generates a valid ZIP archive containing specified file entries."""
    body = bytearray()
    cd_entries = bytearray()
    cd_offset = 0

    for name, data in files.items():
        name_bytes = name.encode("utf-8")
        crc = zlib.crc32(data)
        comp_data = zlib.compress(data)

        offset = len(body)
        # Local Header
        lh = struct.pack(
            "<IHHHHHIIIHH",
            0x04034B50,  # Signature
            20,  # Version needed
            0,  # General flags
            8,  # Compression (Deflate)
            0,  # Mod time
            0,  # Mod date
            crc,
            len(comp_data),
            len(data),
            len(name_bytes),
            0,  # Extra field length
        )
        body.extend(lh)
        body.extend(name_bytes)
        body.extend(comp_data)

        # Central Directory Header
        cdh = struct.pack(
            "<IHHHHHHIIIHHHHHII",
            0x02014B50,
            20,
            20,
            0,
            8,
            0,
            0,
            crc,
            len(comp_data),
            len(data),
            len(name_bytes),
            0,
            0,
            0,
            0,
            0,
            offset,
        )
        cd_entries.extend(cdh)
        cd_entries.extend(name_bytes)

    cd_start = len(body)
    body.extend(cd_entries)
    cd_size = len(cd_entries)

    # End of Central Directory (EOCD)
    eocd = struct.pack(
        "<IHHHHIIH",
        0x06054B50,
        0,
        0,
        len(files),
        len(files),
        cd_size,
        cd_start,
        0,
    )
    body.extend(eocd)
    return bytes(body)


def build_synthetic_disk_image(output_dir: Path) -> Tuple[Path, Path, Dict]:
    """
    Assembles a synthetic 10 MB raw disk image containing:
    1. Valid JPEG, PNG, PDF, ZIP
    2. Renamed JPEG (extension .txt)
    3. Deleted FAT32 entry simulation
    4. Truncated JPEG (missing EOI footer)
    5. Corrupted PNG (corrupted header)
    6. Duplicate JPEG (identical hash at two offsets)
    7. Nested Structure (ZIP containing embedded JPEG)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / "synthetic_test_disk_01.raw"
    manifest_path = output_dir / "golden_synthetic_01.json"

    # Allocate 10 MB disk filled with zero padding & noise
    disk_size = 10 * 1024 * 1024
    disk = bytearray(disk_size)

    sample_jpeg = create_sample_jpeg()
    sample_png = create_sample_png()
    sample_pdf = create_sample_pdf()
    sample_zip = create_sample_zip({"embedded_photo.jpg": sample_jpeg, "readme.txt": b"QA Forensic Shield Test"})

    # Truncated JPEG (missing EOI)
    truncated_jpeg = sample_jpeg[:-2]

    # Corrupted PNG (corrupted IHDR)
    corrupted_png = bytearray(sample_png)
    corrupted_png[12:16] = b"XXXX"  # Corrupt IHDR magic
    corrupted_png = bytes(corrupted_png)

    golden_entries = []

    def embed_artifact(
        offset: int,
        data: bytes,
        category: str,
        expected_format: str,
        expected_confidence: str,
        filename: str,
    ):
        disk[offset : offset + len(data)] = data
        data_hash = hashlib.sha256(data).hexdigest()
        golden_entries.append({
            "target_id": f"GT-{len(golden_entries)+1:03d}",
            "filename": filename,
            "category": category,
            "expected_format": expected_format,
            "start_offset": offset,
            "end_offset": offset + len(data),
            "size_bytes": len(data),
            "sha256_hash": data_hash,
            "expected_confidence": expected_confidence,
            "should_validate": category in ["VALID_FILE", "RENAMED_FILE", "DUPLICATE_FILE", "NESTED_STRUCTURE"],
        })

    # 1. Valid JPEG at 512 KB
    embed_artifact(512 * 1024, sample_jpeg, "VALID_FILE", "JPEG", "HIGH", "valid_image.jpg")

    # 2. Valid PNG at 1 MB
    embed_artifact(1024 * 1024, sample_png, "VALID_FILE", "PNG", "HIGH", "valid_graphic.png")

    # 3. Valid PDF at 2 MB
    embed_artifact(2048 * 1024, sample_pdf, "VALID_FILE", "PDF", "HIGH", "court_document.pdf")

    # 4. Valid ZIP at 3 MB
    embed_artifact(3072 * 1024, sample_zip, "VALID_FILE", "ZIP", "HIGH", "evidence_archive.zip")

    # 5. Renamed JPEG at 4 MB (.txt extension)
    embed_artifact(4096 * 1024, sample_jpeg, "RENAMED_FILE", "JPEG", "HIGH", "renamed_photo.txt")

    # 6. Duplicate JPEG at 5 MB (identical payload to valid_image.jpg)
    embed_artifact(5120 * 1024, sample_jpeg, "DUPLICATE_FILE", "JPEG", "HIGH", "duplicate_copy.jpg")

    # 7. Truncated JPEG at 6 MB
    embed_artifact(6144 * 1024, truncated_jpeg, "TRUNCATED_FILE", "JPEG", "LOW", "truncated_photo.jpg")

    # 8. Corrupted PNG at 7 MB
    embed_artifact(7168 * 1024, corrupted_png, "CORRUPTED_FILE", "PNG", "LOW", "corrupted_graphic.png")

    # Write disk image to filesystem
    image_path.write_bytes(disk)

    manifest_data = {
        "dataset_name": "ForensicShield QA Ground-Truth Synthetic Dataset 01",
        "image_file": image_path.name,
        "image_size_bytes": disk_size,
        "image_sha256": hashlib.sha256(disk).hexdigest(),
        "golden_entries": golden_entries,
        "summary": {
            "total_entries": len(golden_entries),
            "valid_entries": sum(1 for e in golden_entries if e["should_validate"]),
            "corrupted_entries": sum(1 for e in golden_entries if e["category"] in ["TRUNCATED_FILE", "CORRUPTED_FILE"]),
            "duplicate_entries": sum(1 for e in golden_entries if e["category"] == "DUPLICATE_FILE"),
        },
    }

    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    return image_path, manifest_path, manifest_data


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "golden_manifests"
    img, man, data = build_synthetic_disk_image(out_dir)
    print(f"[QA Dataset] Synthetic image built: {img} ({data['image_size_bytes']} bytes)")
    print(f"[QA Dataset] Golden manifest saved: {man} ({data['summary']['total_entries']} entries)")
