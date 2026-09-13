# ForensicShield Security Architecture & Decisions

## Security Philosophy

Digital forensics tools operate in high-trust, high-consequence environments where accidental data destruction or tampered evidence invalidates legal chain-of-custody. ForensicShield enforces strict default guards to eliminate human error and unintended execution.

## Key Security Architecture Decisions

### 1. Default Safe Mode (`SAFE_MODE=true`)
- **Rationale**: Accidental triggers of disk wiping or file modification can cause unrecoverable evidence loss.
- **Enforcement**: Middleware and function decorators inspect `settings.SAFE_MODE`. Destructive routes are blocked from raw write loops and instead generate dry-run diffs.

### 2. Physical Hardware Feature Flag (`REAL_DEVICE_OPERATIONS=false`)
- **Rationale**: Low-level device operations must require explicit opt-in confirmation in production environments.
- **Enforcement**: Hardware abstraction layers raise `PermissionError` when flags are set to false.

### 3. Zero Hardcoded Secrets & Pydantic Validation
- **Rationale**: Hardcoded credentials and lax environment parsing present serious security vulnerabilities.
- **Enforcement**: Environment variables are strictly validated through Pydantic `BaseSettings`. Failure to supply valid configurations blocks server boot. `.env.example` serves as the schema template.

### 4. Immutable JSON Audit Logging & Context Tracing
- **Rationale**: Forensic tools must maintain internal accountability.
- **Enforcement**: Custom middleware injects a unique `X-Request-ID` into every HTTP transaction. All application logs emit structured JSON objects with timestamping, user context, case identifiers, and operation tags.

### 5. API Versioning (`/api/v1`)
- **Rationale**: Forensics pipelines require stable APIs to prevent client-side misinterpretation of evidence schemas during platform upgrades.
- **Enforcement**: Router prefixing under `/api/v1`.

### 6. Sanitized Global Error Handling
- **Rationale**: Raw exception tracebacks leak directory structures, database schemas, library versions, and system environment variables to attackers.
- **Enforcement**: Custom global exception handlers format standard JSON payloads containing only correlation `request_id` and safe error codes.
