"""Prescription verification endpoint (US-010).

GET /api/v1/prescriptions/{id}/verify - Verify prescription authenticity

RBAC: All authenticated users can verify prescriptions
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, get_db
from app.models.user import User
from app.services.verification import VerificationService

router = APIRouter()


class VerificationChecks(BaseModel):
    """Three-step verification checks."""

    signature_valid: bool
    doctor_trusted: bool
    not_revoked: bool


class VerificationResponse(BaseModel):
    """Prescription verification result response."""

    verified: bool
    prescription_id: int
    credential_id: str
    checks: VerificationChecks
    issuer_did: Optional[str] = None
    subject_did: Optional[str] = None
    error: Optional[str] = None
    verified_at: str

    class Config:
        from_attributes = True


@router.get(
    "/api/v1/prescriptions/{id}/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_prescription(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify prescription authenticity (US-010).

    Three-step verification:
    1. Signature verification (W3C VC Ed25519)
    2. Trust registry check (doctor DID)
    3. Revocation status check

    RBAC: All authenticated users (doctor, patient, pharmacist) can verify.

    Args:
        id: Prescription ID
        current_user: Authenticated user
        db: Database session

    Returns:
        VerificationResponse with detailed verification result

    Raises:
        HTTPException 404: Prescription not found
        HTTPException 400: Prescription is not signed yet
        HTTPException 500: Verification error
    """
    verification_service = VerificationService()

    try:
        result = await verification_service.verify_prescription(id, db)
        return VerificationResponse(**result)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        elif "not signed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription is not signed yet",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Verification error: {error_msg}",
            )
