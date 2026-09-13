# ForensicShield: Blockchain Integrity-Notarization Security & Threat Model

## Executive Summary

ForensicShield includes an optional **Blockchain Integrity-Notarization Engine** that anchors cryptographic digests of local audit log chains into a permissioned blockchain ledger or offline mock ledger (`mocknet-local-v1`).

The **local SHA-256 audit log chain remains the primary authoritative source of truth**. Blockchain notarization serves as an optional, privacy-preserving secondary proof layer.

---

## 1. On-Chain Privacy & Data Minimization Policy

To comply with digital privacy mandates (GDPR, HIPAA, ISO/IEC 27037:2012) and prevent sensitive evidence leakage, on-chain storage is strictly limited to non-sensitive cryptographic metadata:

| Field Name | On-Chain Value | Privacy Guarantee |
| :--- | :--- | :--- |
| `digest` | 64-character SHA-256 hex string | Fixed-length cryptographic one-way hash digest. |
| `case_pseudonym` | `CASE-PSEUDO-XXXX` | Anonymized salted hash (`SHA-256("SALT:case_id")[:16]`). Real case titles are **NEVER** stored. |
| `event_range` | `AUDIT-0001:AUDIT-0050` | Sequence range identifier string. |
| `timestamp` | UTC ISO 8601 string | Notarization transaction timestamp. |
| `tool_version` | `"ForensicShield v1.0.0"` | Tool software version tag. |
| `network_id` | `"mocknet-local-v1"` | Target ledger network identifier. |

> [!CAUTION]
> **STRICT PRIVACY GUARANTEE**:
> Raw evidence images, recovered file bytes, passwords, operator usernames, investigator PII, and absolute filesystem paths are **STRICTLY PROHIBITED** from on-chain storage.

---

## 2. Threat Model: What Blockchain DOES vs DOES NOT Prove

### 2.1 What Blockchain DOES Prove

1. **Proof of Existence at Timestamp $T$**:
   - Proves that a specific local audit chain tip digest existed at or before the ledger block timestamp $T$.
2. **Retroactive Anti-Tampering Proof**:
   - Proves that an investigator did not retroactively rewrite local audit log entries after timestamp $T$, because any past alteration changes the tip hash digest.
3. **Independent Third-Party Verification**:
   - Enables defense attorneys, courts, or external auditors to verify that ForensicShield's local audit log matches an independently notarized ledger entry without disclosing raw evidence contents.

### 2.2 What Blockchain DOES NOT Prove

1. **Initial Data Correctness**:
   - Does **NOT** prove that evidence uploaded at intake was truthful, accurate, or uncorrupted prior to logging ("Garbage In, Garbage Out").
2. **Local Data Repair**:
   - Does **NOT** repair or restore corrupted local evidence images or damaged local database files.
3. **Replacement for Local Audit Chain**:
   - Does **NOT** replace the local SHA-256 audit log chain. The local chain contains detailed event provenance and remains the primary authoritative forensic record.

---

## 3. Resilient Offline Architecture & Idempotency

### 3.1 Resilient Offline Queue (`NotarizationOfflineQueue`)
- ForensicShield is designed to operate in **air-gapped, offline forensic lab environments**.
- If the blockchain ledger network is unreachable or times out, the service enqueues the entry into an offline retry queue (`status: "PENDING"`, `tx_id: "TX-QUEUED-OFFLINE"`).
- When connectivity is restored, `flush_queue()` retries pending submissions with exponential backoff up to `BLOCKCHAIN_MAX_RETRIES` (default 3).

### 3.2 Idempotent Submissions
- Submitting the same audit digest multiple times returns the existing transaction receipt (`status: "ANCHORED"`, identical `tx_id`) without throwing duplicate key errors or creating redundant ledger transactions.

---

## 4. Feature Flag & Production Deployment Notes

### 4.1 Feature Flag Configuration
Blockchain notarization is disabled by default for zero-overhead local operation:

```env
ENABLE_BLOCKCHAIN_NOTARIZATION=false
BLOCKCHAIN_NETWORK_ID=mocknet-local-v1
BLOCKCHAIN_TIMEOUT_SECONDS=5
BLOCKCHAIN_MAX_RETRIES=3
```

When `ENABLE_BLOCKCHAIN_NOTARIZATION=false`, verification calls return status `Unavailable` with clear feature flag messages without throwing network exceptions.

### 4.2 Production Enterprise Adapter Integration
To deploy ForensicShield with a live permissioned blockchain network:
1. Implement `BaseNotarizationAdapter` for your target network (e.g. `HyperledgerFabricAdapter` or `EnterpriseEthereumAdapter`).
2. Set `ENABLE_BLOCKCHAIN_NOTARIZATION=true` in `.env`.
3. Configure `BLOCKCHAIN_NETWORK_ID` with your network identifier (e.g., `fabric-channel-forensic-v1`).
