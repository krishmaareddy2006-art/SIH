# ForensicShield Architecture Overview

ForensicShield is designed using defense-in-depth principles for high-integrity digital forensics and incident response (DFIR).

## Monorepo Layout

- **`backend/`**: Python FastAPI backend service managing cases, analysis pipelines, and audit log generation. Uses SQLAlchemy ORM backed by SQLite (or PostgreSQL in production).
- **`frontend/`**: Modern React single-page application built with TypeScript, Vite, and Tailwind CSS.
- **`tests/`**: Unit, integration, and security guard test suite powered by `pytest`.
- **`test_data/`**: Deterministic forensic evidence generator creating synthetic file systems, duplicates, and corrupted headers for pipeline validation.
- **`native_helpers/`**: Low-level platform utilities (C/Rust stubs) for future safe disk acquisition and memory inspection.
- **`docs/`**: Architectural Decision Records (ADRs) and security policy documentation.

## Core Security Controls

1. **Strict Safe Mode Default (`SAFE_MODE=true`)**:
   Potentially destructive operations (such as drive clearing, evidence wiping, or target modifications) MUST evaluate safe mode status. When enabled, operations perform dry-run simulations and return preview impact reports without modifying target disk state.

2. **Hardware Operation Guard (`REAL_DEVICE_OPERATIONS=false`)**:
   Accessing raw physical devices (`\\.\PhysicalDriveX` or `/dev/sdX`) is disabled by default. Code paths attempting raw device I/O verify this flag and throw security exceptions if set to false.

3. **Structured Audit Trail**:
   Every API invocation generates a JSON log record containing:
   - `request_id`: UUIDv4 context ID trace identifier.
   - `case_id`: Optional associated forensic investigation ID.
   - `user_id`: Authenticated operator identity.
   - `operation`: System action identifier (e.g., `CASE_CREATE`, `HASH_SIMULATION`).
   - `status`: Execution outcome (`SUCCESS`, `SIMULATED`, `ERROR`).
   - `timestamp`: UTC ISO-8601 timestamp with microsecond accuracy.

4. **Information Disclosure Prevention**:
   Global exception middleware intercepts unhandled exceptions, logs internal stack traces to secure backend logs, and responds to clients with sanitized error envelopes.
