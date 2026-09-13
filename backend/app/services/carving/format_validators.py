"""Format-Aware Validators for Forensic File Carving.

Validates candidate file data using deep structural format checks for JPEG, PNG, PDF, and ZIP.
Produces confidence levels (HIGH, MEDIUM, LOW) with explicit forensic explanations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BaseFormatValidator(ABC):
    """Abstract base class for format-aware candidate data validators."""

    @abstractmethod
    def validate(self, data: bytes) -> Tuple[bool, str, str, int]:
        """
        Validates candidate bytes.
        Returns (is_valid, confidence_level, validation_reason, calculated_length).
        confidence_level: 'HIGH', 'MEDIUM', 'LOW'
        """
        pass


class JPEGValidator(BaseFormatValidator):
    """Format-aware validator for JPEG files (SOI: FF D8 FF, EOI: FF D9)."""

    def validate(self, data: bytes) -> Tuple[bool, str, str, int]:
        if len(data) < 100 or not data.startswith(b"\xFF\xD8\xFF"):
            return False, "LOW", "Missing valid JPEG Start of Image (SOI) header 0xFFD8FF", 0

        # Search for first End of Image (EOI) marker 0xFFD9
        eoi_idx = data.find(b"\xFF\xD9")
        has_app0_exif = (b"\xFF\xE0" in data[:512]) or (b"\xFF\xE1" in data[:512]) or (b"JFIF" in data[:512]) or (b"Exif" in data[:512])

        if eoi_idx != -1:
            end_offset = eoi_idx + 2
            if has_app0_exif:
                return True, "HIGH", "Valid JPEG SOI, EOI footer marker, and APP0/EXIF metadata headers verified", end_offset
            return True, "MEDIUM", "Valid JPEG SOI and EOI footer markers verified, missing standard APP metadata header", end_offset

        # Missing EOI footer - truncated file
        return True, "LOW", "Valid JPEG SOI header found, but EOI footer marker (0xFFD9) is missing (truncated file)", len(data)


class PNGValidator(BaseFormatValidator):
    """Format-aware validator for PNG files (Header: \x89PNG\r\n\x1a\n, Footer: IEND)."""

    def validate(self, data: bytes) -> Tuple[bool, str, str, int]:
        png_magic = b"\x89PNG\r\n\x1a\n"
        if len(data) < 68 or not data.startswith(png_magic):
            return False, "LOW", "Missing valid 8-byte PNG magic header '\\x89PNG\\r\\n\\x1a\\n'", 0

        has_ihdr = b"IHDR" in data[8:32]
        iend_idx = data.find(b"\x49\x45\x4e\x44\xae\x42\x60\x82")  # IEND + CRC
        if iend_idx == -1:
            iend_idx = data.find(b"IEND")

        if has_ihdr and iend_idx != -1:
            end_offset = iend_idx + (8 if b"\x49\x45\x4e\x44\xae\x42\x60\x82" in data[iend_idx:iend_idx+8] else 4)
            return True, "HIGH", "Valid 8-byte PNG magic header, IHDR chunk, and IEND footer chunk verified", end_offset

        if has_ihdr:
            return True, "LOW", "Valid PNG magic header and IHDR chunk verified, missing IEND footer chunk (truncated file)", len(data)

        return False, "LOW", "PNG header present, but missing IHDR chunk header", 0


class PDFValidator(BaseFormatValidator):
    """Format-aware validator for PDF documents (Header: %PDF-, Footer: %%EOF)."""

    def validate(self, data: bytes) -> Tuple[bool, str, str, int]:
        if len(data) < 100 or not data.startswith(b"%PDF-"):
            return False, "LOW", "Missing valid %PDF- document header signature", 0

        eof_idx = data.find(b"%%EOF")
        has_catalog = (b"/Root" in data) or (b"/Catalog" in data) or (b"xref" in data) or (b"/Pages" in data)

        if eof_idx != -1:
            end_offset = eof_idx + 5
            if has_catalog:
                return True, "HIGH", "Valid %PDF- header, %%EOF footer, and PDF Catalog/xref structural markers verified", end_offset
            return True, "MEDIUM", "Valid %PDF- header and %%EOF footer verified, missing catalog structure", end_offset

        return True, "LOW", "Valid %PDF- header signature found, but %%EOF footer marker is missing (truncated PDF)", len(data)


class ZIPValidator(BaseFormatValidator):
    """Format-aware validator for ZIP archives (Header: PK\x03\x04, Footer: PK\x05\x06)."""

    def validate(self, data: bytes) -> Tuple[bool, str, str, int]:
        if len(data) < 22 or not data.startswith(b"PK\x03\x04"):
            return False, "LOW", "Missing valid PK\\x03\\x04 ZIP local file header signature", 0

        eocd_idx = data.find(b"PK\x05\x06")
        has_central_dir = b"PK\x01\x02" in data

        if eocd_idx != -1:
            end_offset = eocd_idx + 22  # Minimum EOCD record size is 22 bytes
            if has_central_dir:
                return True, "HIGH", "Valid PK\\x03\\x04 local header, Central Directory (PK\\x01\\x02), and EOCD footer verified", end_offset
            return True, "MEDIUM", "Valid PK\\x03\\x04 local header and EOCD footer verified, missing central directory", end_offset

        return True, "LOW", "Valid PK\\x03\\x04 local header signature found, missing EOCD footer (truncated ZIP archive)", len(data)


class FormatValidatorFactory:
    """Factory mapping format names to validator instances."""

    _VALIDATORS = {
        "JPEG": JPEGValidator(),
        "PNG": PNGValidator(),
        "PDF": PDFValidator(),
        "ZIP": ZIPValidator(),
    }

    @classmethod
    def get_validator(cls, fmt: str) -> Optional[BaseFormatValidator]:
        return cls._VALIDATORS.get(fmt.upper())
