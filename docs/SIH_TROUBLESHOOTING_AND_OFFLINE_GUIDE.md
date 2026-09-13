# ForensicShield - SIH Troubleshooting & Offline Presentation Guide

> **Purpose**: Emergency procedures, port resolution, database reset, and offline execution instructions for live Smart India Hackathon (SIH) demonstrations.

---

## 1. Fast Launch Options

### Option A: One-Command Python Launcher (Recommended)
```bash
python run_sih_demo.py
```

### Option B: Windows Batch Script
Double-click `start_sih_demo.bat` in the project root directory.

---

## 2. Emergency Troubleshooting Matrix

| Issue / Symptom | Root Cause | Instant Fix Action |
| :--- | :--- | :--- |
| **Port 8000 Already in Use** | Old uvicorn instance running | **Kill process on port 8000**:<br>• Windows: `netstat -ano \| findstr :8000` -> `taskkill /F /PID <pid>`<br>• Linux: `fuser -k 8000/tcp` |
| **Port 5173 Already in Use** | Old Vite dev server running | Vite automatically switches to port `5174`. Open `http://localhost:5174` in browser. |
| **Database Corruption / Missing Tables** | SQLite database schema mismatch | **Full DB Reset**:<br>1. Delete `forensic_shield.db`<br>2. Run `python backend/app/scripts/seed_demo_data.py` |
| **Login Credentials Failed** | Unseeded user accounts | Use default admin account:<br>• Username: `admin`<br>• Password: `adminpassword123` |
| **Synthetic Evidence Disk Missing** | File not generated | Run `python -m tests.qa_framework.synthetic_dataset` to regenerate `synthetic_test_disk_01.raw`. |
| **No Internet Connection at Venue** | Offline presentation lab | ForensicShield is **100% offline-compatible**. It requires zero external API or cloud connectivity. |

---

## 3. Manual Reset Procedure

If the system enters an unexpected state during live judging preparation, run this 3-step reset sequence:

```bash
# 1. Terminate running Python / Node processes
taskkill /F /IM python.exe /T
taskkill /F /IM node.exe /T

# 2. Reset Database & Re-seed
rm forensic_shield.db
python backend/app/scripts/seed_demo_data.py

# 3. Relaunch Application
python run_sih_demo.py
```

---

## 4. Offline Fallback Verification

ForensicShield operates completely offline:
- **Database**: Embedded SQLite (`forensic_shield.db`).
- **Frontend Assets**: Bundled locally via React 18 + Vite (`npm run build` generates self-contained `frontend/dist/`).
- **PDF Reports**: Generated locally using ReportLab 5.0.1 without external network font downloads.
- **Blockchain Notarization**: Uses `MockLedgerAdapter` for offline ledger simulation when `ENABLE_BLOCKCHAIN_NOTARIZATION=false`.

---

## 5. Live Presentation Failure Demo Checklist

When demonstrating the **System Disk Safety Gate Block** to judges:
1. Open `DriveSanitizationPage` (`http://localhost:5173/sanitization`).
2. Select target device: `C:\Windows` (Windows host) or `/dev/sda` (Linux host).
3. Click **Evaluate Safety Gates**.
4. Point out the prominent red **Safety Gate Blocked Banner** displaying HTTP 403 Forbidden rejection and reason: `Check 2/4 Failed: Target storage device contains active OS boot/root filesystem`.
