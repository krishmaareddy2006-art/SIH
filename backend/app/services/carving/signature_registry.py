"""Signature Registry for Forensic File Carving Engine.

Defines magic header signatures, footer signatures, size boundaries, and extensions
for supported file formats (JPEG, PNG, PDF, ZIP).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CarvingSignatureDefinition:
    file_type: str
    header_signature: bytes
    footer_signature: Optional[bytes]
    min_size_bytes: int
    max_size_bytes: int
    extension: str
    description: str


class CarvingSignatureRegistry:
    """Central registry mapping binary signatures and format boundaries."""

    _SIGNATURES: Dict[str, CarvingSignatureDefinition] = {
        "JPEG": CarvingSignatureDefinition(
            file_type="JPEG",
            header_signature=b"\xFF\xD8\xFF",
            footer_signature=b"\xFF\xD9",
            min_size_bytes=100,
            max_size_bytes=52_428_800,  # 50 MB
            extension=".jpg",
            description="Joint Photographic Experts Group Image",
        ),
        "PNG": CarvingSignatureDefinition(
            file_type="PNG",
            header_signature=b"\x89PNG\r\n\x1a\n",
            footer_signature=b"\x49\x45\x4e\x44\xae\x42\x60\x82",  # IEND chunk + CRC
            min_size_bytes=68,
            max_size_bytes=52_428_800,  # 50 MB
            extension=".png",
            description="Portable Network Graphics Image",
        ),
        "PDF": CarvingSignatureDefinition(
            file_type="PDF",
            header_signature=b"%PDF-",
            footer_signature=b"%%EOF",
            min_size_bytes=100,
            max_size_bytes=104_857_600,  # 100 MB
            extension=".pdf",
            description="Portable Document Format",
        ),
        "ZIP": CarvingSignatureDefinition(
            file_type="ZIP",
            header_signature=b"PK\x03\x04",
            footer_signature=b"PK\x05\x06",  # End of Central Directory
            min_size_bytes=22,
            max_size_bytes=104_857_600,  # 100 MB
            extension=".zip",
            description="ZIP Compressed Archive",
        ),
    }

    @classmethod
    def get_all_signatures(cls) -> List[CarvingSignatureDefinition]:
        return list(cls._SIGNATURES.values())

    @classmethod
    def get_signature_by_format(cls, fmt: str) -> Optional[CarvingSignatureDefinition]:
        return cls._SIGNATURES.get(fmt.upper())
