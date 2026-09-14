"""Pydantic Schemas for Authentication and User Authorization."""

from typing import List, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="AdminPass123!")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    role: str
    permissions: List[str]
    user: Optional["UserProfileResponse"] = None


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    permissions: List[str]
    is_active: bool

    class Config:
        from_attributes = True
