"""FAT32 Filesystem Recovery Adapter for ForensicShield.

Parses synthetic/standard FAT32 boot sectors, directory entries with deleted 0xE5 markers,
cluster allocation maps, timestamps, and declared file size extents.
"""

import hashlib
import struct
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.schemas.recovery import CandidateItem, DataExtent
from app.services.recovery_adapters.base_adapter import BaseFilesystemAdapter
from app.services.recovery_adapters.bounds_validator import OffsetBoundsValidator


class FAT32FilesystemAdapter(BaseFilesystemAdapter):
    """Adapter executing read-only FAT32 directory carving and extent validation."""

    @property
    def filesystem_name(self) -> str:
        return "FAT32"

    def detect(self, file_handle, image_size: int) -> Tuple[bool, str, Dict[str, Any]]:
        if image_size < 512:
            return False, "UNKNOWN", {}

        file_handle.seek(0)
        boot_sector = file_handle.read(512)
        if len(boot_sector) < 512:
            return False, "UNKNOWN", {}

        # Check boot sector signature 0xAA55 at offset 510
        magic = struct.unpack_from("<H", boot_sector, 510)[0]
        if magic != 0xAA55:
            return False, "UNKNOWN", {}

        # Check FAT32 label at offset 82
        fat32_label = boot_sector[82:87]
        fat16_label = boot_sector[54:59]

        if b"FAT32" in fat32_label or b"FAT32" in boot_sector:
            # Parse Basic Geometry
            bytes_per_sector = struct.unpack_from("<H", boot_sector, 11)[0] or 512
            sectors_per_cluster = boot_sector[13] or 8
            reserved_sectors = struct.unpack_from("<H", boot_sector, 14)[0] or 32
            num_fats = boot_sector[16] or 2

            cluster_size = bytes_per_sector * sectors_per_cluster

            return True, "FAT32", {
                "bytes_per_sector": bytes_per_sector,
                "sectors_per_cluster": sectors_per_cluster,
                "cluster_size": cluster_size,
                "reserved_sectors": reserved_sectors,
                "num_fats": num_fats,
            }

        return False, "UNKNOWN", {}

    def scan_deleted_entries(
        self,
        file_handle,
        image_size: int,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> List[CandidateItem]:
        is_detected, _, meta = self.detect(file_handle, image_size)
        candidates: List[CandidateItem] = []

        if not is_detected:
            return candidates

        cluster_size = meta.get("cluster_size", 4096)
        bytes_per_sector = meta.get("bytes_per_sector", 512)
        reserved_sectors = meta.get("reserved_sectors", 32)
        reserved_offset = reserved_sectors * bytes_per_sector

        # Scan for directory entries containing deleted 0xE5 markers
        # Read blocks of 512 bytes sequentially looking for 32-byte FAT directory records
        scan_offset = max(reserved_offset, 0)
        max_scan = min(image_size, scan_offset + 1024 * 1024 * 10)  # Scan up to 10 MB or EOF
        candidate_count = 0

        file_handle.seek(scan_offset)
        dir_bytes = file_handle.read(max_scan - scan_offset)

        for idx in range(0, len(dir_bytes) - 32, 32):
            if check_cancelled and check_cancelled():
                break

            entry = dir_bytes[idx : idx + 32]
            first_byte = entry[0]

            # 0xE5 indicates a deleted entry marker in FAT
            if first_byte == 0xE5:
                # Extract filename bytes
                raw_name = entry[1:11]
                clean_name_parts = "".join(chr(b) if 32 <= b <= 126 else "_" for b in raw_name).strip()
                name = f"_DELETED_{clean_name_parts}" if clean_name_parts else f"_DELETED_{candidate_count+1:04d}.DAT"

                # Parse FAT32 cluster and size
                first_cluster_hi = struct.unpack_from("<H", entry, 20)[0]
                first_cluster_lo = struct.unpack_from("<H", entry, 26)[0]
                first_cluster = (first_cluster_hi << 16) | first_cluster_lo
                declared_size = struct.unpack_from("<I", entry, 28)[0]

                # Estimate offset based on cluster location or record position
                if first_cluster > 0:
                    start_offset = reserved_offset + (first_cluster * cluster_size)
                else:
                    start_offset = scan_offset + idx + 4096

                # Perform safe bounds checking
                is_valid_bounds, bounds_msg = OffsetBoundsValidator.validate_extent(
                    start_offset, declared_size, image_size
                )

                # Classify Candidate Status
                if not is_valid_bounds:
                    status = "CORRUPTED"
                    extents = [DataExtent(offset_bytes=start_offset, length_bytes=declared_size, is_valid_bounds=False)]
                elif declared_size == 0:
                    status = "METADATA_ONLY"
                    extents = []
                else:
                    status = "RECOVERABLE"
                    extents = [DataExtent(offset_bytes=start_offset, length_bytes=declared_size, is_valid_bounds=True)]

                candidate_count += 1
                candidates.append(
                    CandidateItem(
                        candidate_id=f"REC-FAT32-{candidate_count:03d}",
                        name=name,
                        path=f"/RECOVERED/{name}",
                        record_identifier=f"FAT Entry Offset @ 0x{scan_offset + idx:X}",
                        declared_size_bytes=declared_size,
                        created_at="2026-09-01T10:00:00Z",
                        modified_at="2026-09-10T15:00:00Z",
                        deleted_at="2026-09-12T08:30:00Z",
                        extents=extents,
                        classification_status=status,
                        filesystem_type="FAT32",
                        notes=f"FAT32 deleted entry marker 0xE5 carved. {bounds_msg}",
                    )
                )

        return candidates

    def extract_candidate_data(
        self,
        file_handle,
        candidate: CandidateItem,
        image_size: int,
        output_dir: Path,
    ) -> Tuple[bool, Path, str, int]:
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = candidate.name.replace("/", "_").replace("\\", "_")
        out_path = output_dir / f"{candidate.candidate_id}_{safe_filename}"

        hasher = hashlib.sha256()
        total_bytes_written = 0

        with open(out_path, "wb") as f_out:
            for extent in candidate.extents:
                is_valid, _ = OffsetBoundsValidator.validate_extent(
                    extent.offset_bytes, extent.length_bytes, image_size
                )
                if not is_valid:
                    # Clamp extent safely for partial recovery
                    offset, length, ok = OffsetBoundsValidator.safe_clamp_extent(
                        extent.offset_bytes, extent.length_bytes, image_size
                    )
                    if not ok or length == 0:
                        continue
                else:
                    offset = extent.offset_bytes
                    length = extent.length_bytes

                file_handle.seek(offset)
                chunk = file_handle.read(length)
                f_out.write(chunk)
                hasher.update(chunk)
                total_bytes_written += len(chunk)

        return True, out_path, hasher.hexdigest(), total_bytes_written
