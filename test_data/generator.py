"""ForensicShield Evidence Test Data Generator

Generates realistic, synthetic file structures containing:
- Deeply nested folder hierarchies
- Standard dummy files (logs, text, mock binaries)
- Identical duplicate files (matching SHA-256 hashes across locations)
- Intentionally corrupted files (invalid magic bytes, truncated headers)
- JSON manifest with expected file hashes and integrity metadata
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def calculate_sha256(filepath: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_forensic_test_data(target_dir: Path) -> dict:
    """Creates synthetic forensic test data tree and returns manifest data."""
    if target_dir.exists():
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    # 1. Nested folder structure setup
    dirs = [
        target_dir / "system_logs",
        target_dir / "user_profile" / "documents" / "confidential",
        target_dir / "user_profile" / "downloads" / "temp",
        target_dir / "evidence" / "nested" / "deep" / "level4",
        target_dir / "corrupted_artifacts",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Helper to create file and track in manifest
    def create_evidence_file(
        rel_path: str,
        content: bytes,
        is_corrupted: bool = False,
        is_duplicate: bool = False,
        corruption_details: str = "",
    ):
        full_path = target_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)

        file_hash = calculate_sha256(full_path)
        entry = {
            "path": rel_path,
            "size_bytes": len(content),
            "sha256": file_hash,
            "is_corrupted": is_corrupted,
            "is_duplicate": is_duplicate,
            "corruption_details": corruption_details if is_corrupted else None,
        }
        manifest_entries.append(entry)
        return entry

    # 2. Standard Dummy Files
    create_evidence_file(
        "system_logs/auth.log",
        b"2026-09-13T10:00:01Z [INFO] User admin logged in from 192.168.1.50\n"
        b"2026-09-13T10:05:22Z [WARN] Failed login attempt from 10.0.0.12\n",
    )

    create_evidence_file(
        "user_profile/documents/confidential/q4_report.txt",
        b"CONFIDENTIAL FORENSIC REPORT: Case #2026-8849\nTarget system audit complete.",
    )

    create_evidence_file(
        "evidence/nested/deep/level4/deep_artifact.dat",
        b"\x00\x01\x02\x03ForensicShield Deep Data Payload\x04\x05\x06",
    )

    # 3. Duplicate Files (Exact duplicate byte streams across different paths)
    duplicate_payload = b"CRITICAL_SYSTEM_STATE_DUMP_HASH_TEST_MATCHING_BYTES_12345"

    create_evidence_file(
        "user_profile/downloads/temp/sys_dump_orig.bin",
        duplicate_payload,
        is_duplicate=True,
    )
    create_evidence_file(
        "evidence/nested/deep/level4/sys_dump_copy.bin",
        duplicate_payload,
        is_duplicate=True,
    )
    create_evidence_file(
        "corrupted_artifacts/sys_dump_shadow.bin",
        duplicate_payload,
        is_duplicate=True,
    )

    # 4. Intentionally Corrupted Files
    # Corrupted PNG: Invalid magic bytes (Standard PNG: \x89PNG\r\n\x1a\n)
    corrupted_png = b"\x00\x00BAD_HEADER_NOT_PNG\r\n\x1a\n" + b"\xFF" * 100
    create_evidence_file(
        "corrupted_artifacts/evidence_photo_damaged.png",
        corrupted_png,
        is_corrupted=True,
        corruption_details="Invalid PNG magic header replaced with null bytes.",
    )

    # Corrupted ZIP archive (Truncated header)
    corrupted_zip = b"PK\x03\x04TRUNCATED_ARCHIVE_DATA_UNEXPECTED_EOF"
    create_evidence_file(
        "corrupted_artifacts/archived_logs_corrupt.zip",
        corrupted_zip,
        is_corrupted=True,
        corruption_details="Truncated ZIP archive header missing central directory structure.",
    )

    # Corrupted ELF Binary Header
    corrupted_elf = b"\x7FELF_MALFORMED_HEADER_BYTES"
    create_evidence_file(
        "corrupted_artifacts/suspicious_exec.elf",
        corrupted_elf,
        is_corrupted=True,
        corruption_details="Corrupted ELF binary magic bytes header.",
    )

    # 5. Save Manifest JSON
    manifest = {
        "generator_version": "1.0.0",
        "target_directory": str(target_dir),
        "total_files": len(manifest_entries),
        "total_corrupted_files": sum(1 for e in manifest_entries if e["is_corrupted"]),
        "total_duplicate_files": sum(1 for e in manifest_entries if e["is_duplicate"]),
        "files": manifest_entries,
    }

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "generated_evidence"
    if len(sys.argv) > 1:
        out_dir = Path(sys.argv[1])

    print(f"[+] Generating Forensic Test Data in: {out_dir.resolve()}")
    result = generate_forensic_test_data(out_dir)
    print(f"[+] Successfully generated {result['total_files']} files.")
    print(f"    - Corrupted files: {result['total_corrupted_files']}")
    print(f"    - Duplicate files: {result['total_duplicate_files']}")
    print(f"[+] Manifest created at: {out_dir / 'manifest.json'}")
