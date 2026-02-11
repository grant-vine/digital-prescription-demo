"""Prescription signing and verification endpoints.

Implements US-003 (Sign Prescription) and US-010 (Verify Prescription):
- POST /api/v1/prescriptions/{id}/sign - Sign prescription as W3C VC
- GET /api/v1/prescriptions/{id}/verify - Verify signature validity

RBAC:
- Sign: Doctor only (prescribing doctor)
- Verify: All authenticated users
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.models.did import DID
from app.services.vc import VCService

router = APIRouter()


class SignatureResponse(BaseModel):
    prescription_id: int
    credential_id: str
    signed: bool
    signed_at: str
    signature: str
    issuer_did: str
    subject_did: str


class VerificationResponse(BaseModel):
    valid: bool
    issuer_did: Optional[str] = None
    signed_at: Optional[str] = None
    signature_algorithm: Optional[str] = None
    credential_id: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/api/v1/prescriptions/{id}/sign",
    response_model=SignatureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sign_prescription(
    id: int,
    current_user: User = Depends(require_role(["doctor"])),
    db: Session = Depends(get_db),
):
    """Sign prescription with doctor's digital signature.

    Creates W3C Verifiable Credential with Ed25519 signature.
    Only prescribing doctor can sign their own prescription.

    RBAC: Doctor only (must be prescribing doctor)

    Error codes:
        404: Prescription not found
        403: User is not prescribing doctor or not doctor role
        409: Prescription already signed
        400: Doctor or patient DID not found
    """
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    if prescription.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Only prescribing doctor can sign prescription",
        )

    if prescription.digital_signature:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prescription already signed",
        )

    doctor_did_record = db.query(DID).filter(DID.user_id == current_user.id).first()
    if not doctor_did_record:
        from app.services.acapy import ACAPyService

        acapy_service = ACAPyService()
        try:
            wallet_result = await acapy_service.create_wallet()
            if "error" not in wallet_result and wallet_result.get("did"):
                doctor_did_record = DID(
                    user_id=current_user.id,
                    did_identifier=wallet_result["did"],
                    role=str(current_user.role),
                )
                db.add(doctor_did_record)
                db.commit()
                db.refresh(doctor_did_record)
        finally:
            await acapy_service.close()

        if not doctor_did_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor DID not found - create DID first",
            )

    patient_did_record = db.query(DID).filter(DID.user_id == prescription.patient_id).first()
    if not patient_did_record:
        from app.services.acapy import ACAPyService

        acapy_service = ACAPyService()
        try:
            wallet_result = await acapy_service.create_wallet()
            if "error" not in wallet_result and wallet_result.get("did"):
                patient_did_record = DID(
                    user_id=prescription.patient_id,
                    did_identifier=wallet_result["did"],
                    role="patient",
                )
                db.add(patient_did_record)
                db.commit()
                db.refresh(patient_did_record)
        finally:
            await acapy_service.close()

        if not patient_did_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient DID not found - patient must create DID first",
            )

    doctor_did = doctor_did_record.did_identifier
    patient_did = patient_did_record.did_identifier

    vc_service = VCService()
    try:
        credential = vc_service.create_credential(
            prescription=prescription,
            doctor_did=doctor_did,
            patient_did=patient_did,
        )

        signed_result = await vc_service.sign_credential(
            credential=credential,
            doctor_did=doctor_did,
        )

        signed_credential = signed_result["credential"]
        credential_id = signed_result["credential_id"]
        signature = signed_result["signature"]

        prescription.digital_signature = signature
        prescription.credential_id = credential_id
        prescription.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(prescription)

        signed_at = signed_credential.get("proof", {}).get(
            "created", datetime.utcnow().isoformat() + "Z"
        )

        return SignatureResponse(
            prescription_id=prescription.id,
            credential_id=credential_id,
            signed=True,
            signed_at=signed_at,
            signature=signature,
            issuer_did=doctor_did,
            subject_did=patient_did,
        )

    finally:
        await vc_service.close()


@router.get(
    "/api/v1/prescriptions/{id}/verify",
    response_model=VerificationResponse,
)
async def verify_prescription(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify prescription signature validity.

    Verifies W3C Verifiable Credential cryptographic signature.
    All authenticated users can verify prescriptions.

    RBAC: All authenticated users (doctor, patient, pharmacist)

    Error codes:
        404: Prescription not found
        400: Prescription not signed
    """
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    if not prescription.digital_signature or not prescription.credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prescription not signed",
        )

    doctor_did_record = db.query(DID).filter(DID.user_id == prescription.doctor_id).first()
    patient_did_record = db.query(DID).filter(DID.user_id == prescription.patient_id).first()

    if not doctor_did_record or not patient_did_record:
        return VerificationResponse(
            valid=False,
            error="Issuer or subject DID not found",
        )

    doctor_did = doctor_did_record.did_identifier
    patient_did = patient_did_record.did_identifier

    vc_service = VCService()
    try:
        credential = vc_service.create_credential(
            prescription=prescription,
            doctor_did=doctor_did,
            patient_did=patient_did,
        )

        proof = {
            "type": "Ed25519Signature2020",
            "created": prescription.updated_at.isoformat() + "Z",
            "proofPurpose": "assertionMethod",
            "verificationMethod": f"{doctor_did}#key-1",
            "proofValue": prescription.digital_signature,
        }
        credential["proof"] = proof

        verification_result = await vc_service.verify_credential(credential)

        if not verification_result.get("valid", False):
            return VerificationResponse(
                valid=False,
                error=verification_result.get("error", "Signature verification failed"),
            )

        return VerificationResponse(
            valid=True,
            issuer_did=doctor_did,
            signed_at=proof["created"],
            signature_algorithm="Ed25519Signature2020",
            credential_id=prescription.credential_id,
        )

    finally:
        await vc_service.close()
