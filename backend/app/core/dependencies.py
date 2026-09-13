"""Security Dependencies: Authentication, RBAC, IDOR Guards, and Sensitive Action Validation."""

import logging
from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    ForensicShieldException,
    ResourceNotFoundException,
)
from app.core.logging import audit_log
from app.core.security import decode_access_token
from app.models.auth import User
from app.models.case import ForensicCase, CaseAccess, EvidenceItem


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Extracts and validates JWT Bearer Token from HTTP Authorization Header."""
    request_id = getattr(request.state, "request_id", "N/A")

    if not authorization or not authorization.startswith("Bearer "):
        audit_log(
            message="Unauthenticated request missing Bearer token.",
            operation="AUTHENTICATION",
            status="BLOCKED",
            request_id=request_id,
            level=logging.WARNING,
        )
        raise ForensicShieldException(
            message="Authentication required. Missing Bearer token header.",
            code="UNAUTHENTICATED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub", "")
        if not username:
            raise ValueError("Token sub claim empty.")
    except Exception as exc:
        audit_log(
            message=f"Authentication failed: {str(exc)}",
            operation="AUTHENTICATION",
            status="BLOCKED",
            request_id=request_id,
            level=logging.WARNING,
        )
        raise ForensicShieldException(
            message=f"Invalid or expired token: {str(exc)}",
            code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        audit_log(
            message=f"Authenticated user '{username}' not found or deactivated.",
            operation="AUTHENTICATION",
            status="BLOCKED",
            request_id=request_id,
            level=logging.WARNING,
        )
        raise ForensicShieldException(
            message="User account disabled or not found.",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """Dependency enforcing role-based access control (RBAC)."""

    async def role_checker(request: Request, current_user: User = Depends(get_current_user)) -> User:
        request_id = getattr(request.state, "request_id", "N/A")
        case_id = request.headers.get("X-Case-ID", "N/A")

        if current_user.role.name not in allowed_roles:
            audit_log(
                message=f"Permission denied for user '{current_user.username}' (Role: '{current_user.role.name}'). Required roles: {allowed_roles}",
                operation="PERMISSION_CHECK",
                status="PERMISSION_DENIED",
                request_id=request_id,
                case_id=case_id,
                user_id=current_user.username,
                level=logging.WARNING,
            )
            raise ForensicShieldException(
                message=f"Role '{current_user.role.name}' does not have permission for this action. Required: {allowed_roles}",
                code="PERMISSION_DENIED",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return role_checker


def require_permission(permission_name: str) -> Callable:
    """Dependency enforcing fine-grained permission checks."""

    async def permission_checker(
        request: Request, current_user: User = Depends(get_current_user)
    ) -> User:
        request_id = getattr(request.state, "request_id", "N/A")
        case_id = request.headers.get("X-Case-ID", "N/A")

        user_permissions = [p.name for p in current_user.role.permissions]
        if permission_name not in user_permissions:
            audit_log(
                message=f"Permission denied for user '{current_user.username}'. Missing required permission: '{permission_name}'",
                operation="PERMISSION_CHECK",
                status="PERMISSION_DENIED",
                request_id=request_id,
                case_id=case_id,
                user_id=current_user.username,
                level=logging.WARNING,
            )
            raise ForensicShieldException(
                message=f"Missing required permission: '{permission_name}'",
                code="PERMISSION_DENIED",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return permission_checker


def verify_case_access(
    case_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForensicCase:
    """
    Insecure Direct Object Reference (IDOR) Protection Guard.
    Verifies that requesting user is Administrator, assigned Lead Investigator,
    or explicitly granted case access.
    """
    request_id = getattr(request.state, "request_id", "N/A")

    case = db.query(ForensicCase).filter(ForensicCase.id == case_id).first()
    if not case:
        raise ResourceNotFoundException(f"Forensic Case #{case_id} not found.")

    # 1. Administrator role bypass
    if current_user.role.name == "Administrator":
        return case

    # 2. Assigned Lead Investigator
    if case.investigator_id == current_user.id:
        return case

    # 3. Explicit Case Access Grant
    has_access = (
        db.query(CaseAccess)
        .filter(CaseAccess.case_id == case.id, CaseAccess.user_id == current_user.id)
        .first()
    )
    if has_access:
        return case

    # IDOR Access Denied Audit Log
    audit_log(
        message=f"IDOR Violation: User '{current_user.username}' attempted unauthorized access to Case #{case.case_number}",
        operation="IDOR_CHECK",
        status="IDOR_ACCESS_DENIED",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
        level=logging.WARNING,
    )

    raise ForensicShieldException(
        message="IDOR Protection: Access denied. You do not have permission to view or modify this case.",
        code="IDOR_ACCESS_DENIED",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def verify_evidence_access(
    evidence_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceItem:
    """
    IDOR Protection Guard for Evidence Items.
    Verifies user has access to the parent case containing the evidence item.
    Supports lookup by integer primary key or string evidence_id.
    """
    if str(evidence_id).isdigit():
        evidence = db.query(EvidenceItem).filter((EvidenceItem.id == int(evidence_id)) | (EvidenceItem.evidence_id == str(evidence_id))).first()
    else:
        evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == str(evidence_id)).first()

    if not evidence:
        raise ResourceNotFoundException(f"Evidence Item '{evidence_id}' not found.")

    # Delegate to parent case access verification
    verify_case_access(evidence.case_id, request, current_user, db)
    return evidence

