"""Unsupported Filesystem Fallback Adapter for ForensicShield.

Enforces digital forensics policy: Never guess or fabricate data when encountering
unrecognized, corrupted, or unsupported filesystems. Returns a clear manual-review recommendation.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.schemas.recovery import CandidateItem
from app.services.recovery_adapters.base_adapter import BaseFilesystemAdapter


class UnsupportedFilesystemAdapter(BaseFilesystemAdapter):
    """Fallback adapter handling unsupported or unrecognized volume structures."""

    @property
    def filesystem_name(self) -> str:
        return "UNSUPPORTED"

    def detect(self, file_handle, image_size: int) -> Tuple[bool, str, Dict[str, Any]]:
        return False, "UNSUPPORTED", {
            "manual_review_required": True,
            "reason": "Unrecognized or corrupted volume header magic signature",
        }

    def scan_deleted_entries(
        self,
        file_handle,
        image_size: int,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> List[CandidateItem]:
        return [
            CandidateItem(
                candidate_id="REC-UNSUP-001",
                name="UNSUPPORTED_VOLUME_ANALYSIS_REQUIRED",
                path="/UNSUPPORTED_FILESYSTEM",
                record_identifier="UNKNOWN_VOLUME_HEADER",
                declared_size_bytes=0,
                created_at=None,
                modified_at=None,
                deleted_at=None,
                extents=[],
                classification_status="UNSUPPORTED",
                filesystem_type="UNSUPPORTED",
                notes=(
                    "UNSUPPORTED_FILESYSTEM_MANUAL_REVIEW_REQUIRED: Target disk image does not match any supported "
                    "filesystem signatures (FAT32, NTFS, EXT4) or contains severely corrupted volume headers. "
                    "ForensicShield policy prohibits guessing or returning false positive candidates. Manual analyst "
                    "review required in accordance with ISO/IEC 27037:2012."
                ),
            )
        ]

    def extract_candidate_data(
        self,
        file_handle,
        candidate: CandidateItem,
        image_size: int,
        output_dir: Path,
    ) -> Tuple[bool, Path, str, int]:
        output_dir.mkdir(parents=True, exist_ok=True)
        dummy_file = output_dir / "UNSUPPORTED_MANUAL_REVIEW_NOTE.txt"
        note_content = (
            "MANUAL ANALYST REVIEW REQUIRED\n"
            "------------------------------\n"
            "Target evidence image could not be automatically parsed by available filesystem adapters.\n"
            "Please submit evidence image to senior forensic laboratory analyst for manual Hex/carving inspection."
        )
        dummy_file.write_text(note_content, encoding="utf-8")
        return False, dummy_file, "0000000000000000000000000000000000000000000000000000000000000000", 0
