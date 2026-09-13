# ForensicShield: Tamper-Evident Audit Logging Architecture & Threat Model

## Executive Summary

ForensicShield implements an **append-only, cryptographically linked tamper-evident audit logging architecture**. Every system event (logins, case creation, file erasure, storage sanitization, recovery, carving, safety gate rejections, and errors) is recorded as a canonicalized `AuditEvent` linked into an unbroken **SHA-256 cryptographic hash chain**.

Any unauthorized modification, deletion, or reordering of audit records breaks the cryptographic chain link and is immediately detected during automated verification scans.

---

## 1. Cryptographic Hash Chain Specifications

### 1.1 Genesis Block
- The initial audit event (sequence index 0) links to a fixed Genesis hash:
  $$\text{previous\_hash}_0 = \text{"0" \times 64}$$

### 1.2 Deterministic Canonicalization Standard
To guarantee cross-platform reproducibility, event parameters are canonicalized into a key-sorted, unpadded UTF-8 JSON string before hashing:

```json
{
  "action": "SAFETY_GATE_FAILURE",
  "actor": "operator1",
  "case_id": 1,
  "clock_source": "SERVER_UTC",
  "event_id": "AUDIT-20260913-9F8A1B2C",
  "evidence_id": "EVD-01",
  "result": "DENIED",
  "role": "Operator",
  "target_summary": "Device /dev/sda rejected: System boot disk protection triggered",
  "timestamp": "2026-09-13T07:59:17.605860+00:00",
  "tool_version": "ForensicShield v1.0.0"
}
```

### 1.3 Block Hash Formula
For each block $i$:
$$\text{current\_hash}_i = \text{SHA-256}(\text{canonical\_json}_i + \text{previous\_hash}_i)$$
where $\text{previous\_hash}_i = \text{current\_hash}_{i-1}$ for all $i > 0$.

---

## 2. Threat Model & Attack Mitigations

### 2.1 Threat Actor Profiles

1. **Attacker Profile T1: Malicious DB Administrator / SQL Access**
   - *Capability*: Direct SQL access to edit, delete, or reorder `audit_events` table rows.
   - *Mitigation*: Any SQL `UPDATE`, `DELETE`, or row swapping alters row fields or pointers, causing `verify_chain()` to immediately flag `is_valid: false`, identify the exact `first_broken_event_id`, and list all affected downstream event IDs.

2. **Attacker Profile T2: Compromised Application Server API**
   - *Capability*: Attempting to invoke HTTP endpoints to overwrite or delete audit logs.
   - *Mitigation*: Immutability guards on `PUT /api/v1/audit/logs/{event_id}` and `DELETE /api/v1/audit/logs/{event_id}` return HTTP 403 Forbidden (`AUDIT_LOG_IMMUTABLE`).

3. **Attacker Profile T3: Malicious Operator / Credential Exfiltration**
   - *Capability*: Attempting to inject passwords, tokens, or JWTs into log summaries.
   - *Mitigation*: Automatic sensitive parameter scrubbing (`sanitize_target_summary()`) redacts passwords and bearer tokens (`password=[REDACTED]`, `Bearer [REDACTED]`) prior to canonicalization.

---

## 3. Threat Matrix & Diagnostic Verification

| Attack Vector | Detection Mechanism | Diagnostic Output |
| :--- | :--- | :--- |
| **Field Modification** (Modifying actor, action, or target summary of an existing event) | Recalculated `SHA-256(canonical_json + previous_hash)` does not match recorded `current_hash`. | `is_valid: false`<br>`broken_index: i`<br>`reason: "Field tampering detected at sequence index i"`<br>`affected_event_ids: [ID_i, ID_i+1, ...]` |
| **Record Deletion** (Deleting an event row from middle of chain) | Next record's `previous_hash` does not match prior record's `current_hash`. | `is_valid: false`<br>`broken_index: i`<br>`reason: "Previous hash link broken at sequence index i"` |
| **Record Reordering** (Swapping 2 event row positions) | Pointer chain break and block hash mismatch. | `is_valid: false`<br>`chain_status: "BROKEN_CHAIN_DETECTED"` |
| **Credential Ingestion** | Regex sanitizer scrubs credentials before block hashing. | Passwords/Tokens replaced with `[REDACTED]`. |

---

## 4. Export Verification & Blockchain Ledger Integration

### 4.1 Export Integrity Digest (`X-Export-SHA256`)
When exporting audit logs to JSON or CSV (`/api/v1/audit/export/json`, `/api/v1/audit/export/csv`), the server computes the SHA-256 digest of the entire exported byte stream and attaches it in the HTTP response header `X-Export-SHA256`.

### 4.2 Permissioned Blockchain Adapter (`BaseBlockchainAdapter`)
- Local SHA-256 hash chain serves as the primary source of truth.
- An abstract blockchain adapter (`BaseBlockchainAdapter`) permits secondary anchoring into permissioned ledgers (e.g. Hyperledger Fabric, Ethereum enterprise node).
- `SimulatedBlockchainAdapter` provides in-memory ledger simulation for test environments.
