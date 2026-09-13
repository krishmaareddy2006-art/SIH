"""Recovery Validation & Confidence-Scoring REST API Endpoints for ForensicShield."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.auth import User
from app.schemas.validation import ValidationRequest, ValidationReport
from app.services.recovery_validation import RecoveryValidationService

router = APIRouter()
validation_service = RecoveryValidationService()


@router.post("/validate-file", response_model=ValidationReport, status_code=status.HTTP_200_OK)
def validate_recovered_artifact_file(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validates a recovered or carved evidence file artifact on disk:
    - Runs safe static format parser (JPEG, PNG, PDF, ZIP, GENERIC).
    - Checks magic bytes, footers, structure, and chunk CRCs without executing binaries or scripts.
    - Calculates transparent 7-factor scoring rubric (0-100).
    - Assigns confidence label (HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, UNRELIABLE_CORRUPTED).
    - Identifies security warnings (active scripts, embedded binaries) and manual review recommendations.
    """
    return validation_service.validate_file(request)
