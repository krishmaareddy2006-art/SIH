# ForensicShield Threat Model & Security Controls Architecture

This document presents the formal threat model, attack vectors, security controls, and design rationale for ForensicShield.

---

## Threat Matrix & Security Controls

| Threat Identifier | Threat Category & Scenario | Risk Impact | Implemented Mitigation Control | Design Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **TM-01** | **Password Compromise & Credential Theft**<br>Attacker attempts brute-force or dictionary attacks against user passwords. | CRITICAL | **Cryptographic Password Hashing (PBKDF2-HMAC-SHA256)**<br>Passwords hashed using PBKDF2 with 100,000 iterations and 16-byte random salts. Plaintext passwords are never logged or stored. | Prevents hash cracking via rainbow tables or offline database leak exploitation. |
| **TM-02** | **Vertical Privilege Escalation**<br>Low-privileged user (e.g. Viewer or Operator) attempts to execute administrative actions (e.g. creating cases or wiping partitions). | HIGH | **Server-Side RBAC Enforcement (`require_roles` / `require_permission`)**<br>Role checks are strictly enforced in FastAPI dependencies on every endpoint. Frontend permission checks are treated as untrusted. | Ensures clients cannot bypass UI restrictions by sending handcrafted HTTP requests directly to API endpoints. |
| **TM-03** | **Insecure Direct Object Reference (IDOR)**<br>User authorized for Case A attempts to access or modify Case B or Evidence B by guessing numeric IDs in request URLs (`GET /api/v1/cases/2`). | HIGH | **Contextual Ownership & Access Verification (`verify_case_access` / `verify_evidence_access`)**<br>Every request verifies that `current_user` is an Administrator, assigned Lead Investigator, or explicitly granted access in `CaseAccess`. | Prevents unauthorized cross-case data access or evidence tampering between investigators. |
| **TM-04** | **Accidental Storage Mutation / Evidence Wiping**<br>Operator accidentally triggers a destructive disk sanitization or recovery routine on active evidence. | CRITICAL | **Default Safe Mode (`SAFE_MODE=true`) & Sensitive Action Confirmation Guard**<br>1. Safe Mode forces dry-run previews.<br>2. Requests require four mandatory payload fields: `case_id`, `reason` (>=5 chars), `target_identifier`, and `explicit_confirmation == "CONFIRM_SENSITIVE_ACTION"`. | Prevents human error and automated script mistakes from destroying evidence or chain-of-custody. |
| **TM-05** | **Audit Trail Evasion & Accountability Denial**<br>Attacker executes actions without leaving evidence in system logs. | HIGH | **Structured JSON Audit Trail (`audit_log`)**<br>Emits JSON audit frames for `LOGIN_SUCCESS`, `LOGIN_FAILED`, `PERMISSION_DENIED`, `IDOR_ACCESS_DENIED`, `CASE_CREATE`, `CASE_CLOSE`, and `SENSITIVE_ACTION_EXECUTE` containing `request_id`, `case_id`, `user_id`, and `timestamp`. | Provides forensic chain-of-custody and non-repudiation during incident investigations. |
| **TM-06** | **Session Hijacking & Token Manipulation**<br>Attacker intercepts or tampers with user session tokens. | HIGH | **HMAC-SHA256 Signed JWT Tokens with TTL Expiration**<br>Access tokens contain signed claims (`sub`, `role`, `exp`, `iat`) validated against server `SECRET_KEY`. Expired tokens are rejected with HTTP 401. | Ensures session integrity and limits vulnerability window if a token is leaked. |
| **TM-07** | **Information Disclosure via Unhandled Tracebacks**<br>Server crash leaks internal file paths, database schemas, or secret environment variables to API clients. | MEDIUM | **Global Error Handler & Response Sanitization**<br>Catches internal exceptions, logs detailed tracebacks to secure internal logs, and returns a sanitized JSON error payload containing only correlation `request_id` and safe error codes. | Prevents reconnaissance attackers from mapping internal platform architecture. |

---

## Role Permission Matrix

| Role | `case:create` | `case:read` | `case:close` | `evidence:create` | `evidence:read` | `job:sanitization` | `job:recovery` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Administrator** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Investigator** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Operator** | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Viewer** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
