# ForensicShield: Read-Only Evidence Image Intake & Chain-of-Custody Architecture

## 1. Overview & Chain-of-Custody Principles

Digital evidence integrity requires strict compliance with international forensic standards (ISO/IEC 27037:2012). ForensicShield enforces an uncompromised chain-of-custody model through read-only file ingestion, 64 KB chunked streaming SHA-256 hash verification, pre-stage tamper detection, and standardized evidence manifest exports.

```
 +------------------------+
 | Original Source Image  | (Read-Only Handle 'rb')
 +------------------------+
             |
             v
 +------------------------+
 | Streaming SHA-256      | (64 KB Bounded Chunks, Progress & Cancellation)
 | Calculator             |
 +------------------------+
             |
             +----------------------------+
             |                            |
             v                            v
 +------------------------+   +------------------------+
 | Immutable Working Copy |   | Metadata DB Record     |
 | (chmod 0o444 / IREAD)  |   | (sha256, operator,     |
 +------------------------+   |  import_time, status)  |
                               +------------------------+
                                          |
                                          v
                               +------------------------+
                               | Pre-Stage Re-Hash      |
                               | Verification           |
                               +------------------------+
                                 /                    \
                     Hash Match /                      \ Hash Mismatch
                               v                        v
                  +------------------+         +--------------------+
                  | Continue Stage   |         | INTEGRITY_FAILURE  |
                  | (Status:VERIFIED)|         | (HTTP 409 Abort)   |
                  +------------------+         +--------------------+
```

---

## 2. Key Architectural Guarantees

### 2.1 Read-Only Source Intake
- **No In-Place Modifications**: Original source evidence files are opened exclusively using binary read-only handles (`open(path, "rb")`).
- **Working Copy Isolation**: When working copies are created for analysis, the copy is saved to an isolated sandbox location and stripped of write permissions (`stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH`).

### 2.2 Memory-Bounded 64 KB Streaming Hash Calculation
- Evidence files frequently exceed hundreds of gigabytes (`.raw`, `.dd`, `.e01`). Loading entire files into memory risks system crash or out-of-memory (OOM) errors.
- `StreamingHashCalculator` processes data in fixed 64 KB (`65,536 bytes`) chunks. Memory footprint remains constant (~64 KB) regardless of file size.
- Supports real-time progress callbacks `progress_callback(processed_bytes, total_bytes)` and interruptible cancellation tokens `check_cancelled()`.

### 2.3 Pre-Stage Tamper Detection & Integrity Failure Rejection
- Forensic analysis pipelines execute across multiple stages (e.g., `PRE_CARVING`, `KEYWORD_SEARCH`, `TIMELINE_ANALYSIS`).
- Before executing any stage, `verify_evidence_integrity()` recalculates the SHA-256 hash from disk.
- **Instant Tamper Rejection**: If the recalculated hash does not match `sha256_hash`:
  1. The item's `processing_status` in the database is set to `INTEGRITY_FAILURE`.
  2. An audit log frame with `operation="EVIDENCE_INTEGRITY_FAILURE"` and `status="INTEGRITY_FAILURE"` is generated.
  3. A `ForensicShieldException` with HTTP 409 Conflict is raised, immediately terminating the processing job.

### 2.4 Path Traversal & Sandbox Isolation
- `PathSandboxGuard` canonicalizes all input file paths using `os.path.realpath`.
- Enforces system path rejection rules (`FORBIDDEN_SYSTEM_PATHS`), preventing operators from targeting protected OS directories (`C:\Windows`, `/etc`, `/boot`).
- Rejects path traversal escapes (e.g., `../../../etc/passwd`).

---

## 3. Metadata Schema & Audit Log Fields

Every evidence intake record captures the following forensic metadata:

| Field | Type | Description |
| :--- | :--- | :--- |
| `evidence_id` | `String(100)` | Unique identifier (`EVD-YYYYMMDDHHMMSS-xxxxxx`) |
| `case_id` | `Integer` | Foreign key referencing target Forensic Case |
| `item_number` | `String(50)` | Sequential item tracking number (`EVID-001`) |
| `title` | `String(200)` | Operator assigned title |
| `original_filename` | `String(255)` | Original filename of source evidence image |
| `file_path` | `String(500)` | Absolute reference path to original source image |
| `working_copy_path` | `String(500)` | Path to read-only working copy |
| `file_size_bytes` | `BigInteger` | Exact byte count of evidence image |
| `sha256_hash` | `String(64)` | Immutable SHA-256 cryptographic hash |
| `import_time` | `DateTime` | UTC timestamp of initial intake |
| `source_description` | `Text` | Contextual acquisition notes |
| `operator_username` | `String(100)` | Authenticated operator who performed intake |
| `tool_version` | `String(50)` | Tool version string (`ForensicShield v1.0.0`) |
| `processing_status` | `String(50)` | Status (`IMPORTED`, `VERIFIED`, `INTEGRITY_FAILURE`) |
| `last_verified_at` | `DateTime` | UTC timestamp of last hash re-verification |

---

## 4. Evidence Manifest Exports

Court compliance requires downloadable evidence manifest exports. ForensicShield supports two formats:

1. **Structured JSON Manifest (`/api/v1/cases/{case_id}/evidence/manifest/json`)**:
   Contains manifest version (`1.0.0`), UTC export timestamp, exporting operator username, case number, item count, and full evidence item metadata array.

2. **RFC 4180 Compliant CSV Manifest (`/api/v1/cases/{case_id}/evidence/manifest/csv`)**:
   Standardized CSV spreadsheet export formatted for courtroom submission, including headers and all forensic chain-of-custody fields.
