"""Offset Bounds Validator for Forensic Filesystem Analysis.

Never trusts raw filesystem metadata blindly. Validates that every byte offset and
data extent falls strictly within physical disk image boundaries (0 <= offset + length <= image_size).
"""

from typing import Tuple


class OffsetBoundsValidator:
    """Enforces strict bounds verification on all source image file offsets and lengths."""

    @staticmethod
    def validate_extent(offset: int, length: int, image_size: int) -> Tuple[bool, str]:
        """
        Validates that offset and length are non-negative and do not exceed image boundaries.
        Returns (is_valid, error_reason).
        """
        if offset < 0:
            return False, f"Negative offset value detected: {offset}"

        if length < 0:
            return False, f"Negative extent length value detected: {length}"

        if offset >= image_size:
            return False, f"Offset {offset} is beyond disk image size {image_size}"

        if offset + length > image_size:
            return (
                False,
                f"Extent range [{offset}, {offset + length}] exceeds disk image size {image_size}",
            )

        return True, "Valid extent bounds"

    @staticmethod
    def safe_clamp_extent(offset: int, length: int, image_size: int) -> Tuple[int, int, bool]:
        """
        Clamps offset and length safely within image boundaries for partial recovery calculations.
        Returns (safe_offset, safe_length, is_partially_valid).
        """
        if offset < 0 or offset >= image_size or length < 0:
            return 0, 0, False

        safe_offset = offset
        if safe_offset + length > image_size:
            safe_length = max(0, image_size - safe_offset)
            return safe_offset, safe_length, True

        return safe_offset, length, True
