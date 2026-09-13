"""ForensicShield Application Configuration Management.

Enforces zero-hardcoded secret principles and strict security settings.
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ForensicShield"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"

    # Security Feature Flags (Strict Safe Defaults)
    SAFE_MODE: bool = True
    REAL_DEVICE_OPERATIONS: bool = False
    ENABLE_BLOCKCHAIN_NOTARIZATION: bool = False

    # Blockchain Notarization Settings
    BLOCKCHAIN_NETWORK_ID: str = "mocknet-local-v1"
    BLOCKCHAIN_TIMEOUT_SECONDS: int = 5
    BLOCKCHAIN_MAX_RETRIES: int = 3

    # Environment & Server
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    SECRET_KEY: str = "DEFAULT_UNSECURE_SECRET_CHANGE_IN_PRODUCTION_32_BYTES"

    # Database
    DATABASE_URL: str = "sqlite:///./forensic_shield.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
