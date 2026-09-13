# ForensicShield: Signature-Based File Carving Accuracy & Fragmentation Limitations

## Executive Summary

ForensicShield implements a signature-based raw content carving engine designed to recover file artifacts from raw disk images, unallocated disk space, or corrupted filesystems. 

Signature carving operates independently of filesystem metadata (such as FAT, MFT, or Ext inodes). While highly effective for contiguous file recovery, **pure signature carving has fundamental accuracy limitations when dealing with fragmented or non-contiguous file allocations**.

This document outlines the operational mechanics, validation algorithms, confidence scoring matrix, evidentiary safeguards (ISO/IEC 27037:2012), and explicit limitations regarding fragmented files.

---

## 1. Supported File Formats & Signature Registry

The ForensicShield carving registry defines strict criteria for header magic, footer markers, size bounds, and format validators:

| Format | Extension | Header Signature (Hex) | Footer Marker (Hex) | Min Size | Max Size | Primary Structural Check |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JPEG** | `.jpg` / `.jpeg` | `FF D8 FF` (SOI) | `FF D9` (EOI) | 64 B | 50 MB | SOF0/EXIF/JFIF marker validation |
| **PNG** | `.png` | `89 50 4E 47 0D 0A 1A 0A` | `49 45 4E 44 AE 42 60 82` (IEND + CRC) | 67 B | 50 MB | IHDR chunk structure & CRC check |
| **PDF** | `.pdf` | `25 50 44 46 2D` (`%PDF-`) | `25 25 45 4F 46` (`%%EOF`) | 100 B | 200 MB | Catalog (`/Catalog`) or xref table check |
| **ZIP** | `.zip` | `50 4B 03 04` (`PK\x03\x04`) | `50 4B 05 06` (`PK\x05\x06`) | 22 B | 500 MB | Central directory header (`PK\x01\x02`) check |

---

## 2. Confidence Scoring Matrix & Validation Logic

Each carved candidate is processed by format-aware structural validators to eliminate false positives and calculate an empirical confidence rating:

### Confidence Levels

- **HIGH Confidence**:
  - Valid header magic at target offset.
  - Valid footer marker found within `max_size_bytes`.
  - Format-specific metadata structure present (e.g., valid PNG IHDR + IEND chunk, valid PDF xref/Catalog, valid ZIP central directory).
- **MEDIUM Confidence**:
  - Valid header magic and footer marker found within bounds.
  - Format metadata incomplete or non-standard, but basic container boundaries are intact.
- **LOW Confidence**:
  - Valid header signature identified.
  - Footer marker missing or truncated (e.g., end of disk reached before footer).
  - Subject to potential false positive header matches in raw data.

---

## 3. Handling Overlapping, Nested, and Corrupted Candidates

1. **Chunked Boundary Overlap**: Scans disk images in 1 MB chunks with 256-byte overlap, ensuring signatures spanning block boundaries are never missed.
2. **Untrusted Allocations**: Buffer allocation is bounded by `min(max_size_bytes, image_size - start_offset)`. Memory is never allocated directly from internal size fields embedded in untrusted file headers.
3. **De-overlapping Algorithm**: When nested signatures (e.g., a thumbnail JPEG embedded within a larger parent JPEG) or overlapping header candidates occur, candidates are sorted by start offset and length, selecting the longest valid candidate unless nested structure validation confirms distinct sub-files.
4. **Deduplication**: Carved output files are hashed (SHA-256). Duplicate extracted files are consolidated to optimize investigator review efficiency.

---

## 4. Fundamental Accuracy Limitations: Fragmented Files

> [!CAUTION]
> **ForensicShield DOES NOT claim fragmented-file reassembly in this signature carving module.**

### Technical Explanation of Fragmentation Failure

Signature-based carving reads contiguous byte streams starting from a recognized header signature up to a calculated or identified footer.

```
Contiguous Allocation (Carved Successfully):
[ HEADER ][ DATA BLOCK A ][ DATA BLOCK B ][ FOOTER ]  ---> Carved File (100% Intact)

Fragmented Allocation (Carving Corruption):
[ HEADER ][ DATA BLOCK A ][ SECTOR OF UNRELATED DATA ][ DATA BLOCK B ][ FOOTER ]
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
                           Interleaved sector breaks internal format parsing
```

When a file is fragmented across non-contiguous disk sectors:
1. **Linear Splice Corruption**: The carved stream will linearly splice unrelated sector data into the carved artifact between the header and footer.
2. **Format Decoder Failures**:
   - In **JPEG**: Entropy-coded Huffman streams will fail decoding, resulting in visual gray/distorted blocks below the fragmentation point.
   - In **PNG**: CRC32 check failures occur on chunk payloads following the fragment boundary.
   - In **ZIP**: Decompression algorithms (Deflate) will raise CRC errors or invalid distance code exceptions.
   - In **PDF**: Stream object offsets (`xref`) will point to incorrect byte positions, rendering pages unreadable.

3. **Advanced Bifragment Gap Carving Requirements**: True fragmented file recovery requires smart bi-fragment gap carving, entropy analysis, format-specific reassembly heuristics, or filesystem metadata (FAT cluster chains, MFT run lists). ForensicShield marks non-contiguous candidate failures as `LOW` confidence or `Rejected` during format structural validation.

---

## 5. Evidentiary Integrity & ISO/IEC 27037:2012 Compliance

ForensicShield adheres to digital evidence preservation standards:
- **Read-Only Access**: Original evidence images are mounted/accessed in strict read-only mode (`rb`).
- **Integrity Verification**: Source evidence SHA-256 hash is computed before and after carving execution. Any mismatch aborts processing and flags `Integrity-Failure`.
- **Chain of Custody**: Every carved artifact records:
  - Source evidence ID and source image SHA-256 hash.
  - Absolute sector/byte source offset and end offset.
  - Carving engine version and signature registry version.
  - Carved artifact SHA-256 hash.
