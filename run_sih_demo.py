"""One-Command Demonstration Launcher for ForensicShield SIH Demo.

Configures demo environment:
1. Forces SAFE_MODE=true and REAL_DEVICE_OPERATIONS=false (0% accidental wiping risk).
2. Executes backend database seeding (app/scripts/seed_demo_data.py).
3. Verifies backend FastAPI server (:8000) and frontend Vite server (:5173).
4. Prints live demo credentials, quick start steps, and failure scenario commands.
"""

import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

# Force Demonstration Safety Environment Variables
os.environ["SAFE_MODE"] = "true"
os.environ["REAL_DEVICE_OPERATIONS"] = "false"
os.environ["ENABLE_BLOCKCHAIN_NOTARIZATION"] = "false"

project_root = Path(__file__).resolve().parent


def is_server_running(url: str) -> bool:
    """Checks if a local HTTP endpoint is responding."""
    try:
        req = urllib.request.urlopen(url, timeout=1.5)
        return req.status == 200
    except Exception:
        return False


def main():
    print("\n" + "=" * 64)
    print("   FORENSICSHIELD - SMART INDIA HACKATHON DEMO LAUNCHER")
    print("=" * 64)
    print(" [Safety Guard] SAFE_MODE = TRUE")
    print(" [Safety Guard] REAL_DEVICE_OPERATIONS = FALSE (Simulated Wiping)")
    print("=" * 64 + "\n")

    # 1. Execute Seed Script
    print("[1/3] Initializing DB & Seeding SIH Demonstration Case...")
    seed_script = project_root / "backend" / "app" / "scripts" / "seed_demo_data.py"
    res = subprocess.run([sys.executable, str(seed_script)], cwd=project_root)
    if res.returncode != 0:
        print("[Launcher Error] DB Seeding failed. Check python environment.")
        sys.exit(1)

    # 2. Check Backend Server
    backend_url = "http://127.0.0.1:8000/api/v1/health"
    print("\n[2/3] Checking FastAPI Backend Server (:8000)...")
    if is_server_running(backend_url):
        print(" -> FastAPI Backend is ALREADY RUNNING on http://127.0.0.1:8000")
    else:
        print(" -> Starting FastAPI Backend server in background process...")
        backend_dir = project_root / "backend"
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=backend_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
        time.sleep(2.5)

    # 3. Check Frontend Server
    frontend_url = "http://localhost:5173"
    print("\n[3/3] Checking React Vite Frontend Server (:5173)...")
    if is_server_running(frontend_url):
        print(" -> Vite Frontend is ALREADY RUNNING on http://localhost:5173")
    else:
        print(" -> Launching Vite Frontend server...")
        frontend_dir = project_root / "frontend"
        subprocess.Popen(
            ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"],
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
        time.sleep(2)

    # Display Demo Portal Summary
    print("\n" + "=" * 64)
    print("    FORENSICSHIELD DEMONSTRATION ENVIRONMENT READY!")
    print("=" * 64)
    print("  Application Portal:  http://localhost:5173")
    print("  Backend OpenAPI Docs:http://127.0.0.1:8000/docs")
    print("------------------------------------------------------------")
    print("  DEMO CREDENTIALS:")
    print("   • Administrator: username='admin'            password='adminpassword123'")
    print("   • Operator:      username='operator_san'     password='operatorpassword123'")
    print("   • Investigator:  username='investigator_lead' password='investigatorpassword123'")
    print("   • Analyst:       username='analyst_qa'        password='analystpassword123'")
    print("------------------------------------------------------------")
    print("  KEY DEMO WORKFLOWS:")
    print("   1. Case Workspace:   CAS-SIH-2026-001 (Pre-seeded)")
    print("   2. Evidence Intake:  EVD-SIH-DISK-01 (10 MB Synthetic Disk Image)")
    print("   3. Safety Gate Demo: Attempt sanitization on 'C:\\Windows' or '/dev/sda'")
    print("                        -> Instantly BLOCKED by 8-Point Gate")
    print("   4. Carving & Val:   Inspect 5 carved artifacts & validation scores")
    print("   5. Audit Ledger:     Verify intact SHA-256 chain & test tampering")
    print("   6. Report Export:    Download Court-Compliant PDF & JSON manifest")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
