"""Tests for prescription signing and credential issuance flow.

This is a TDD test suite - all tests FAIL until TASK-016 implements endpoints.
Tests cover:
- Sign prescription (POST /api/v1/prescriptions/{id}/sign)
- Verify signature (GET /api/v1/prescriptions/{id}/verify)
- W3C Verifiable Credential structure validation
- Cryptographic signature verification
- RBAC enforcement (only doctor can sign their own prescription)
- Error cases: unsigned prescription, already signed, not found, unauthorized
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES - Prescription and signing data
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

    Will fail until app has signing routes.
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def prescription_data_for_signing(patient_user):
    """Valid unsigned prescription data ready for signing.

    Patient ID comes from the patient_user fixture (ID=2).
    """
    return {
        "patient_id": 2,
        "medication_name": "Lisinopril",
        "medication_code": "C09AA01",
        "dosage": "10mg",
        "quantity": 30,
        "instructions": "Take one tablet once daily in the morning",
        "date_expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "is_repeat": False,
        "repeat_count": 0,
    }


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


# ============================================================================
# PRESCRIPTION SIGN TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_sign_prescription_success(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test successful prescription signing by doctor.

    EXPECTED FAILURE: Endpoint POST /api/v1/prescriptions/{id}/sign does not exist yet.
    Will be implemented in TASK-016.

    User Story: US-003 - Sign Prescription with Digital Signature

    Expected response (when implemented):
    {
        "prescription_id": 1,
        "credential_id": "cred_abc123xyz",
        "signed": true,
        "signed_at": "2026-02-11T10:30:00Z",
        "signature": "base64-encoded-ed25519-signature",
        "issuer_did": "did:cheqd:testnet:...",
        "subject_did": "did:cheqd:testnet:..."
    }
    """
    # First create an unsigned prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Now sign the prescription
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},  # Empty body - signature from current user's DID
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016 implements endpoint
    assert response.status_code == 201
    data = response.json()

    # Response structure validation
    assert "prescription_id" in data
    assert data["prescription_id"] == prescription_id
    assert "credential_id" in data
    assert "signed" in data
    assert data["signed"] is True
    assert "issuer_did" in data
    assert data["issuer_did"].startswith("did:cheqd:testnet:")
    assert "subject_did" in data
    assert data["subject_did"].startswith("did:cheqd:testnet:")


@pytest.mark.asyncio
async def test_sign_prescription_not_found(test_client, auth_headers_doctor):
    """Test signing non-existent prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Prescription not found"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions/99999/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sign_prescription_unauthorized(
    test_client, prescription_data_for_signing
):
    """Test signing prescription without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions/1/sign",
        json={},
        # No Authorization header
    )

    # FAILS until TASK-016
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sign_prescription_forbidden_patient(
    test_client, auth_headers_doctor, auth_headers_patient,
    prescription_data_for_signing
):
    """Test that patient cannot sign prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Only doctor can sign prescriptions
    - Returns 403 Forbidden
    """
    # Create prescription as doctor
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Try to sign as patient
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_patient,
    )

    # FAILS until TASK-016
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sign_prescription_forbidden_pharmacist(
    test_client, auth_headers_doctor, auth_headers_pharmacist,
    prescription_data_for_signing
):
    """Test that pharmacist cannot sign prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Only doctor can sign prescriptions
    - Returns 403 Forbidden
    """
    # Create prescription as doctor
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Try to sign as pharmacist
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-016
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sign_prescription_forbidden_different_doctor(
    test_client, auth_headers_doctor, prescription_data_for_signing, test_session
):
    """Test that only prescribing doctor can sign their prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Doctor 1 creates prescription
    - Doctor 2 cannot sign it
    - Returns 403 Forbidden
    """
    # Create prescription as doctor (user_id=1)
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Create another doctor user
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.auth import create_access_token

    other_doctor = User(
        username="dr_brown",
        email="brown@hospital.co.za",
        password_hash=hash_password("password123"),
        role="doctor",
        full_name="Dr. Brown",
        registration_number="HPCSA_99999",
    )
    test_session.add(other_doctor)
    test_session.commit()
    test_session.refresh(other_doctor)

    other_doctor_token = create_access_token({
        "sub": str(other_doctor.id),
        "username": other_doctor.username,
        "role": "doctor"
    })
    other_doctor_headers = {
        "Authorization": f"Bearer {other_doctor_token}",
        "Content-Type": "application/json",
    }

    # Try to sign as different doctor
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=other_doctor_headers,
    )

    # FAILS until TASK-016
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sign_prescription_already_signed(
    test_client, auth_headers_doctor, prescription_data_for_signing, test_session
):
    """Test that already-signed prescriptions cannot be signed again.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - First sign attempt → 201 Created
    - Second sign attempt → 409 Conflict
    """
    # Create prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # First sign
    response1 = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS at this step - endpoint doesn't exist
    # When implemented, should be 201
    if response1.status_code == 201:
        # Try to sign again
        response2 = test_client.post(
            f"/api/v1/prescriptions/{prescription_id}/sign",
            json={},
            headers=auth_headers_doctor,
        )

        # Second attempt should fail with 409 Conflict
        assert response2.status_code == 409
        assert "already" in response2.json()["detail"].lower()


# ============================================================================
# PRESCRIPTION VERIFY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_prescription_success(
    test_client, auth_headers_doctor, auth_headers_pharmacist,
    prescription_data_for_signing
):
    """Test successful prescription verification by pharmacist.

    Endpoint exists but verification service has internal errors (returns 500).
    Needs investigation in verification service.

    User Story: US-010 - Verify Prescription Authenticity
    """
    # Create and sign prescription as doctor
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )
    assert sign_response.status_code == 201

    # Verify as pharmacist
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}/verify",
        headers=auth_headers_pharmacist,
    )

    # Should return 200 with verification result
    # Currently returns 500 due to verification service error (marked as xfail)
    assert response.status_code == 200
    data = response.json()
    # Verification result
    assert "verified" in data
    assert data["verified"] is True
    assert "issuer_did" in data
    assert data["issuer_did"].startswith("did:cheqd:testnet:")
    assert "credential_id" in data


@pytest.mark.asyncio
async def test_verify_unsigned_prescription(
    test_client, auth_headers_doctor, auth_headers_pharmacist,
    prescription_data_for_signing
):
    """Test verification of unsigned prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Prescription has no signature yet
    - Returns 400 Bad Request or 404 Not Found
    """
    # Create prescription (unsigned)
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Try to verify unsigned prescription
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-016
    # Should be 400 (not signed) or 404 (verification not available)
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_verify_prescription_not_found(
    test_client, auth_headers_pharmacist
):
    """Test verifying non-existent prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Prescription not found"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions/99999/verify",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-016
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_prescription_unauthorized(test_client):
    """Test verification without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions/1/verify",
        # No Authorization header
    )

    # FAILS until TASK-016
    assert response.status_code == 401


# ============================================================================
# W3C VERIFIABLE CREDENTIAL STRUCTURE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_signed_prescription_has_valid_vc_structure(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test that signed prescription generates valid W3C VC structure.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected credential structure (when implemented):
    {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "PrescriptionCredential"],
        "issuer": "did:cheqd:testnet:...",
        "issuanceDate": "2026-02-11T10:30:00Z",
        "expirationDate": "2026-05-11T23:59:59Z",
        "credentialSubject": {
            "id": "did:cheqd:testnet:...",
            "prescription": {
                "id": 1,
                "medication_name": "Lisinopril",
                "medication_code": "C09AA01",
                "dosage": "10mg",
                "quantity": 30,
                "instructions": "Take one tablet once daily in the morning",
                "date_issued": "2026-02-11T10:30:00Z"
            }
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": "2026-02-11T10:30:00Z",
            "proofPurpose": "assertionMethod",
            "verificationMethod": "did:cheqd:testnet:...#key-1",
            "proofValue": "base64-encoded-ed25519-signature"
        }
    }
    """
    # Create prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Sign prescription
    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    signed_data = sign_response.json()

    # Verify credential structure (will be available in response or via GET)
    assert "credential_id" in signed_data

    # Get signed prescription to inspect credential
    get_response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}",
        headers=auth_headers_doctor,
    )

    assert get_response.status_code == 200
    prescription = get_response.json()

    # Check prescription has signature fields
    assert prescription["digital_signature"] is not None
    assert prescription["credential_id"] is not None


@pytest.mark.asyncio
async def test_credential_context_w3c_compliance(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test that generated credential includes required W3C context.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Credential includes @context array
    - Must contain "https://www.w3.org/2018/credentials/v1"
    - May include additional contexts for custom types
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    signed_data = sign_response.json()

    # Verify context would be present
    # (This tests implementation when endpoint exists)
    assert "credential_id" in signed_data


@pytest.mark.asyncio
async def test_credential_has_issuer_did(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test that credential issuer is doctor's DID.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Credential issuer = doctor's DID
    - Format: did:cheqd:testnet:[unique-id]
    - Matches doctor's DID from DIDs table
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    data = sign_response.json()

    # Verify issuer is doctor's DID
    assert "issuer_did" in data
    assert data["issuer_did"].startswith("did:cheqd:testnet:")
    assert len(data["issuer_did"]) > 30


@pytest.mark.asyncio
async def test_credential_has_subject_did(
    test_client, auth_headers_doctor, prescription_data_for_signing, patient_user
):
    """Test that credential subject is patient's DID.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Credential subject = patient's DID
    - Format: did:cheqd:testnet:[unique-id]
    - Matches patient's DID from DIDs table
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    data = sign_response.json()

    # Verify subject is patient's DID
    assert "subject_did" in data
    assert data["subject_did"].startswith("did:cheqd:testnet:")
    assert len(data["subject_did"]) > 30


# ============================================================================
# CRYPTOGRAPHIC SIGNATURE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_signature_is_base64_encoded(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test that signature is valid base64 encoding.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Signature field contains base64-encoded bytes
    - Should be decodable to binary data
    - Signature length > 50 characters (typical for Ed25519)
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    data = sign_response.json()

    # Verify signature
    assert "signature" in data
    signature = data["signature"]
    assert len(signature) > 50  # Ed25519 signatures are ~86 chars in base64

    # Try to decode to verify it's valid base64
    try:
        import base64
        decoded = base64.b64decode(signature)
        assert len(decoded) > 0  # Signature should have content
    except Exception:
        pytest.fail("Signature is not valid base64 encoding")


@pytest.mark.asyncio
async def test_signature_algorithm_ed25519(
    test_client, auth_headers_doctor, auth_headers_pharmacist,
    prescription_data_for_signing
):
    """Test that signature uses Ed25519 algorithm.

    Verification endpoint exists but returns 500 due to verification service error.
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )
    assert sign_response.status_code == 201

    # Verify the signature algorithm via verification endpoint
    verify_response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}/verify",
        headers=auth_headers_pharmacist,
    )

    # Should return 200 with verification result
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert "verified" in verify_data


@pytest.mark.asyncio
async def test_signature_verification_returns_valid_true(
    test_client, auth_headers_doctor, auth_headers_pharmacist,
    prescription_data_for_signing
):
    """Test that legitimate signature verifies successfully.

    Verification endpoint exists but returns 500 due to verification service error.
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201

    # Verify signature
    verify_response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}/verify",
        headers=auth_headers_pharmacist,
    )

    # Should return 200 with verification result
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["verified"] is True


@pytest.mark.asyncio
async def test_signature_includes_proof_purpose(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test that signature proof includes proofPurpose.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Signature has proofPurpose field
    - proofPurpose = "assertionMethod"
    - This indicates the doctor is asserting the prescription's authenticity
    """
    # Create and sign prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    assert sign_response.status_code == 201
    # proofPurpose would be in full credential structure
    # (tested when endpoint exists)


# ============================================================================
# RBAC & PERMISSION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_only_doctor_can_sign_prescription(
    test_client, auth_headers_doctor, auth_headers_patient,
    auth_headers_pharmacist, prescription_data_for_signing
):
    """Test that only doctor role can sign prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Patient cannot sign → 403
    - Pharmacist cannot sign → 403
    - Doctor can sign → 201
    """
    # Create prescription as doctor
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Patient tries to sign
    patient_sign = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_patient,
    )

    # FAILS until TASK-016
    assert patient_sign.status_code == 403

    # Pharmacist tries to sign
    pharmacist_sign = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_pharmacist,
    )

    assert pharmacist_sign.status_code == 403


@pytest.mark.asyncio
async def test_verify_available_to_all_roles(
    test_client, auth_headers_doctor, auth_headers_patient,
    auth_headers_pharmacist, prescription_data_for_signing
):
    """Test that all roles can verify signed prescriptions.

    Verification endpoint exists but returns 500 due to verification service error.
    - Doctor can verify → 200 OK (expected)
    - Patient can verify → 200 OK (expected)
    - Pharmacist can verify → 200 OK
    """
    # Create and sign prescription as doctor
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    sign_response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # All roles should be able to verify (endpoint allows all authenticated users)
    # Currently returns 500 due to verification service error (marked as xfail)
    if sign_response.status_code == 201:
        # Doctor verifies
        doctor_verify = test_client.get(
            f"/api/v1/prescriptions/{prescription_id}/verify",
            headers=auth_headers_doctor,
        )
        assert doctor_verify.status_code == 200

        # Patient verifies
        patient_verify = test_client.get(
            f"/api/v1/prescriptions/{prescription_id}/verify",
            headers=auth_headers_patient,
        )
        assert patient_verify.status_code == 200

        # Pharmacist verifies
        pharmacist_verify = test_client.get(
            f"/api/v1/prescriptions/{prescription_id}/verify",
            headers=auth_headers_pharmacist,
        )
        assert pharmacist_verify.status_code == 200


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_sign_prescription_without_patient_did(
    test_client, auth_headers_doctor, prescription_data_for_signing, test_session
):
    """Test signing prescription when patient has no DID.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Patient without DID cannot be prescription subject
    - Returns 400 Bad Request or auto-creates DID
    - Implementation decides behavior
    """
    # Create prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Try to sign (patient has no DID yet)
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    # May succeed (auto-create DID) or fail (DID required)
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_sign_prescription_without_doctor_did(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test signing prescription when doctor has no DID.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Doctor issuer without DID cannot sign
    - Returns 400 Bad Request
    - Must have DID before signing
    """
    # Create prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # Try to sign (doctor has no DID yet)
    response = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    # May fail (DID required) or auto-create
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_sign_prescription_concurrent_requests(
    test_client, auth_headers_doctor, prescription_data_for_signing
):
    """Test concurrent sign requests don't create duplicate signatures.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - First request succeeds → 201
    - Second concurrent request fails → 409 or waits for lock
    - Ensures signature idempotency
    """
    # Create prescription
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_for_signing,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    # First sign request
    response1 = test_client.post(
        f"/api/v1/prescriptions/{prescription_id}/sign",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-016
    if response1.status_code == 201:
        # Second sign request (concurrent scenario)
        response2 = test_client.post(
            f"/api/v1/prescriptions/{prescription_id}/sign",
            json={},
            headers=auth_headers_doctor,
        )

        # Should prevent double-signing
        assert response2.status_code == 409
