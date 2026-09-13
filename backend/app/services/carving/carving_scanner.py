"""Bounded Overlapping Chunk Scanner for Signature-Based File Carving.

Scans disk images in bounded chunks with overlap so headers spanning chunk boundaries
are never missed. Enforces strict upper bounds on candidate read allocations.
"""

from typing import Callable, List, Optional, Set, Tuple

from app.schemas.carving import CarvingCandidateItem
from app.services.carving.format_validators import FormatValidatorFactory
from app.services.carving.signature_registry import (
    CarvingSignatureDefinition,
    CarvingSignatureRegistry,
)

DEFAULT_CHUNK_SIZE = 1_048_576  # 1 MB chunk size
DEFAULT_OVERLAP = 256  # 256 bytes overlap to capture boundary-spanning signatures


class CarvingScanner:
    """Chunked overlapping scanner locating header signatures and validating candidate bounds."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def scan_image(
        self,
        file_handle,
        image_size: int,
        target_formats: Optional[List[str]] = None,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> Tuple[List[CarvingCandidateItem], int, int, int]:
        """
        Scans file_handle in bounded overlapping chunks for target header signatures.
        Returns (validated_candidates, total_bytes_scanned, candidates_found_count, rejected_count).
        """
        all_sigs = CarvingSignatureRegistry.get_all_signatures()
        if target_formats:
            fmt_set = {f.upper() for f in target_formats}
            enabled_sigs = [s for s in all_sigs if s.file_type in fmt_set]
        else:
            enabled_sigs = all_sigs

        seen_offsets: Set[Tuple[str, int]] = set()
        raw_candidates: List[CarvingCandidateItem] = []
        candidates_found = 0
        rejected_count = 0
        total_bytes_scanned = 0

        current_offset = 0

        while current_offset < image_size:
            if check_cancelled and check_cancelled():
                break

            # Read chunk bytes
            read_size = min(self.chunk_size, image_size - current_offset)
            file_handle.seek(current_offset)
            chunk_bytes = file_handle.read(read_size)
            total_bytes_scanned += len(chunk_bytes)

            for sig_def in enabled_sigs:
                header_sig = sig_def.header_signature
                start_idx = 0

                while True:
                    match_idx = chunk_bytes.find(header_sig, start_idx)
                    if match_idx == -1:
                        break

                    abs_start = current_offset + match_idx
                    start_idx = match_idx + 1

                    # Prevent duplicate processing from chunk overlap
                    offset_key = (sig_def.file_type, abs_start)
                    if offset_key in seen_offsets:
                        continue
                    seen_offsets.add(offset_key)

                    candidates_found += 1

                    # Determine upper bound allocation limit safely
                    max_alloc = min(sig_def.max_size_bytes, image_size - abs_start)
                    if max_alloc < sig_def.min_size_bytes:
                        rejected_count += 1
                        continue

                    # Read candidate window safely without unbounded memory allocation
                    file_handle.seek(abs_start)
                    candidate_data = file_handle.read(max_alloc)

                    # Validate candidate format structure
                    validator = FormatValidatorFactory.get_validator(sig_def.file_type)
                    if not validator:
                        rejected_count += 1
                        continue

                    is_valid, confidence, reason, calc_length = validator.validate(candidate_data)
                    if not is_valid:
                        rejected_count += 1
                        continue

                    length_bytes = calc_length if (calc_length > 0 and calc_length <= len(candidate_data)) else len(candidate_data)
                    abs_end = abs_start + length_bytes

                    cand = CarvingCandidateItem(
                        candidate_id=f"CARV-{sig_def.file_type}-{len(raw_candidates)+1:04d}",
                        format=sig_def.file_type,
                        start_offset=abs_start,
                        end_offset=abs_end,
                        length_bytes=length_bytes,
                        header_signature_hex=sig_def.header_signature.hex().upper(),
                        footer_signature_hex=sig_def.footer_signature.hex().upper() if sig_def.footer_signature else None,
                        confidence_level=confidence,
                        validation_reason=reason,
                        is_valid=True,
                    )
                    raw_candidates.append(cand)

            # Advance chunk offset minus overlap
            if current_offset + read_size >= image_size:
                break
            current_offset += read_size - self.overlap

        # De-duplicate overlapping candidate windows (prefer HIGH confidence or longer windows)
        filtered_candidates = self._filter_overlapping_candidates(raw_candidates)

        return filtered_candidates, total_bytes_scanned, candidates_found, rejected_count

    def _filter_overlapping_candidates(self, candidates: List[CarvingCandidateItem]) -> List[CarvingCandidateItem]:
        """Resolves overlapping candidate ranges and nested signatures."""
        if not candidates:
            return []

        # Sort by start_offset asc, confidence rank desc (HIGH=3, MEDIUM=2, LOW=1)
        conf_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

        candidates.sort(key=lambda c: (c.start_offset, -conf_rank.get(c.confidence_level, 0)))

        filtered: List[CarvingCandidateItem] = []
        for cand in candidates:
            # Check for exact duplicate start_offset & format
            if filtered and filtered[-1].start_offset == cand.start_offset and filtered[-1].format == cand.format:
                # Keep higher confidence
                if conf_rank.get(cand.confidence_level, 0) > conf_rank.get(filtered[-1].confidence_level, 0):
                    filtered[-1] = cand
                continue

            filtered.append(cand)

        return filtered
