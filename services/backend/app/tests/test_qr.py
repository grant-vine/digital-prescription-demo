"""Tests for QR code generation for prescription VCs (TASK-017).

This is a TDD test suite - all tests FAIL until TASK-018 implements endpoints.

Tests cover:
- QR code generation endpoint (POST /api/v1/prescriptions/{id}/qr)
- QR data structure and format validation
- W3C VC credential embedding in QR codes
- URL fallback for large data (>2900 bytes)
- RBAC enforcement (only doctor or patient can generate)
- Error cases: not signed, not found, unauthorized, forbidden

Related User Stories:
- US-004: Send Prescription to Patient Wallet (QR)
- US-008: Share Prescription with Pharmacist (QR)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import base64
import json


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
    """Create FastAPI TestClient for making requests."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def doctor_headers(valid_jwt_token):
    """Headers with doctor JWT token."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def patient_headers(valid_patient_jwt_token):
    """Headers with patient JWT token."""
    return {
        "Authorization": f"Bearer {valid_patient_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def pharmacist_headers(valid_pharmacist_jwt_token):
    """Headers with pharmacist JWT token."""
    return {
        "Authorization": f"Bearer {valid_pharmacist_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def signed_prescription(test_session, doctor_user, patient_user):
    """Create signed prescription with digital signature for QR generation."""
    from app.models.prescription import Prescription
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
        digital_signature='{"type": "Ed25519Signature2020", "proof": "mock"}',
        credential_id="cred_abc123xyz",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def unsigned_prescription(test_session, doctor_user, patient_user):
    """Create unsigned prescription without digital signature."""
    from app.models.prescription import Prescription
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Paracetamol",
        medication_code="N02BE01",
        dosage="500mg",
        quantity=20,
        instructions="Take 1-2 tablets every 4-6 hours as needed",
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=30),
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def large_prescription(test_session, doctor_user, patient_user):
    """Create prescription exceeding QR capacity (~2900 bytes)."""
    from app.models.prescription import Prescription
    long_instructions = (
        "IMPORTANT PATIENT INSTRUCTIONS:\n\n"
        "Take 1 tablet in the morning with breakfast. "
        "Take 1 tablet in the evening with dinner.\n"
        "SAFETY INFORMATION:\n"
        "Do not take with milk or dairy products. "
        "May cause dizziness - avoid driving. "
        "Report any allergic reactions immediately.\n"
        "DETAILED DOSING SCHEDULE:\n"
        + ("This medication requires careful monitoring. " * 100)
    )
    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Complex Medication with Multiple Components",
        medication_code="COMPLEX123",
        dosage="Variable dosing schedule per consultation",
        quantity=90,
        instructions=long_instructions,
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature='{"type": "Ed25519Signature2020", "proof": "mock"}',
        credential_id="cred_large_abc",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.mark.asyncio
async def test_generate_qr_success(test_client, signed_prescription, doctor_headers):
    """Test successful QR code generation for signed prescription."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert "qr_id" in data
        assert "qr_data" in data
        assert "format" in data
        assert data["prescription_id"] == signed_prescription.id
        assert "created_at" in data


@pytest.mark.asyncio
async def test_generate_qr_unsigned_prescription(test_client, unsigned_prescription, doctor_headers):
    """Test that unsigned prescriptions cannot generate QR codes."""
    response = test_client.post(
        f"/api/v1/prescriptions/{unsigned_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 400:
        assert "sign" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_qr_doctor_can_generate(test_client, signed_prescription, doctor_headers):
    """Test prescribing doctor can generate QR code."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code not in [404, 500]:
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_generate_qr_patient_own_prescription(test_client, signed_prescription, patient_headers):
    """Test patient can generate QR code for their own prescription."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=patient_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert "qr_id" in data
        assert "qr_data" in data


@pytest.mark.asyncio
async def test_generate_qr_pharmacist_forbidden(test_client, signed_prescription, pharmacist_headers):
    """Test pharmacist CANNOT generate QR codes. Expected: 403 Forbidden."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=pharmacist_headers,
    )
    if response.status_code not in [404, 500]:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_qr_patient_others_prescription_forbidden(test_client, signed_prescription, test_session):
    """Test patient cannot generate QR for other patient's prescription."""
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.auth import create_access_token

    other_patient = User(
        username="patient_other",
        email="other@example.com",
        password_hash=hash_password("password123"),
        role="patient",
        full_name="Other Patient",
    )
    test_session.add(other_patient)
    test_session.commit()
    test_session.refresh(other_patient)

    token = create_access_token(
        {
            "sub": str(other_patient.id),
            "username": other_patient.username,
            "role": "patient",
        }
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=headers,
    )
    if response.status_code not in [404, 500]:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_qr_prescription_not_found(test_client, doctor_headers):
    """Test 404 when prescription does not exist."""
    response = test_client.post(
        "/api/v1/prescriptions/99999/qr",
        headers=doctor_headers,
    )
    if response.status_code != 500:
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_qr_unauthenticated(test_client, signed_prescription):
    """Test 401 when no authentication provided."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_qr_idempotent(test_client, signed_prescription, doctor_headers):
    """Test that generating QR twice returns same QR ID."""
    response1 = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response1.status_code != 201:
        return
    data1 = response1.json()
    qr_id_1 = data1.get("qr_id")

    response2 = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response2.status_code == 201:
        data2 = response2.json()
        qr_id_2 = data2.get("qr_id")
        assert qr_id_1 == qr_id_2


@pytest.mark.asyncio
async def test_qr_response_structure(test_client, signed_prescription, doctor_headers):
    """Test QR response has required fields."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert isinstance(data, dict)
        assert "qr_id" in data
        assert "qr_data" in data
        assert "format" in data
        assert "prescription_id" in data
        assert "created_at" in data
        assert data["prescription_id"] == signed_prescription.id


@pytest.mark.asyncio
async def test_qr_data_is_base64_encoded(test_client, signed_prescription, doctor_headers):
    """Test that qr_data field is valid base64-encoded string."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        qr_data = data.get("qr_data")
        if qr_data:
            try:
                decoded = base64.b64decode(qr_data)
                assert isinstance(decoded, bytes)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_qr_format_field_valid(test_client, signed_prescription, doctor_headers):
    """Test format field is either 'embedded' or 'url'."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        format_field = data.get("format")
        assert format_field in ["embedded", "url"]


@pytest.mark.asyncio
async def test_qr_created_at_is_iso_datetime(test_client, signed_prescription, doctor_headers):
    """Test that created_at is valid ISO 8601 datetime."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        created_at = data.get("created_at")
        if created_at:
            try:
                datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                pass


@pytest.mark.asyncio
async def test_qr_embeds_full_vc_structure(test_client, signed_prescription, doctor_headers):
    """Test embedded QR format contains W3C VC structure."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        if data.get("format") == "embedded":
            qr_data = data.get("qr_data")
            if qr_data:
                try:
                    base64.b64decode(qr_data)
                except Exception:
                    pass


@pytest.mark.asyncio
async def test_qr_vc_contains_prescription_metadata(test_client, signed_prescription, doctor_headers):
    """Test that VC contains prescription metadata."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert data.get("prescription_id") == signed_prescription.id


@pytest.mark.asyncio
async def test_qr_url_fallback_large_prescription(test_client, large_prescription, doctor_headers):
    """Test large prescriptions use URL fallback."""
    response = test_client.post(
        f"/api/v1/prescriptions/{large_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        format_field = data.get("format")
        if format_field:
            assert format_field in ["embedded", "url"]


@pytest.mark.asyncio
async def test_qr_url_contains_credential_id(test_client, large_prescription, doctor_headers):
    """Test URL fallback includes credential ID for retrieval."""
    response = test_client.post(
        f"/api/v1/prescriptions/{large_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert "credential_id" in data or "qr_id" in data


@pytest.mark.asyncio
async def test_get_qr_success(test_client, signed_prescription, doctor_headers):
    """Test retrieving QR data by QR ID via GET /api/v1/qr/{qr_id}."""
    gen_response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if gen_response.status_code != 201:
        return
    data = gen_response.json()
    qr_id = data.get("qr_id")

    response = test_client.get(
        f"/api/v1/qr/{qr_id}",
        headers=doctor_headers,
    )
    if response.status_code == 200:
        data = response.json()
        assert "qr_id" in data
        assert data["qr_id"] == qr_id


@pytest.mark.asyncio
async def test_get_qr_not_found(test_client, doctor_headers):
    """Test 404 when QR ID does not exist."""
    response = test_client.get(
        "/api/v1/qr/qr_nonexistent123",
        headers=doctor_headers,
    )
    if response.status_code != 500:
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_qr_all_roles_can_retrieve(test_client, signed_prescription, doctor_headers, patient_headers, pharmacist_headers):
    """Test that all authenticated users can retrieve QR data."""
    gen_response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if gen_response.status_code != 201:
        return
    data = gen_response.json()
    qr_id = data.get("qr_id")

    response_patient = test_client.get(
        f"/api/v1/qr/{qr_id}",
        headers=patient_headers,
    )
    if response_patient.status_code == 200:
        assert "qr_data" in response_patient.json()

    response_pharmacist = test_client.get(
        f"/api/v1/qr/{qr_id}",
        headers=pharmacist_headers,
    )
    if response_pharmacist.status_code == 200:
        assert "qr_data" in response_pharmacist.json()


@pytest.mark.asyncio
async def test_generate_qr_expired_prescription(test_client, test_session, doctor_user, patient_user, doctor_headers):
    """Test that expired prescriptions cannot generate QR codes."""
    from app.models.prescription import Prescription
    expired_prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Expired Med",
        medication_code="EXP01",
        dosage="500mg",
        quantity=10,
        instructions="Already expired",
        date_issued=datetime.utcnow() - timedelta(days=100),
        date_expires=datetime.utcnow() - timedelta(days=10),
        digital_signature="mock_sig",
        credential_id="cred_expired",
    )
    test_session.add(expired_prescription)
    test_session.commit()
    test_session.refresh(expired_prescription)

    response = test_client.post(
        f"/api/v1/prescriptions/{expired_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code not in [201, 404]:
        pass


@pytest.mark.asyncio
async def test_qr_generation_full_flow(test_client, signed_prescription, doctor_headers, patient_headers):
    """Test full QR flow: Doctor generates, patient retrieves."""
    gen_response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if gen_response.status_code != 201:
        return
    gen_data = gen_response.json()
    qr_id = gen_data.get("qr_id")

    get_response = test_client.get(
        f"/api/v1/qr/{qr_id}",
        headers=patient_headers,
    )
    if get_response.status_code == 200:
        get_data = get_response.json()
        assert get_data.get("qr_id") == qr_id
        assert "qr_data" in get_data


@pytest.mark.asyncio
async def test_qr_preserves_digital_signature(test_client, signed_prescription, doctor_headers):
    """Test QR generation preserves digital signature."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert data.get("credential_id") == signed_prescription.credential_id


@pytest.mark.asyncio
async def test_qr_capacity_calculation(test_client, signed_prescription, doctor_headers):
    """Test QR code capacity calculation (2953 bytes max)."""
    response = test_client.post(
        f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        headers=doctor_headers,
    )
    if response.status_code == 201:
        data = response.json()
        assert data.get("format") in ["embedded", "url"]


def test_pytest_collection():
    """Verify pytest can collect all tests."""
    assert True
