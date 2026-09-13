# ForensicShield Operator Safety Guide & Anti-One-Click Architecture Policy

## Architectural Policy Statement: Prohibition of One-Click Unrestricted Wiping

In digital forensics and incident response (DFIR), accidental triggers of disk wiping or file destruction invalidate legal chain-of-custody, destroy critical evidentiary data, and risk rendering investigator workstations unbootable.

**ForensicShield explicitly forbids any "one-click", unrestricted, or unvalidated wipe functionality.**

All storage sanitization and logical file erasure capabilities are engineered behind a **Multi-Stage Safety-First Orchestration Architecture** requiring explicit preflight inspection, 8-point safety gate validation, target classification, typed two-factor confirmation tokens, simulation-first defaults, and physical test-lab allowlist controls.

---

## The 5-Stage Operator Safety Workflow

```
[ Stage 1: Preflight & Safety Gate ] ──> [ Stage 2: Target Classification ] ──> [ Stage 3: Confirmation Token ]
                                                                                         │
[ Stage 5: Postflight Sample Audit ] <── [ Stage 4: Simulation-First Execution ] <───────┘
```

### Stage 1: Preflight & 8-Point Safety Gate Inspection
**API Endpoint**: `POST /api/v1/sanitization/preflight`

Before any job can be planned, the system evaluates the 8-Point Safety Gate:
1. **Administrator Authorization**: Only authenticated users with `Administrator` role can initiate preflight.
2. **Typed Path Allowlist**: Device path must match allowlist regex (`/dev/sda`, `/dev/nvme0n1`) and canonical real path.
3. **Stable Identifier Match**: Device path resolved to `/dev/disk/by-id/` or hardware serial.
4. **System-Disk Exclusion**: Target must NOT contain OS root (`/`) or boot (`/boot`) filesystems.
5. **Mounted Partition & Swap Check**: Target must NOT contain active mounted partitions or active swap space (`/proc/swaps`).
6. **Device Capability Match**: Method must be compatible with hardware transport.
7. **Confirmation Token Check**: Validates token string.
8. **Active Case ID Check**: Case must exist in database and be `OPEN`.

---

### Stage 2: Storage Classification & FTL Wear-Leveling Audit

The system classifies the storage target:
- **`HDD`**: Recommended Method: `DOD_5220_22_M_3_PASS_OVERWRITE` (Confidence: `HIGH`).
- **`SSD`**: Recommended Method: `ATA_SECURE_ERASE` (Confidence: `HIGH`). Software overwriting is flagged as `LOW` confidence due to FTL wear-leveling spare blocks.
- **`NVME`**: Recommended Method: `NVME_FORMAT_CRYPTO_ERASE` (Confidence: `HIGH`). Software overwriting is flagged as `LOW` confidence.
- **`USB_FLASH`**: Recommended Method: `USB_CONTROLLER_SANITIZE` (Confidence: `MEDIUM`).
- **`VIRTUAL_DISK`**: Recommended Method: `VIRTUAL_DISK_UNLINK_AND_HYPERVISOR_PURGE` (Confidence: `HIGH`).
- **`UNKNOWN`**: Flagged as `LOW` confidence requiring manual analyst review.

---

### Stage 3: Two-Factor Confirmation Token Generation
**API Endpoint**: `POST /api/v1/sanitization/token`

The system generates a unique confirmation requirement string formatted as:
```text
CONFIRM:<canonical_device_path>:<case_id>:<token_hash>
```
An operator must manually type this exact string into the request payload. Automated or generic strings (`"YES"`, `"CONFIRM"`) are rejected server-side.

---

### Stage 4: Simulation-First Execution Pipeline
**API Endpoint**: `POST /api/v1/sanitization/execute`

- **Simulation Default**: `REAL_DEVICE_OPERATIONS=false` and `SAFE_MODE=true` are strictly enforced by default.
- **Mock Hardware Adapters**: Commands execute via `SimulatedHardwareAdapter`, generating 5-step dry-run progress callbacks (0% to 100%) without invoking hardware commands or altering disk blocks.
- **Physical Test-Lab Allowlist Guard**: If `REAL_DEVICE_OPERATIONS=true` is enabled in a hardware test lab, real execution is blocked unless the target device serial number is explicitly listed in `TEST_LAB_DEVICE_ALLOWLIST`.

---

### Stage 5: Postflight Block Sampling & Audit Logging

- **Zero Content Logging**: Every command intent, request ID, case ID, user ID, target class, and method is logged to structured JSON logs. **No secrets, confirmation tokens, or raw drive payload data are ever logged.**
- **Postflight Sample Verification**: Block sampling checks verify zero readable data.
- **Result States**: Output classified as `SIMULATED`, `COMPLETED_VERIFIED`, `COMPLETED_INCONCLUSIVE`, `FAILED`, `UNSUPPORTED`, `ABORTED`, or `MANUAL_REVIEW`.

---

## Operator Error Recovery Guide

| Error Code | Root Cause | Operator Action |
| :--- | :--- | :--- |
| `SAFETY_GATE_REJECTED` | Target is system boot disk or contains mounted partitions. | Unmount partitions using standard Linux tools (`umount`), turn off swap (`swapoff`), and re-run preflight. System boot disks cannot be sanitized. |
| `INVALID_CONFIRMATION_TOKEN` | Typed token string did not match expected `CONFIRM:<path>:<case>:<hash>`. | Re-request token via `POST /api/v1/sanitization/token` and copy/paste exact requirement string. |
| `TEST_LAB_ALLOWLIST_DENIED` | Real device operation attempted on device not registered in test lab allowlist. | Add device serial number to `TEST_LAB_DEVICE_ALLOWLIST` in environment configuration. |
| `PERMISSION_DENIED` | User lacks `Administrator` role. | Log in with Administrator credentials. |
