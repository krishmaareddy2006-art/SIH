"""Authentication API Endpoints: Login, Logout, Profile Inspection."""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForensicShieldException
from app.core.logging import audit_log
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.auth import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse

router = APIRouter()

TOKEN_EXPIRE_MINUTES = 480  # 8 hours expiration


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticates user credentials and generates a signed JWT Access Token."""
    request_id = getattr(request.state, "request_id", "N/A")

    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        audit_log(
            message=f"Failed login attempt for username '{login_data.username}'.",
            operation="LOGIN",
            status="LOGIN_FAILED",
            request_id=request_id,
            user_id=login_data.username,
            level=logging.WARNING,
        )
        raise ForensicShieldException(
            message="Invalid username or password.",
            code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        audit_log(
            message=f"Login attempt for deactivated user '{user.username}'.",
            operation="LOGIN",
            status="LOGIN_FAILED",
            request_id=request_id,
            user_id=user.username,
            level=logging.WARNING,
        )
        raise ForensicShieldException(
            message="User account is deactivated.",
            code="USER_DEACTIVATED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    permissions = [p.name for p in user.role.permissions]

    token_expires = timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username,
        extra_data={"role": user.role.name, "user_id": user.id},
        expires_delta=token_expires,
    )

    audit_log(
        message=f"User '{user.username}' (Role: '{user.role.name}') logged in successfully.",
        operation="LOGIN",
        status="LOGIN_SUCCESS",
        request_id=request_id,
        user_id=user.username,
    )

    user_profile = UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        permissions=permissions,
        is_active=user.is_active,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(token_expires.total_seconds()),
        username=user.username,
        role=user.role.name,
        permissions=permissions,
        user=user_profile,
    )


@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    """Logs out user session and records audit trail event."""
    request_id = getattr(request.state, "request_id", "N/A")

    audit_log(
        message=f"User '{current_user.username}' logged out.",
        operation="LOGOUT",
        status="SUCCESS",
        request_id=request_id,
        user_id=current_user.username,
    )

    return {"message": "Logged out successfully. Token session terminated."}


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns currently authenticated user profile and active permission scopes."""
    permissions = [p.name for p in current_user.role.permissions]

    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.name,
        permissions=permissions,
        is_active=current_user.is_active,
    )
