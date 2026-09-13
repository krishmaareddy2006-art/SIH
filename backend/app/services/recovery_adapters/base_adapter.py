"""Abstract Base Adapter Interface for Forensic Filesystem & Disk Image Recovery."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.schemas.recovery import CandidateItem


class BaseFilesystemAdapter(ABC):
    """Abstract interface defining standard methods for filesystem recovery adapters."""

    @property
    @abstractmethod
    def filesystem_name(self) -> str:
        """Returns the canonical filesystem identifier (e.g., FAT32, NTFS, EXT4)."""
        pass

    @abstractmethod
    def detect(self, file_handle, image_size: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Scans file_handle headers/superblocks to detect filesystem signature.
        Returns (is_detected, filesystem_name, metadata_dict).
        """
        pass

    @abstractmethod
    def scan_deleted_entries(
        self,
        file_handle,
        image_size: int,
        check_cancelled: Optional[Callable[[], bool]] = None,
    ) -> List[CandidateItem]:
        """
        Scans unallocated clusters / directory structures for deleted file candidates.
        Enforces strict bounds checking and candidate status classification.
        """
        pass

    @abstractmethod
    def extract_candidate_data(
        self,
        file_handle,
        candidate: CandidateItem,
        image_size: int,
        output_dir: Path,
    ) -> Tuple[bool, Path, str, int]:
        """
        Safely extracts candidate data extents from file_handle into output_dir.
        Returns (success, output_file_path, sha256_hash_of_output, bytes_written).
        """
        pass
