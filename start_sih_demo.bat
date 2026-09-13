@echo off
TITLE ForensicShield - SIH 2026 Demonstration Launcher
CLS
ECHO ============================================================
ECHO   FORENSICSHIELD - SMART INDIA HACKATHON DEMO LAUNCHER
ECHO ============================================================
ECHO   Enforcing SAFE_MODE=true and REAL_DEVICE_OPERATIONS=false
ECHO ============================================================
ECHO.

SET SAFE_MODE=true
SET REAL_DEVICE_OPERATIONS=false
SET ENABLE_BLOCKCHAIN_NOTARIZATION=false

py run_sih_demo.py

PAUSE
