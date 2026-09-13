# ForensicShield - SIH 2026 Live Demonstration & Technical Pitch Script

> **Total Duration**: 5 to 7 Minutes  
> **Roles**: Presenter (Presenter 1 - Pitch / Storyteller), Technical Driver (Presenter 2 - UI & System Commands)  
> **Prerequisite Environment**: Run `python run_sih_demo.py` or double-click `start_sih_demo.bat`.

---

## Script Overview & Timeline

| Time Marker | Demonstration Stage | Key Technical Action / UI Focus | Presenter Focus |
| :---: | :--- | :--- | :--- |
| **0:00 - 0:45** | **1. Introduction & Problem** | Open Dashboard (`http://localhost:5173`) | Highlight accidental wiping risks & chain-of-custody gaps. |
| **0:45 - 1:30** | **2. Case & Evidence Intake** | Open Evidence Intake Page (`EVD-SIH-DISK-01`) | Explain read-only intake & 64 KB streaming SHA-256 calculation. |
| **1:30 - 2:15** | **3. FAILURE DEMO (Safety Gate)** | Attempt wipe on `C:\Windows` or `/dev/sda` | **SHOW CRITICAL FAILURE**: 8-Point Gate blocks OS system disk! |
| **2:15 - 3:15** | **4. Storage Classification & Wipe**| Select `/dev/sdb`, dynamic token `CONFIRM...` | Show HDD/SSD classification, dry-run simulation & zero byte change. |
| **3:15 - 4:15** | **5. Signature File Carving** | Open Recovery Workspace (`CARV-JPEG`, `PDF`) | Show 1 MB chunk scanner, format checks, and deduplication. |
| **4:15 - 5:00** | **6. 7-Factor Validation Score** | View Validation Details (`HIGH` vs `LOW`) | Explain transparent scoring index (no arbitrary probability claims). |
| **5:00 - 6:00** | **7. Audit Chain & Tampering** | Open Audit Chain Page & Click 'Verify' | Demonstrate SHA-256 hash chaining & instant tampering detection. |
| **6:00 - 7:00** | **8. Report Export & Conclusion**| Click 'Generate PDF Report' | Download court-compliant PDF report & conclude pitch. |

---

## Detailed Step-by-Step Presenter Dialogue & UI Actions

### Step 1: Introduction & Problem Context (0:00 - 0:45)

**Presenter 1**:
> *"Respected Judges, welcome to ForensicShield. In digital forensics and enterprise sanitization, law enforcement officers face two massive challenges: first, commercial wiping software often lacks safety boundaries—a single accidental click can wipe an active OS boot disk. Second, court evidence is frequently dismissed because audit logs can be edited or tampered with after an incident. Today, we present ForensicShield—a court-compliant, safety-first digital forensics and sanitization system."*

**Technical Driver Action**:
- Show `DashboardPage` displaying system metrics, active case `CAS-SIH-2026-001`, and unbroken audit chain status banner.

---

### Step 2: Case Creation & Read-Only Evidence Intake (0:45 - 1:30)

**Presenter 1**:
> *"Let's look at evidence intake. ForensicShield opens original evidence files strictly in binary read-only mode (`rb`). We calculate SHA-256 hashes in 64 KB streaming chunks without loading full disk images into RAM."*

**Technical Driver Action**:
- Navigate to `EvidenceIntakePage`.
- Point out `EVD-SIH-DISK-01` (`synthetic_test_disk_01.raw`, 10.0 MB).
- Show verified SHA-256 hash `effcb0dbb243905bd2c0a025...` and `VERIFIED` intake status.

---

### Step 3: FAILURE DEMO — System Disk Safety Gate Protection (1:30 - 2:15)

**Presenter 1**:
> *"Now, let's test our core safety guarantee: Can an operator accidentally destroy the host operating system? Watch what happens if we attempt to sanitize system drive `C:\Windows` or `/dev/sda`."*

**Technical Driver Action**:
- Navigate to `DriveSanitizationPage`.
- Select or enter system drive target: `C:\Windows` (or `/dev/sda`).
- Click **Evaluate Safety Gates**.

**Presenter 1**:
> *"Notice the result: The system IMMEDIATELY BLOCKS execution! Our 8-Point Mandatory Safety Gate evaluates system disk markers, active mount points, administrator RBAC roles, and path allowlists. It rejects the operation with HTTP 403 Forbidden before a single sector can be touched."*

---

### Step 4: Storage Classification & Dry-Run Sanitization (2:15 - 3:15)

**Presenter 1**:
> *"Now let's select an approved secondary target `/dev/sdb`. ForensicShield automatically classifies storage media into HDD, SSD, NVMe, or USB Flash, warning operators about FTL wear-leveling caveats."*

**Technical Driver Action**:
- Select secondary target device `/dev/sdb`.
- Open `DryRunPreviewModal` displaying sanitization plan.
- Enter required typed dynamic confirmation token: `CONFIRM DESTROY /dev/sdb`.
- Click **Start Dry-Run Sanitization**.

**Presenter 1**:
> *"Notice that `SAFE_MODE=true` is strictly enforced. The system executes a 5-pass DoD simulation via our `SimulatedHardwareAdapter`. Zero hardware bytes are modified, guaranteeing safety in field operations."*

---

### Step 5: Signature File Carving & Recovery Workspace (3:15 - 4:15)

**Presenter 1**:
> *"Next, let's examine file carving. Our carving engine scans evidence images in 1 MB bounded chunks with 256-byte overlap, ensuring signatures crossing block boundaries are never lost."*

**Technical Driver Action**:
- Navigate to `RecoveryWorkspacePage`.
- Display candidate artifacts recovered from `synthetic_test_disk_01.raw` (`JPEG`, `PNG`, `PDF`, `ZIP`).

**Presenter 1**:
> *"We validate every candidate using format-aware checks—not just file extensions. In our test dataset, a JPEG saved as `.txt` was correctly identified and carved with 100% precision."*

---

### Step 6: 7-Factor Validation Scoring (4:15 - 5:00)

**Presenter 1**:
> *"Recovered files are evaluated using our transparent 7-Factor Confidence Rubric: header signature, footer marker, static parser success, expected length, CRC32 checksum, provenance, and overlap."*

**Technical Driver Action**:
- Click on `CARV-JPEG-001` (High Confidence, Score 100).
- Click on `CARV-JPEG-TRUNC` (Low Confidence, Score 45, Truncated).

**Presenter 1**:
> *"Notice that valid files achieve High Confidence, while truncated files missing footer markers are flagged for Manual Review. We strictly avoid presenting uncalibrated statistical probabilities of truth."*

---

### Step 7: Cryptographic SHA-256 Audit Chain & Tamper Injection Demo (5:00 - 6:00)

**Presenter 1**:
> *"Every single system action is recorded in an append-only cryptographic hash chain where `current_hash = SHA-256(canonical_json + previous_hash)`. Let's run a live chain integrity scan."*

**Technical Driver Action**:
- Navigate to `AuditChainPage`.
- Click **Verify Hash Chain Integrity**.

**Presenter 1**:
> *"The scanner verifies all blocks from Genesis to tip. If an attacker attempts to edit an event field or delete a log entry, our chain scanner immediately flags the exact broken event ID and reports `BROKEN_CHAIN_DETECTED`."*

---

### Step 8: Court-Compliant PDF Report Export & Conclusion (6:00 - 7:00)

**Presenter 1**:
> *"Finally, we generate court-compliant evidence reports."*

**Technical Driver Action**:
- Navigate to `ReportsPage`.
- Click **Generate & Download PDF Report**.
- Open generated PDF report.

**Presenter 1**:
> *"The generated PDF includes case metadata, evidence SHA-256 hashes, recovered file provenance, 5-point classification matrix, limitations disclaimers, and the cryptographic report SHA-256 digest linked into the audit chain.*

> *In summary, ForensicShield brings bulletproof safety gates, read-only evidence integrity, format-aware recovery, and cryptographic audit chains to digital forensics. Thank you, and we welcome your questions!"*
