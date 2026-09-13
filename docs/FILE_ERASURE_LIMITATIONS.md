# ForensicShield Controlled File Erasure: Security Model & Technical Limitations

This document details the security architecture, sandbox isolation guards, and technical limitations of the ForensicShield Controlled File & Folder Erasure Module.

---

## 1. Technical Limitations & SSD Disclaimer

### Logical File Overwriting vs. Hardware Physical Sanitization
- **Logical File Overwrite**: Overwrites the file data bytes allocated to the file in the active operating system filesystem (e.g. ext4, NTFS, FAT32) and issues an `os.fsync(fd)` call after each pass before unlinking the file inode/MFT entry.
- **SSD / Flash Memory Wear-Leveling Limitation**: Modern solid-state drives (SSDs), NVMe drives, and flash storage utilize Flash Translation Layers (FTL), wear-leveling algorithms, and over-provisioned spare blocks. Writing to an existing file logical block address (LBA) does **NOT** guarantee that the physical NAND flash cells underlying previous writes are immediately physically purged.
- **Hardware Sanitization Requirement**: True physical sanitization of flash storage requires drive-level hardware commands (such as ATA Secure Erase, NVMe Format with Cryptographic Erase, or physical degaussing/shredding).
- **Audit Labeling**: All generated reports explicitly state:
  > *"LOGICAL FILE ERASURE DISCLAIMER: File contents were logically overwritten with zero/pattern passes and unlinked via filesystem fsync. Physical flash media (SSD/NVMe) wear-leveling FTL blocks may retain latent physical data without ATA/NVMe hardware sanitization."*

---

## 2. Security Guards & Isolation Guarantees

### Approved Root Sandbox Guard (`PathSandboxGuard`)
- **Sandbox Boundary**: Targets MUST reside inside a user-approved root directory (e.g. `/evidence/case_101_sandbox`).
- **Path Traversal Defense**: The service canonicalizes all paths via `os.path.realpath` and verifies `os.path.commonpath([target, approved_root]) == approved_root`.
- **System Root Protection**: Hardcoded guards block targeting protected system roots (`/`, `/boot`, `/etc`, `C:\`, `C:\Windows`) and the ForensicShield project repository root (`c:\SIH`).

### Symlink Non-Following Policy (`follow_symlinks=False`)
- **Symlink Escape Defense**: Symbolic links inside an evidence directory are unlinked as link nodes without recursing into or modifying the target file/directory referenced by the symlink.
- **External Target Safety**: Target files outside the approved root referenced by a symlink inside the sandbox remain completely untouched.

### Two-Factor Confirmation Token System
- Live execution requires a unique typed confirmation token formatted as `CONFIRM:<target_path>:<token_hash>`.
- Token hashes are HMAC-SHA256 digests generated server-side using the server `SECRET_KEY`, target path, and user ID.

### Special File Filters
- Sockets, FIFO named pipes, character devices, and block device nodes inside directories are automatically skipped with status `SKIPPED` / `UNSUPPORTED` to prevent system IPC/driver deadlocks.

---

## 3. Per-Item Status Categories

| Status Code | Description |
| :--- | :--- |
| **`PLANNED`** | Item listed during dry-run preview mode. No file modifications performed. |
| **`ERASED`** | Item successfully overwritten with pattern passes, flushed via `fsync()`, and unlinked. |
| **`SKIPPED`** | Item skipped (special device node, IPC pipe, or user cancellation request). |
| **`FAILED`** | Item encountered an I/O error or permission error that could not be recovered. |
| **`UNSUPPORTED`** | Item format unsupported by logical erasure module. |
| **`REQUIRES_REVIEW`** | Item requires manual forensic analyst inspection. |
