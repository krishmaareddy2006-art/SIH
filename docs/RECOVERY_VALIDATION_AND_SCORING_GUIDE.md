# ForensicShield: Recovery Validation & Confidence-Scoring Guide

## Executive Summary

The **ForensicShield Recovery Validation Engine (`v1.0.0-val-engine`)** provides automated, deterministic quality assurance and confidence scoring for carved and recovered file artifacts. 

Validation is performed strictly via **safe static binary byte analysis**. Recovered files, embedded scripts, or active macros are **NEVER executed**.

---

## 1. Core Principles & Safety Model

### 1.1 Non-Execution Safety Guarantee
- All structural inspection (magic bytes, segment headers, chunk CRCs, object trees) is executed in isolated, read-only memory buffers.
- Executables, DLLs, active PDF scripts (`/JavaScript`, `/OpenAction`), and Microsoft Office macros are identified purely by static byte pattern matching. No process creation or code execution occurs.

### 1.2 Deterministic Engine & Versioning
- Engine version: `v1.0.0-val-engine`.
- Identical artifact bytes and provenance inputs guarantee 100% reproducible factor scores, confidence labels, and explanatory reasons across all environments.

### 1.3 Statistical Probability Calibration Policy

> [!IMPORTANT]
> **MANDATORY CALIBRATION DISCLAIMER**:
> Validation scores (0–100) represent an empirical heuristic quality index based on structural integrity factors.
> Scores **MUST NEVER be presented to forensic operators or in legal reports as a statistical probability of truth** unless statistically calibrated against a ground-truth forensic dataset.

---

## 2. Transparent 7-Factor Scoring Model Rubric

Every recovered file is evaluated against 7 explainable factors summing to a total score between 0 and 100:

| Factor ID | Factor Name | Max Points | Evaluation Criteria |
| :--- | :--- | :---: | :--- |
| **F1** | `valid_header` | **20 pts** | Header magic signature verified at offset 0 (e.g., `FF D8 FF` for JPEG, `89PNG` for PNG, `%PDF-` for PDF, `PK\x03\x04` for ZIP). |
| **F2** | `valid_footer` | **15 pts** | Footer / end marker signature verified (e.g., `FF D9` for JPEG, `IEND` for PNG, `%%EOF` for PDF, `PK\x05\x06` EOCD for ZIP). |
| **F3** | `parser_success` | **20 pts** | Format-specific structural parser successfully parses internal chunks, marker tables, or catalog object trees. |
| **F4** | `complete_length` | **15 pts** | Actual file size matches calculated format container length exactly (15 pts), or contains minor trailing padding (10 pts). |
| **F5** | `checksum_crc_success` | **15 pts** | All internal payload checksums (PNG chunk CRC32, ZIP entry CRC32) match declared header digests. |
| **F6** | `source_provenance` | **10 pts** | Source evidence image SHA-256 hash provided (5 pts) and valid non-negative byte offset recorded (5 pts). |
| **F7** | `overlap_ambiguity` | **5 pts** | Absence of overlapping signature conflicts, container ambiguity, or header collisions. |

---

## 3. Confidence Label & Review Matrix

| Score Range | Confidence Label | UI Badge Color | Action & Manual Review Guidance |
| :---: | :--- | :--- | :--- |
| **85 – 100** | `HIGH_CONFIDENCE` | 🟢 Emerald / Green | Structure, footers, and CRCs verified intact. Suitable for immediate evidence indexing. |
| **60 – 84** | `MEDIUM_CONFIDENCE` | 🟡 Amber / Yellow | Container valid but minor trailing padding or missing metadata present. Review recommended. |
| **30 – 59** | `LOW_CONFIDENCE` | 🟠 Orange / Warning | Truncated file or CRC mismatch detected. Manual forensic investigation required. |
| **0 – 29** | `UNRELIABLE_CORRUPTED` | 🔴 Crimson / Red | Corrupted magic bytes, invalid structure, or severe truncation. High probability of unrecoverable data. |

> [!WARNING]
> `requires_manual_review = True` is automatically triggered whenever `overall_score < 70`, extension mismatch occurs, CRC fails, or security flags are raised.

---

## 4. Static Security Inspection & Risk Detection

The validation engine scans candidate files for hidden security risks prior to investigator review:

1. **PDF Active Content**: Scans for `/JS`, `/JavaScript`, `/OpenAction`, `/AA`, `/Launch`, and `/EmbeddedFile`.
2. **ZIP Decompression Bombs**: Flags entries exceeding a **100:1 uncompressed-to-compressed ratio**.
3. **Embedded Executables**: Flags Windows Portable Executables (`MZ`) or Linux binaries (`ELF`) embedded inside image payloads or archive streams.
4. **Extension Mismatches**: Detects files renamed with misleading extensions (e.g., JPEG file saved with `.png` or `.pdf` extension).

---

## 5. UI Display & Quality Assurance Recommendations

When rendering recovery validation results in the ForensicShield web interface, adhere to the following design recommendations:

### UI Component Layout Architecture

1. **Header Summary Card**:
   - Display File Name, Size (KB/MB), Detected Format Badge, Declared Extension, and Overall Score Radial Gauge (0–100).
   - Display `Confidence Label` badge (`HIGH_CONFIDENCE`, `MEDIUM_CONFIDENCE`, `LOW_CONFIDENCE`, `UNRELIABLE_CORRUPTED`).
   - If `is_extension_matched == False`, display a prominent Amber Extension Mismatch Warning Pill.

2. **Security & Truncation Alert Banner**:
   - If `security_flags` or `warnings` exist, render a dedicated Red/Amber Alert Box listing every detected risk factor (e.g. `PDF Active JavaScript Detected`).

3. **7-Factor Breakdown Interactive Table**:
   - Render a table showing all 7 factors with:
     - Status Icon (✅ Green Check for `passed: true`, ❌ Red Cross for `passed: false`).
     - Factor Name & Description.
     - Granted Points / Max Points (e.g. `20 / 20 pts`).
     - Factor Explanation string.

4. **Manual Review Recommendation Box**:
   - If `requires_manual_review == True`, display a callout box:
     > **MANUAL REVIEW RECOMMENDED**: This artifact contains structural anomalies, CRC mismatches, or security flags requiring investigator verification before court presentation.

5. **Mandatory Statistical Disclaimer Footer**:
   - Every validation panel MUST include the explicit disclaimer at the bottom:
     > *Empirical heuristic quality index (0-100). This score is NOT a statistical probability of truth.*
