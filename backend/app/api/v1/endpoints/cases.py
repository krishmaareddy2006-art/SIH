"""Forensic Case Management API Endpoints with IDOR Protection and Audit Logging."""

from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import audit_log
from app.core.dependencies import (
    get_current_user,
    require_roles,
    verify_case_access,
)
from app.models.auth import User
from app.models.case import ForensicCase, CaseAccess
from app.schemas.forensic import CaseCreate, CaseResponse
from app.schemas.evidence import CaseAccessGrantRequest

router = APIRouter()


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    request: Request,
    current_user: User = Depends(require_roles(["Administrator", "Investigator"])),
    db: Session = Depends(get_db),
):
    """Creates a new forensic investigation case context. (Admin / Investigator only)."""
    request_id = getattr(request.state, "request_id", "N/A")

    db_case = ForensicCase(
        case_number=case_in.case_number,
        title=case_in.title,
        description=case_in.description,
        investigator_id=current_user.id,
        status="OPEN",
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # Automatically grant case access to creator
    access = CaseAccess(case_id=db_case.id, user_id=current_user.id, granted_by_id=current_user.id)
    db.add(access)
    db.commit()

    audit_log(
        message=f"Forensic case #{db_case.case_number} ('{db_case.title}') created by '{current_user.username}'.",
        operation="CASE_CREATE",
        status="SUCCESS",
        request_id=request_id,
        case_id=db_case.case_number,
        user_id=current_user.username,
    )

    return db_case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists forensic cases accessible to the current user (IDOR Filtered)."""
    request_id = getattr(request.state, "request_id", "N/A")

    if current_user.role.name == "Administrator":
        cases = db.query(ForensicCase).all()
    else:
        # Fetch cases where user is lead investigator OR has explicit access grant
        granted_case_ids = (
            db.query(CaseAccess.case_id).filter(CaseAccess.user_id == current_user.id).subquery()
        )
        cases = (
            db.query(ForensicCase)
            .filter(
                (ForensicCase.investigator_id == current_user.id)
                | (ForensicCase.id.in_(granted_case_ids))
            )
            .all()
        )

    audit_log(
        message=f"User '{current_user.username}' retrieved {len(cases)} accessible cases.",
        operation="CASE_LIST",
        status="SUCCESS",
        request_id=request_id,
        user_id=current_user.username,
    )

    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_by_id(
    case: ForensicCase = Depends(verify_case_access),
):
    """Gets details for a specific case. (IDOR Protected)."""
    return case


@router.post("/{case_id}/close", response_model=CaseResponse)
async def close_case(
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator"])),
    db: Session = Depends(get_db),
):
    """Closes an active forensic case context and emits audit event. (Admin / Investigator only)."""
    request_id = getattr(request.state, "request_id", "N/A")

    case.status = "CLOSED"
    db.commit()
    db.refresh(case)

    audit_log(
        message=f"Forensic case #{case.case_number} closed by '{current_user.username}'.",
        operation="CASE_CLOSE",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return case


@router.post("/{case_id}/grant-access")
async def grant_case_access(
    grant_req: CaseAccessGrantRequest,
    request: Request,
    case: ForensicCase = Depends(verify_case_access),
    current_user: User = Depends(require_roles(["Administrator", "Investigator"])),
    db: Session = Depends(get_db),
):
    """Grants explicit case access permission to another user."""
    request_id = getattr(request.state, "request_id", "N/A")

    target_user = db.query(User).filter(User.id == grant_req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    existing = (
        db.query(CaseAccess)
        .filter(CaseAccess.case_id == case.id, CaseAccess.user_id == target_user.id)
        .first()
    )
    if not existing:
        access = CaseAccess(case_id=case.id, user_id=target_user.id, granted_by_id=current_user.id)
        db.add(access)
        db.commit()

    audit_log(
        message=f"Case #{case.case_number} access granted to '{target_user.username}' by '{current_user.username}'.",
        operation="GRANT_ACCESS",
        status="SUCCESS",
        request_id=request_id,
        case_id=case.case_number,
        user_id=current_user.username,
    )

    return {"message": f"Access to Case #{case.case_number} granted to {target_user.username}."}
