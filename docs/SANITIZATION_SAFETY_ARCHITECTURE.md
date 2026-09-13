# ForensicShield Safe Storage Sanitization Safety Architecture

This document details the safety architecture, 8-point mandatory safety gate, target classification rules, hardware adapter isolation, and physical test-lab allowlist guards for ForensicShield.

---

## 1. Safety Principles & Default Posture

1. **Simulation-Only Default**: `REAL_DEVICE_OPERATIONS=false` and `SAFE_MODE=true` are strictly enforced by default. All storage sanitization operations perform dry-run simulations. Zero hardware bytes are modified.
2. **Zero Destruction in Tests / Safe Mode**: Tests and safe-mode executions use `SimulatedHardwareAdapter` which mocks step execution and emits progress callbacks without invoking hardware binaries.
3. **Physical Test-Lab Allowlist Requirement**: Even if an operator enables `REAL_DEVICE_OPERATIONS=true`, real hardware commands are blocked unless the target device serial number / stable identifier is explicitly registered in `TEST_LAB_DEVICE_ALLOWLIST`.
4. **Command Adapter Isolation**: Real hardware command execution adapters (ATA Secure Erase, NVMe Format with Cryptographic Erase) are isolated behind a separate disabled interface (`RealDeviceHardwareAdapter`).

---

## 2. 8-Point Mandatory Safety Gate

Every sanitization request must pass 8 validation checks before a preflight report or execution token can be issued:

| Check # | Safety Check Description | Failure Outcome |
| :--- | :--- | :--- |
| **Check 1** | **Administrator Authorization** | Rejected if `current_user.role.name != "Administrator"`. |
| **Check 2** | **Typed Device Path Allowlist** | Rejected if device path fails allowlist regex or canonical real path verification. |
| **Check 3** | **Stable Device Identifier Verification** | Verified against `/dev/disk/by-id/` or hardware serial. |
| **Check 4** | **System-Disk Exclusion** | Rejected if device contains OS root (`/`) or boot (`/boot`) filesystems. |
| **Check 5** | **Mounted Partition & Active Swap Status** | Rejected if device contains active mounted partitions or active swap partitions (`/proc/swaps`). |
| **Check 6** | **Device Capability & Method Match** | Verified that recommended/selected method is compatible with storage target. |
| **Check 7** | **Typed Confirmation Token Match** | Rejects request if token does not match `CONFIRM:<device_path>:<case_id>:<token_hash>`. |
| **Check 8** | **Active Case ID Association** | Rejects if associated forensic case is missing or `CLOSED`. |

---

## 3. Storage Target Classification & Confidence Matrix

| Target Class | Detection Rules | Recommended Method | Confidence Level | FTL / Wear-Leveling Technical Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`NVME`** | Transport: `nvme`, Path: `/dev/nvme*` | `NVME_FORMAT_CRYPTO_ERASE` | **HIGH** | NVMe Format (Command Set 0x80) or NVMe Sanitize purges over-provisioned flash blocks. Software overwrites provide LOW confidence. |
| **`SSD`** | Transport: `sata`, Non-rotational (`rota=0`) | `ATA_SECURE_ERASE` | **HIGH** | ATA Secure Erase (`hdparm --security-erase`) or ATA Sanitize purges remitted NAND blocks. Software overwrites provide LOW confidence. |
| **`HDD`** | Transport: `sata/scsi/ide`, Rotational (`rota=1`) | `DOD_5220_22_M_3_PASS_OVERWRITE` | **HIGH** | Fixed physical LBA track mappings. Multi-pass software overwriting provides HIGH confidence for magnetic tracks. |
| **`USB_FLASH`** | Transport: `usb` or hotplug drive | `USB_CONTROLLER_SANITIZE_OR_CRYPTO_ERASE` | **MEDIUM** | Lacks standard ATA/NVMe passthroughs. Overwriting clears visible LBA blocks, but bad-block pools may retain data. |
| **`VIRTUAL_DISK`** | Path: `/dev/loop*`, Model: `QEMU/VBOX/VMware` | `VIRTUAL_DISK_UNLINK_AND_HYPERVISOR_PURGE` | **HIGH** | Resides on host storage pools. Unlinking image files and issuing hypervisor volume trim commands is required. |
| **`UNKNOWN`** | Unrecognized transport/controller | `MANUAL_FORENSIC_ANALYST_REVIEW` | **LOW** | Unidentified controller capabilities. Manual physical inspection required before procedure authorization. |

---

## 4. Execution Result States

- **`SIMULATED`**: Sanitization dry-run simulation completed successfully. 0 hardware bytes modified.
- **`COMPLETED_VERIFIED`**: Real hardware command completed and postflight block sampling verified zero data.
- **`COMPLETED_INCONCLUSIVE`**: Real hardware command executed but postflight block sampling returned non-deterministic status.
- **`FAILED`**: Hardware command or pipeline step returned error.
- **`UNSUPPORTED`**: Target storage class or method unsupported by system environment.
- **`ABORTED`**: Sanitization cancelled mid-stream by user or cancellation token.
- **`MANUAL_REVIEW`**: Safety gate or target classification requires manual forensic analyst review.
