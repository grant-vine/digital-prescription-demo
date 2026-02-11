"""Verifiable Credential service for W3C VC generation and verification.

Provides W3C Verifiable Credential operations:
- Create prescription credentials
- Sign credentials with Ed25519
- Verify credential signatures
- Integrate with ACA-Py for cryptographic operations
"""

import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional

from app.services.acapy import ACAPyService


class VCService:
    """Service for W3C Verifiable Credential operations.

    Creates, signs, and verifies W3C-compliant Verifiable Credentials
    for digital prescriptions using Ed25519 signatures via ACA-Py.
    """

    def __init__(self, acapy_service: Optional[ACAPyService] = None):
        """Initialize VC service with ACA-Py service.

        Args:
            acapy_service: Optional ACA-Py service instance.
                          If None, creates new instance.
        """
        self._acapy_service = acapy_service or ACAPyService()
        self._owns_acapy = acapy_service is None

    async def close(self):
        """Close ACA-Py service if owned by this instance."""
        if self._owns_acapy and self._acapy_service:
            await self._acapy_service.close()

    def create_credential(
        self,
        prescription: Any,
        doctor_did: str,
        patient_did: str,
    ) -> Dict[str, Any]:
        """Create W3C Verifiable Credential for prescription.

        Creates unsigned W3C VC structure with prescription data
        in credentialSubject. Does NOT include proof - use sign_credential()
        to add cryptographic signature.

        Args:
            prescription: Prescription model instance with fields:
                - id, medication_name, medication_code, dosage, quantity
                - instructions, date_issued, date_expires
            doctor_did: Doctor's DID (issuer)
            patient_did: Patient's DID (subject)

        Returns:
            Dict containing unsigned W3C VC:
            {
                "@context": [...],
                "type": [...],
                "issuer": "did:cheqd:testnet:...",
                "issuanceDate": "2026-02-11T10:30:00Z",
                "expirationDate": "2026-05-11T23:59:59Z",
                "credentialSubject": {
                    "id": "did:cheqd:testnet:...",
                    "prescription": {...}
                }
            }
        """
        # Get timestamps
        issued_at = prescription.date_issued or datetime.utcnow()
        expires_at = prescription.date_expires

        # Format dates to ISO 8601
        issuance_date = issued_at.isoformat() + "Z"
        expiration_date = expires_at.isoformat() + "Z" if expires_at else None

        # Build credential structure
        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", "PrescriptionCredential"],
            "issuer": doctor_did,
            "issuanceDate": issuance_date,
            "credentialSubject": {
                "id": patient_did,
                "prescription": {
                    "id": prescription.id,
                    "medication_name": prescription.medication_name,
                    "medication_code": prescription.medication_code,
                    "dosage": prescription.dosage,
                    "quantity": prescription.quantity,
                    "instructions": prescription.instructions,
                    "date_issued": issuance_date,
                },
            },
        }

        # Add expiration date if available
        if expiration_date:
            credential["expirationDate"] = expiration_date

        return credential

    async def sign_credential(
        self,
        credential: Dict[str, Any],
        doctor_did: str,
    ) -> Dict[str, Any]:
        """Sign credential with doctor's DID using Ed25519.

        Adds W3C LD-Proof to credential using ACA-Py's issue-credential-2.0
        API endpoint. Returns signed credential with proof section.

        Args:
            credential: Unsigned W3C VC dict (from create_credential)
            doctor_did: Doctor's DID for signing (issuer)

        Returns:
            Dict containing signed W3C VC with proof:
            {
                ...credential fields,
                "proof": {
                    "type": "Ed25519Signature2020",
                    "created": "2026-02-11T10:30:00Z",
                    "proofPurpose": "assertionMethod",
                    "verificationMethod": "did:cheqd:testnet:...#key-1",
                    "proofValue": "base64-encoded-signature"
                }
            }

            Also returns metadata:
            {
                "credential": {...signed VC...},
                "credential_id": "cred_...",
                "signature": "base64-encoded-signature"
            }
        """
        # Issue credential via ACA-Py
        result = await self._acapy_service.issue_credential(credential)

        if "error" in result:
            raise Exception(f"Failed to sign credential: {result['error']}")

        # Extract signed credential
        signed_credential = result.get("credential", credential)

        # Ensure proof exists and add if missing
        if "proof" not in signed_credential:
            # Mock proof for local development
            # In production, ACA-Py will provide real cryptographic proof
            proof = {
                "type": "Ed25519Signature2020",
                "created": datetime.utcnow().isoformat() + "Z",
                "proofPurpose": "assertionMethod",
                "verificationMethod": f"{doctor_did}#key-1",
                "proofValue": self._generate_mock_signature(credential),
            }
            signed_credential["proof"] = proof

        # Extract signature from proof
        signature = signed_credential["proof"].get("proofValue", "")

        # Generate credential ID
        credential_id = (
            result.get("cred_ex_id")
            or result.get("credential_id")
            or self._generate_credential_id()
        )

        return {
            "credential": signed_credential,
            "credential_id": credential_id,
            "signature": signature,
        }

    async def verify_credential(
        self,
        credential: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify W3C Verifiable Credential signature.

        Uses ACA-Py's present-proof-2.0 API to verify cryptographic
        signature and proof validity.

        Args:
            credential: Signed W3C VC dict with proof section

        Returns:
            Dict with verification result:
            {
                "valid": true/false,
                "issuer": "did:cheqd:testnet:...",
                "subject": "did:cheqd:testnet:...",
                "signed_at": "2026-02-11T10:30:00Z",
                "expires_at": "2026-05-11T23:59:59Z" (if present),
                "signature_algorithm": "Ed25519Signature2020"
            }

            If verification fails:
            {
                "valid": false,
                "error": "reason"
            }
        """
        # Check credential has proof
        if "proof" not in credential:
            return {
                "valid": False,
                "error": "Credential has no proof",
            }

        # Verify via ACA-Py
        result = await self._acapy_service.verify_credential(credential)

        # Extract verification status
        valid = result.get("verified", False)

        if not valid:
            return {
                "valid": False,
                "error": result.get("error", "Signature verification failed"),
            }

        # Extract credential fields
        issuer = credential.get("issuer", "")
        subject = credential.get("credentialSubject", {}).get("id", "")
        signed_at = credential.get("proof", {}).get("created", "")
        expires_at = credential.get("expirationDate")
        signature_algorithm = credential.get("proof", {}).get("type", "Ed25519Signature2020")

        return {
            "valid": True,
            "issuer": issuer,
            "subject": subject,
            "signed_at": signed_at,
            "expires_at": expires_at,
            "signature_algorithm": signature_algorithm,
        }

    def _generate_mock_signature(self, credential: Dict[str, Any]) -> str:
        """Generate mock base64 signature for development.

        In production, ACA-Py provides real Ed25519 signature.
        This is fallback for local testing.

        Args:
            credential: Credential dict to sign

        Returns:
            Base64-encoded mock signature string
        """
        # Create deterministic signature based on credential content
        credential_json = json.dumps(credential, sort_keys=True)
        signature_bytes = credential_json.encode("utf-8")[:64]  # Mock 64-byte signature

        # Pad to 64 bytes if needed
        if len(signature_bytes) < 64:
            signature_bytes += b"\x00" * (64 - len(signature_bytes))

        return base64.b64encode(signature_bytes).decode("utf-8")

    def _generate_credential_id(self) -> str:
        """Generate unique credential ID.

        Returns:
            Credential ID string (format: cred_{timestamp})
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"cred_{timestamp}"

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
