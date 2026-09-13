# ForensicShield - Neon Serverless PostgreSQL Integration Guide

> **Purpose**: Step-by-step instructions for connecting ForensicShield to **Neon Serverless PostgreSQL** database.

---

## 1. Overview & Architectural Features

ForensicShield supports both local SQLite (for offline development) and **Neon Serverless PostgreSQL** (for cloud deployments and production hackathon hosting).

### Built-in Neon Optimizations:
1. **Automatic URL Prefix Normalization**: Converts `postgres://` to `postgresql://` automatically for SQLAlchemy dialect compatibility.
2. **Serverless Connection Health Ping (`pool_pre_ping=True`)**: Neon compute endpoints auto-suspend when idle. `pool_pre_ping=True` tests connections before executing queries, preventing `psycopg2.OperationalError` when Neon wakes up.
3. **Connection Recycling (`pool_recycle=300`)**: Stale connections are recycled every 5 minutes.

---

## 2. Quick Setup Instructions

### Step 1: Install PostgreSQL Driver
Install `psycopg2-binary` in your Python environment:
```bash
pip install psycopg2-binary
```
*(Or install all requirements via `pip install -r backend/requirements.txt`)*

---

### Step 2: Obtain your Neon Database Connection String

1. Log into your [Neon Console](https://console.neon.tech).
2. Create or select your project (e.g. `forensic-shield-db`).
3. Under **Connection Details**, copy your **PostgreSQL Connection String**. It will look like:
   ```
   postgres://alex:AbC123dEf@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

---

### Step 3: Configure `.env` File

Create or edit your `.env` file in the root directory (or inside `backend/.env`) and set `DATABASE_URL`:

```env
# Neon Serverless PostgreSQL Database Connection
DATABASE_URL=postgresql://alex:AbC123dEf@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

# Application Settings
SAFE_MODE=true
REAL_DEVICE_OPERATIONS=false
SECRET_KEY=change-this-to-a-secure-random-32-byte-key
```

---

### Step 4: Initialize & Seed Database Schema

Run the automated seed script to create database tables (`forensic_cases`, `evidence_items`, `carved_file_artifacts`, `audit_events`, `job_records`) and seed default admin accounts and SIH demo data:

```bash
python backend/app/scripts/seed_demo_data.py
```

Expected output:
```
[SIH Seed] Initializing database tables...
[SIH Seed] Core roles and users initialized.
[SIH Seed] Synthetic Image SHA-256: effcb0dbb243905b... (10.0 MB)
[SIH Seed] Demo case 'CAS-SIH-2026-001' created (ID #1).
[SIH Seed] 5 Carved file artifacts seeded.
[SIH Seed] Cryptographic audit chain seeded (9 total blocks).
==========================================================
  SIH DEMO SEED DATA SUCCESSFULLY INITIALIZED
==========================================================
```

---

### Step 5: Launch Application

Launch backend and frontend services:
```bash
python run_sih_demo.py
```

---

## 3. Verification & Troubleshooting

### Verify Database Connection via Pytest:
Run the unit test suite to verify ORM models, audit chain, and job management operations on your active database:
```bash
python -m pytest tests/test_qa_safety_and_tampering.py tests/test_qa_fuzzing_and_resilience.py -v -W ignore
```

### Common Issues:

1. **`ModuleNotFoundError: No module named 'psycopg2'`**:
   - Solution: Run `pip install psycopg2-binary`.
2. **`NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres`**:
   - Solution: Change `postgres://` to `postgresql://` in your `DATABASE_URL` string (ForensicShield handles this automatically in `config.py` and `database.py`).
3. **`psycopg2.OperationalError: SSL error: certificate verify failed`**:
   - Solution: Ensure `?sslmode=require` is appended at the end of your Neon `DATABASE_URL`.
