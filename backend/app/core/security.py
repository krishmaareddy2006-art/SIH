"""Security, Cryptography, Password Hashing, and JWT Token Management for ForensicShield."""

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.exceptions import (
    SafeModeViolationException,
    RealDeviceOperationBlockedException,
)


# ==========================================
# 1. Cryptographic Password Hashing (PBKDF2-SHA256)
# ==========================================

PBKDF2_ITERATIONS = 100000


def hash_password(password: str) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    salt_hex = salt.hex()
    hash_hex = hash_bytes.hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a PBKDF2-HMAC-SHA256 hash string."""
    try:
        algorithm, iterations_str, salt_hex, expected_hash_hex = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        computed_bytes = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(computed_bytes.hex(), expected_hash_hex)
    except Exception:
        return False


# ==========================================
# 2. JWT Token Generation & Verification (RFC 7519)
# ==========================================

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data_str: str) -> bytes:
    padding = "=" * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode((data_str + padding).encode("utf-8"))


def create_access_token(
    subject: str,
    extra_data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates an HMAC-SHA256 signed JWT Access Token with expiration timestamp."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    header_b64 = _base64url_encode(header_json)

    now = int(time.time())
    expire = now + int(
        expires_delta.total_seconds()
        if expires_delta
        else timedelta(hours=8).total_seconds()
    )

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra_data:
        payload.update(extra_data)

    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _base64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and verifies an HMAC-SHA256 signed JWT token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format.")

    header_b64, payload_b64, signature_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    actual_sig = _base64url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("JWT token signature validation failed.")

    payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))

    # Verify Token Expiration
    now = int(time.time())
    if payload.get("exp") and now > payload["exp"]:
        raise ValueError("JWT access token has expired.")

    return payload


# ==========================================
# 3. Safe Mode & Real Device Guards
# ==========================================

def verify_real_device_allowed() -> None:
    """Verifies whether real physical device operations are enabled in environment configuration."""
    if not settings.REAL_DEVICE_OPERATIONS:
        raise RealDeviceOperationBlockedException(
            "Hardware operation blocked: REAL_DEVICE_OPERATIONS environment flag is disabled."
        )


def verify_destructive_allowed(simulate: bool = True) -> None:
    """Dependency check for destructive endpoint routes."""
    if settings.SAFE_MODE and not simulate:
        raise SafeModeViolationException(
            "Destructive operation rejected by SAFE_MODE policy. Enable simulate=true to preview actions."
        )
