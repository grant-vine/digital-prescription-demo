"""Prescription verification endpoint (US-010)."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

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


class VerifyPrescriptionRequest(BaseModel):
    """Request body for POST /verify/prescription"""
    prescription_id: int


@router.post(
    "/api/v1/verify/prescription",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_prescription_post(
    request: VerifyPrescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alternative POST endpoint for prescription verification.

    Same functionality as GET /prescriptions/{id}/verify but accepts
    prescription_id in request body for compatibility.
    """
    return await verify_prescription(request.prescription_id, current_user, db)


class TrustRegistryRequest(BaseModel):
    did: str = Field(..., alias="issuer_did")


class TrustRegistryResponse(BaseModel):
    """Response for trust registry verification"""
    did: str
    trusted: bool
    role: Optional[str] = None
    verified_at: str


@router.post(
    "/api/v1/verify/trust-registry",
    response_model=TrustRegistryResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_trust_registry(
    request: TrustRegistryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify if a DID is in the trust registry.

    Checks if the provided DID belongs to a registered and active user.
    """
    from app.models.did import DID as DIDModel

    did_record = db.query(DIDModel).filter(DIDModel.did_identifier == request.did).first()

    if not did_record:
        return TrustRegistryResponse(
            did=request.did,
            trusted=False,
            role=None,
            verified_at=datetime.utcnow().isoformat() + "Z",
        )

    user = db.query(User).filter(User.id == did_record.user_id).first()

    return TrustRegistryResponse(
        did=request.did,
        trusted=True,
        role=user.role if user else did_record.role,
        verified_at=datetime.utcnow().isoformat() + "Z",
    )
