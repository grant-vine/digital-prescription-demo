"""Prescription verification service for W3C VC authenticity checks.

Implements US-010 (Verify Prescription Authenticity).

Provides three-step verification:
1. Signature verification (W3C VC Ed25519)
2. Trust registry check (doctor DID)
3. Revocation status check
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.prescription import Prescription
from app.models.did import DID
from app.services.vc import VCService


# Mock trust registry for MVP (production: real HPCSA/SAPC integration)
TRUSTED_DOCTOR_DIDS = [
    "did:cheqd:testnet:mock-1",  # doctor_user DID from tests
]


class VerificationService:
    """Service for prescription verification.

    Three-step verification:
    1. Verify W3C VC signature is valid
    2. Check doctor DID is in trust registry
    3. Check credential hasn't been revoked
    """

    def __init__(self):
        """Initialize verification service with VCService."""
        self.vc_service = VCService()

    async def verify_prescription(self, prescription_id: int, db: Session) -> Dict[str, Any]:
        """Complete 3-step verification: signature + trust + revocation.

        Args:
            prescription_id: Prescription ID to verify
            db: Database session

        Returns:
            Dict with verification result:
            {
                "verified": true/false,
                "prescription_id": int,
                "credential_id": str,
                "checks": {
                    "signature_valid": true/false,
                    "doctor_trusted": true/false,
                    "not_revoked": true/false
                },
                "issuer_did": str or None,
                "subject_did": str or None,
                "error": str or None,
                "verified_at": "2026-02-11T17:00:00Z"
            }

        Raises:
            ValueError: If prescription not found or is not signed
        """
        prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()

        if not prescription:
            raise ValueError("Prescription not found")

        if not prescription.digital_signature or not prescription.credential_id:
            raise ValueError("Prescription is not signed")

        # Parse W3C VC from digital_signature field
        try:
            credential = json.loads(prescription.digital_signature)
        except (json.JSONDecodeError, TypeError):
            raise ValueError("Invalid credential format")

        # Get DIDs
        doctor_did_record = db.query(DID).filter(DID.user_id == prescription.doctor_id).first()
        patient_did_record = db.query(DID).filter(DID.user_id == prescription.patient_id).first()

        issuer_did = doctor_did_record.did_identifier if doctor_did_record else None
        subject_did = patient_did_record.did_identifier if patient_did_record else None

        # Step 1: Verify signature
        signature_valid = await self.verify_signature(credential)

        # Step 2: Check trust registry
        doctor_trusted = self.is_doctor_trusted(issuer_did) if issuer_did else False

        # Step 3: Check revocation status
        not_revoked = await self.is_credential_revoked(prescription.credential_id)
        not_revoked = not not_revoked  # Invert: is_revoked → not_revoked

        # All checks must pass
        verified = signature_valid and doctor_trusted and not_revoked

        result = {
            "verified": verified,
            "prescription_id": prescription_id,
            "credential_id": prescription.credential_id,
            "checks": {
                "signature_valid": signature_valid,
                "doctor_trusted": doctor_trusted,
                "not_revoked": not_revoked,
            },
            "issuer_did": issuer_did,
            "subject_did": subject_did,
            "verified_at": datetime.utcnow().isoformat() + "Z",
        }

        if not verified:
            # Add error message
            if not signature_valid:
                result["error"] = "Invalid signature"
            elif not doctor_trusted:
                result["error"] = "Doctor DID not trusted"
            elif not not_revoked:
                result["error"] = "Credential has been revoked"

        return result

    async def verify_signature(self, credential: Dict[str, Any]) -> bool:
        """Verify W3C VC signature using VCService.

        Args:
            credential: W3C VC dict with proof section

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            verification_result = await self.vc_service.verify_credential(credential)
            return verification_result.get("valid", False)
        except Exception:
            return False

    def is_doctor_trusted(self, did: Optional[str]) -> bool:
        """Check if doctor DID is in trust registry (mock for MVP).

        Args:
            did: Doctor DID to check

        Returns:
            True if DID is in trust registry, False otherwise
        """
        if not did:
            return False
        return did in TRUSTED_DOCTOR_DIDS

    async def is_credential_revoked(self, credential_id: str) -> bool:
        """Check if credential is revoked (mock for MVP - always False).

        Args:
            credential_id: Credential ID to check

        Returns:
            True if revoked, False if not revoked
        """
        # MVP: Always return False (not revoked)
        # Production: Query ACA-Py revocation registry
        return False
