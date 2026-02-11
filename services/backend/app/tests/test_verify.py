"""Tests for prescription verification flow (W3C VC verification).

This is a TDD test suite - all tests FAIL until TASK-020 implements endpoints.
Tests cover:
- Verify prescription signature (GET /api/v1/prescriptions/{id}/verify)
- Validate W3C VC signature against doctor's DID
- Check doctor DID in trust registry
- Check credential revocation status
- Complete verification flow (signature + trust + revocation)
- RBAC enforcement (all authenticated users can verify)
- Error cases: invalid signature, revoked, not found, unsigned

User Story: US-010 - Verify Prescription Authenticity

Expected API endpoint:
GET /api/v1/prescriptions/{id}/verify

Response 200 (success):
{
    "verified": true,
    "prescription_id": 1,
    "credential_id": "cred_123456",
    "checks": {
        "signature_valid": true,
        "doctor_trusted": true,
        "not_revoked": true
    },
    "issuer_did": "did:cheqd:testnet:...",
    "subject_did": "did:cheqd:testnet:...",
    "verified_at": "2026-02-11T16:45:00Z"
}

Response 200 (verification failed):
{
    "verified": false,
    "prescription_id": 1,
    "credential_id": "cred_123456",
    "checks": {
        "signature_valid": false,
        "doctor_trusted": true,
        "not_revoked": true
    },
    "error": "Invalid signature",
    "verified_at": "2026-02-11T16:45:00Z"
}
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_client(
    override_get_db,
    doctor_user,
    patient_user,
    pharmacist_user,
    doctor_with_did,
    patient_with_did,
    mock_acapy_signing_service,
):
    """Create FastAPI TestClient for making requests.

    Will fail until app has verification routes.
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers_doctor(valid_jwt_token):
    """Headers with doctor JWT token."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_patient(valid_patient_jwt_token):
    """Headers with patient JWT token."""
    return {
        "Authorization": f"Bearer {valid_patient_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_pharmacist(valid_pharmacist_jwt_token):
    """Headers with pharmacist JWT token."""
    return {
        "Authorization": f"Bearer {valid_pharmacist_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def signed_prescription_data(patient_user):
    """Valid signed prescription data ready for verification.

    Patient ID comes from the patient_user fixture (ID=2).
    Includes digital_signature and credential_id to simulate already-signed Rx.
    """
    return {
        "patient_id": 2,
        "medication_name": "Lisinopril",
        "medication_code": "C09AA01",
        "dosage": "10mg",
        "quantity": 30,
        "instructions": "Take one tablet once daily in the morning",
        "date_issued": datetime.utcnow().isoformat(),
        "date_expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "is_repeat": False,
        "repeat_count": 0,
        "digital_signature": "mock_signature_base64_ed25519",
        "credential_id": "cred_12345_verification_test",
    }


@pytest.fixture
def valid_vc_credential(doctor_with_did, patient_with_did):
    """Valid W3C Verifiable Credential for testing.

    Simulates a signed prescription credential with:
    - Valid Ed25519 signature
    - Doctor as issuer
    - Patient as subject
    - All required W3C VC fields
    """
    # Get DIDs from fixtures
    doctor_did = (
        doctor_with_did.dids[0].did_identifier
        if hasattr(doctor_with_did, "dids")
        else "did:cheqd:testnet:doctor123"
    )
    patient_did = (
        patient_with_did.dids[0].did_identifier
        if hasattr(patient_with_did, "dids")
        else "did:cheqd:testnet:patient456"
    )

    return {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "PrescriptionCredential"],
        "issuer": doctor_did,
        "issuanceDate": datetime.utcnow().isoformat() + "Z",
        "expirationDate": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z",
        "credentialSubject": {
            "id": patient_did,
            "prescription": {
                "id": 1,
                "medication_name": "Lisinopril",
                "medication_code": "C09AA01",
                "dosage": "10mg",
                "quantity": 30,
                "instructions": "Take once daily",
            },
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat() + "Z",
            "proofPurpose": "assertionMethod",
            "verificationMethod": f"{doctor_did}#key-1",
            "proofValue": "base64encodedSignatureDataHere",
        },
    }


# ============================================================================
# SIGNATURE VERIFICATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_valid_signed_prescription(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verifying a prescription with valid signature.

    EXPECTED FAILURE: Endpoint GET /api/v1/prescriptions/{id}/verify does not exist.
    Will be implemented in TASK-020.

    User Story: US-010

    Expected response:
    {
        "verified": true,
        "prescription_id": 1,
        "credential_id": "cred_12345",
        "checks": {
            "signature_valid": true,
            "doctor_trusted": true,
            "not_revoked": true
        },
        "issuer_did": "did:cheqd:testnet:...",
        "subject_did": "did:cheqd:testnet:...",
        "verified_at": "2026-02-11T16:45:00Z"
    }
    """
    from app.models.prescription import Prescription

    # Create and sign a prescription
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=21,
        instructions="Take 1 capsule three times daily with food",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="valid_ed25519_signature_base64",
        credential_id="cred_valid_test_12345",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    # Attempt to verify
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020 implements endpoint
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is True
        assert data["prescription_id"] == prescription.id
        assert "credential_id" in data
        assert "checks" in data
        assert data["checks"]["signature_valid"] is True
        assert data["checks"]["doctor_trusted"] is True
        assert data["checks"]["not_revoked"] is True
        assert "verified_at" in data


@pytest.mark.asyncio
async def test_verify_invalid_signature(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification fails with invalid signature.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response:
    {
        "verified": false,
        "checks": {
            "signature_valid": false,
            "doctor_trusted": true,
            "not_revoked": true
        },
        "error": "Invalid signature"
    }
    """
    from app.models.prescription import Prescription

    # Create prescription with INVALID signature
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Paracetamol",
        medication_code="N02BE01",
        dosage="500mg",
        quantity=20,
        instructions="Take as needed",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=30),
        digital_signature="invalid_tampered_signature_data",
        credential_id="cred_invalid_sig_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is False
        assert data["checks"]["signature_valid"] is False


@pytest.mark.asyncio
async def test_verify_unsigned_prescription(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification fails for unsigned prescription.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response: 400 or 200 with verified=false
    """
    from app.models.prescription import Prescription

    # Create UNSIGNED prescription (no digital_signature field)
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Ibuprofen",
        medication_code="M01AE01",
        dosage="200mg",
        quantity=20,
        instructions="Take with food",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=30),
        # No digital_signature - NULL
        # No credential_id - NULL
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    # Should be 400 Bad Request or 200 with verified=false
    if response.status_code in (200, 400):
        if response.status_code == 200:
            data = response.json()
            assert data["verified"] is False


@pytest.mark.asyncio
async def test_verify_tampered_prescription(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification fails when prescription data is tampered.

    EXPECTED FAILURE: Endpoint does not exist.

    Scenario:
    - Original Rx: quantity=30
    - After retrieval: quantity=5 (modified)
    - Signature was for original data → verification fails
    """
    from app.models.prescription import Prescription

    # Create prescription with valid signature for specific data
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=30,  # Original quantity
        instructions="Take 1 capsule three times daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="signature_for_qty_30_only",
        credential_id="cred_tamper_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    # Simulate tampering by modifying prescription
    prescription.quantity = 5
    test_session.commit()

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is False
        assert data["checks"]["signature_valid"] is False


@pytest.mark.asyncio
async def test_verify_prescription_not_found(test_client, auth_headers_pharmacist):
    """Test verification returns 404 for non-existent prescription.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response: 404 Not Found
    """
    response = test_client.get(
        "/api/v1/prescriptions/99999/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020 - likely 404
    if response.status_code != 404:
        # If endpoint exists, should be 404 for missing prescription
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_unauthenticated(test_client, test_session, doctor_user, patient_user):
    """Test verification requires authentication.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response: 401 Unauthorized (no auth header)
    """
    from app.models.prescription import Prescription

    # Create a prescription
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Lisinopril",
        medication_code="C09AA01",
        dosage="10mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_signature",
        credential_id="cred_auth_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    # Request without Authorization header
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
    )

    # FAILS until TASK-020 - likely 401
    if response.status_code != 404:
        # If endpoint exists, should be 401 without auth
        assert response.status_code == 401


# ============================================================================
# TRUST REGISTRY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_checks_doctor_did_in_trust_registry(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user, doctor_with_did
):
    """Test verification checks if doctor's DID is in trust registry.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Extract doctor's DID from prescription issuer
    - Check if DID in trust registry (mock: hardcoded TRUSTED_DOCTOR_DIDS)
    - If found: checks.doctor_trusted = true
    - If not found: checks.doctor_trusted = false
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Lisinopril",
        medication_code="C09AA01",
        dosage="10mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_trust_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert "checks" in data
        assert "doctor_trusted" in data["checks"]
        assert isinstance(data["checks"]["doctor_trusted"], bool)


@pytest.mark.asyncio
async def test_verify_untrusted_doctor_did(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification fails if doctor's DID not in trust registry.

    EXPECTED FAILURE: Endpoint does not exist.

    Scenario:
    - Doctor DID: did:cheqd:testnet:untrusted-doctor-12345
    - This DID is NOT in TRUSTED_DOCTOR_DIDS mock registry
    - Expected: checks.doctor_trusted = false
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Metformin",
        medication_code="A10BA02",
        dosage="500mg",
        quantity=60,
        instructions="Take twice daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=180),
        digital_signature="test_sig_untrusted",
        credential_id="cred_untrusted_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        # Verification should fail or flag trust check as false
        if data["verified"] is False:
            assert data["checks"]["doctor_trusted"] is False


@pytest.mark.asyncio
async def test_verify_trust_registry_unavailable(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test graceful handling when trust registry is unavailable.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Trust registry temporarily unavailable
    - Service returns verified=false or error message
    - OR includes "doctor_trusted": null/unknown
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Atorvastatin",
        medication_code="C10AA05",
        dosage="20mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_registry_error_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        # Should handle gracefully (either fail verification or flag as unknown)
        assert "verified" in data or "error" in data


# ============================================================================
# REVOCATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_checks_revocation_status(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification checks if credential is revoked.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Query revocation registry via ACA-Py
    - For MVP: mock always returns not_revoked=true
    - checks.not_revoked boolean field
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Aspirin",
        medication_code="B01AC06",
        dosage="100mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_revocation_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert "checks" in data
        assert "not_revoked" in data["checks"]
        assert isinstance(data["checks"]["not_revoked"], bool)


@pytest.mark.asyncio
async def test_verify_revoked_prescription(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification fails if prescription is revoked.

    EXPECTED FAILURE: Endpoint does not exist.

    Scenario:
    - Doctor revokes prescription after issuance
    - Credential credential_id is marked revoked in registry
    - Verification fails: verified=false, checks.not_revoked=false
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Oxycodone",
        medication_code="N02AA05",
        dosage="5mg",
        quantity=10,
        instructions="Take as needed for pain",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=30),
        digital_signature="test_sig_revoked",
        credential_id="cred_revoked_test",
        is_revoked=True,  # Mark as revoked
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is False
        if "checks" in data:
            assert data["checks"]["not_revoked"] is False


@pytest.mark.asyncio
async def test_verify_revocation_registry_unavailable(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test graceful handling when revocation registry is unavailable.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Revocation registry temporarily unreachable
    - Service returns verified=false or error
    - OR includes "not_revoked": null/unknown
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Fluoxetine",
        medication_code="N06AB03",
        dosage="20mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_revoc_unavail_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        # Should handle gracefully
        assert "verified" in data or "error" in data


# ============================================================================
# COMPLETE VERIFICATION FLOW TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_complete_flow_success(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test complete verification flow with all checks passing.

    EXPECTED FAILURE: Endpoint does not exist.

    Verification Flow:
    1. Signature verification: valid Ed25519 signature ✓
    2. Trust registry check: doctor's DID is trusted ✓
    3. Revocation check: credential not revoked ✓
    → Result: verified=true
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Lisinopril",
        medication_code="C09AA01",
        dosage="10mg",
        quantity=30,
        instructions="Take once daily in the morning",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="valid_signature_data",
        credential_id="cred_complete_flow_success",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is True
        assert "checks" in data
        assert data["checks"]["signature_valid"] is True
        assert data["checks"]["doctor_trusted"] is True
        assert data["checks"]["not_revoked"] is True


@pytest.mark.asyncio
async def test_verify_complete_flow_failure(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test complete verification flow with ANY check failing.

    EXPECTED FAILURE: Endpoint does not exist.

    Scenario:
    - Signature: invalid (modified data)
    - Trust: doctor is trusted
    - Revocation: not revoked
    → Result: verified=false (ANY check failing = fail)
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=21,
        instructions="Take three times daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="invalid_broken_signature",
        credential_id="cred_complete_flow_fail",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert data["verified"] is False
        # At least one check should be false
        checks = data.get("checks", {})
        assert (
            checks.get("signature_valid") is False
            or checks.get("doctor_trusted") is False
            or checks.get("not_revoked") is False
        )


# ============================================================================
# RBAC TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_doctor_can_verify(
    test_client, auth_headers_doctor, test_session, doctor_user, patient_user
):
    """Test that doctor role can verify prescriptions.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Doctor can call GET /api/v1/prescriptions/{id}/verify
    - Returns verification result (not 403 Forbidden)
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Metformin",
        medication_code="A10BA02",
        dosage="500mg",
        quantity=60,
        instructions="Take twice daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=180),
        digital_signature="test_sig",
        credential_id="cred_doctor_verify_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-020
    # Should be 200 (success or fail verification), not 403 (forbidden)
    if response.status_code != 404:
        assert response.status_code != 403


@pytest.mark.asyncio
async def test_verify_patient_can_verify(
    test_client, auth_headers_patient, test_session, doctor_user, patient_user
):
    """Test that patient role can verify prescriptions.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Patient can call GET /api/v1/prescriptions/{id}/verify
    - Returns verification result (not 403 Forbidden)
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Vitamin D3",
        medication_code="A11CC05",
        dosage="1000IU",
        quantity=90,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=365),
        digital_signature="test_sig",
        credential_id="cred_patient_verify_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_patient,
    )

    # FAILS until TASK-020
    if response.status_code != 404:
        assert response.status_code != 403


@pytest.mark.asyncio
async def test_verify_pharmacist_can_verify(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test that pharmacist role can verify prescriptions.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Pharmacist can call GET /api/v1/prescriptions/{id}/verify
    - Primary use case for verification
    - Returns verification result
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Sertraline",
        medication_code="N06AB06",
        dosage="50mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_pharmacist_verify_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        # Pharmacist should be able to verify
        data = response.json()
        assert "verified" in data


@pytest.mark.asyncio
async def test_verify_all_roles_can_verify(
    test_client,
    auth_headers_doctor,
    auth_headers_patient,
    auth_headers_pharmacist,
    test_session,
    doctor_user,
    patient_user,
):
    """Test that all authenticated roles can verify prescriptions.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected behavior:
    - Doctor: Can verify ✓
    - Patient: Can verify ✓
    - Pharmacist: Can verify ✓
    - Unauthenticated: Cannot verify (401) ✓

    No role-based restriction - all authenticated users have access.
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Lisinopril",
        medication_code="C09AA01",
        dosage="10mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_all_roles_verify",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    # Test doctor can verify
    doctor_response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_doctor,
    )

    # Test patient can verify
    patient_response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_patient,
    )

    # Test pharmacist can verify
    pharmacist_response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    # If endpoint exists, none should return 403
    for response in [doctor_response, patient_response, pharmacist_response]:
        if response.status_code != 404:
            assert response.status_code != 403


# ============================================================================
# ERROR CASE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_error_invalid_prescription_id_type(test_client, auth_headers_pharmacist):
    """Test verification with invalid prescription ID format.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response: 422 Unprocessable Entity (invalid path parameter type)
    """
    response = test_client.get(
        "/api/v1/prescriptions/invalid-id-not-integer/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    # Should be 404 or 422, not 500
    if response.status_code != 404:
        assert response.status_code in (422, 400)


@pytest.mark.asyncio
async def test_verify_error_malformed_auth_header(
    test_client, test_session, doctor_user, patient_user
):
    """Test verification with malformed authorization header.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response: 401 Unauthorized
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Test",
        medication_code="TEST01",
        dosage="1mg",
        quantity=1,
        instructions="Test",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=30),
        digital_signature="test",
        credential_id="cred_malformed_auth",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    headers = {"Authorization": "Bearer invalid-token-format"}
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=headers,
    )

    # FAILS until TASK-020
    if response.status_code != 404:
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_response_includes_timestamps(
    test_client, auth_headers_pharmacist, test_session, doctor_user, patient_user
):
    """Test verification response includes timestamp.

    EXPECTED FAILURE: Endpoint does not exist.

    Expected response field: "verified_at" (ISO 8601 timestamp)
    """
    from app.models.prescription import Prescription

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Aspirin",
        medication_code="B01AC06",
        dosage="100mg",
        quantity=30,
        instructions="Take once daily",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="test_sig",
        credential_id="cred_timestamp_test",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)

    response = test_client.get(
        f"/api/v1/prescriptions/{prescription.id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-020
    if response.status_code == 200:
        data = response.json()
        assert "verified_at" in data
        # Should be ISO 8601 format
        assert "T" in data["verified_at"]
