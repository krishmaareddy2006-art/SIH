# ForensicShield Read-Only Device Discovery Security Model

This document outlines the security architecture, risk classification engine, and non-destructive execution guarantees of the ForensicShield Read-Only Device Discovery Service.

---

## Security Guarantees & Controls

### 1. Read-Only Non-Destructive Execution
- **Zero Disk Mutations**: The service invokes only query-only tools (`lsblk -J -b`, reading `/proc/mounts`, `/proc/swaps`, and `/sys/block`).
- **No Disk Operations**: The discovery service does NOT erase, mount, unmount, format, or alter partition tables.

### 2. Shell Injection Defense (`shell=False`)
- **Direct Subprocess Invocation**: All system commands use Python `subprocess.run(cmd_array, shell=False, capture_output=True, timeout=5)`.
- **String Commands Prohibited**: Shell execution via `shell=True` or string interpolation is strictly forbidden to prevent shell expansion attacks (`/dev/sda; rm -rf /`).

### 3. Device Path Allowlist & Canonicalization
- **Regex Allowlist Enforcement**: Paths are validated against `^/dev/(sd[a-z][0-9]*|nvme[0-9]+n[0-9]+(p[0-9]+)?|vd[a-z][0-9]*|mmcblk[0-9]+(p[0-9]+)?|loop[0-9]+)$`.
- **Canonical Real Path Verification**: Every path is canonicalized via `os.path.realpath`. Path traversal attempts (e.g. `/dev/../etc/shadow`) or arbitrary file references are rejected before payload generation.

### 4. Boot/System Disk Identification & Non-Destructibility Tagging
- **OS Root Detection**: Parses `/proc/mounts` to identify the block device hosting `/` or `/boot`.
- **Protection Flag**: System boot disks are automatically marked `is_boot_system_disk=True`, `is_destructible=False`, and assigned a `CRITICAL` risk score.

### 5. Platform Awareness Guard
- **Kernel Verification**: Checks `sys.platform == "linux"`. On non-Linux host platforms (e.g. Windows/macOS), returns `status: "UNSUPPORTED"` with an informational response without guessing or making unsafe system calls.

---

## Risk Score Matrix & Classification Rules

| Risk Score | Destructible Flag | Evaluation Criteria & Rationale |
| :--- | :--- | :--- |
| **`CRITICAL`** | `is_destructible = False` | Storage device hosts the active operating system root (`/`) or boot (`/boot`) filesystem. Modification blocks system execution. |
| **`HIGH`** | `is_destructible = False` | Storage device contains active mounted partitions or active swap space (`/proc/swaps`). Data loss risk if modified while mounted. |
| **`MEDIUM`** | `is_destructible = False` | Internal fixed hardware disk (SATA, NVMe, SCSI, PCI) that is not hotplug/removable. Requires explicit administrative override. |
| **`LOW`** | `is_destructible = True` | External removable hotplug drive (e.g., USB flash drive, SD card) with no active mounted partitions. Suitable for dry-run simulation. |
