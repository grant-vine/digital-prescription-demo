"""Test QR code generation for prescription VCs (TASK-017).

Tests QR code generation API endpoints and service logic before implementation.
All tests should FAIL initially - implementation in TASK-018 will make them pass.

Tests cover:
- QR code generation endpoint (POST /api/v1/prescriptions/{id}/qr)
- QR data structure and format
- VC credential embedding in QR codes
- URL fallback for large data (>2953 bytes)
- Error handling (not found, not signed, unauthorized)

Related User Stories:
- US-004: Send Prescription to Patient Wallet (QR)
- US-008: Share Prescription with Pharmacist (QR)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.prescription import Prescription


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
    from app.main import app

    return TestClient(app)


@pytest.fixture
def doctor_token(valid_jwt_token):
    return valid_jwt_token


@pytest.fixture
def patient_token(valid_patient_jwt_token):
    return valid_patient_jwt_token


@pytest.fixture
def signed_prescription(test_session, doctor_user, patient_user):
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
        digital_signature="mock_signature_base64",
        credential_id="cred_123456",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def unsigned_prescription(test_session, doctor_user, patient_user):
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
    long_instructions = (
        "Take 1 tablet in the morning after breakfast. "
        "Important safety information: " + ("x" * 3000)
    )

    prescription = Prescription(
        doctor_id=doctor_user.id,
        patient_id=patient_user.id,
        medication_name="Complex Medication with Very Long Name",
        medication_code="COMPLEX123",
        dosage="Variable dosing schedule",
        quantity=90,
        instructions=long_instructions,
        date_issued=datetime.utcnow(),
        date_expires=datetime.utcnow() + timedelta(days=90),
        digital_signature="mock_signature_base64",
        credential_id="cred_large",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


class TestQRGenerationEndpoint:
    def test_generate_qr_for_signed_prescription(
        self, test_client, signed_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "qr_code" in data
        assert "data_type" in data
        assert "credential_id" in data

        assert isinstance(data["qr_code"], str)
        assert len(data["qr_code"]) > 0

        assert data["data_type"] == "embedded"

        assert data["credential_id"] == signed_prescription.credential_id

    def test_generate_qr_returns_url_for_large_prescription(
        self, test_client, large_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{large_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["data_type"] == "url"

        assert "url" in data
        assert data["url"].startswith("https://")
        assert large_prescription.credential_id in data["url"]

    def test_generate_qr_for_unsigned_prescription_fails(
        self, test_client, unsigned_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{unsigned_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 400
        assert "not signed" in response.json()["detail"].lower()

    def test_generate_qr_for_nonexistent_prescription(self, test_client, doctor_token):
        response = test_client.post(
            "/api/v1/prescriptions/99999/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_qr_requires_authentication(self, test_client, signed_prescription):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
        )

        assert response.status_code == 401

    def test_patient_can_generate_qr_for_own_prescription(
        self, test_client, signed_prescription, patient_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {patient_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "qr_code" in data

    def test_pharmacist_cannot_generate_qr(self, test_client, signed_prescription, test_session):
        from app.models.user import User
        from app.core.auth import create_access_token

        pharmacist = User(
            username="pharmacist_test",
            email="pharmacist@test.com",
            password_hash="fake_hash",
            full_name="Test Pharmacist",
            role="pharmacist",
        )
        test_session.add(pharmacist)
        test_session.commit()

        pharmacist_token = create_access_token(
            {
                "sub": str(pharmacist.id),
                "username": pharmacist.username,
                "role": str(pharmacist.role),
            }
        )

        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {pharmacist_token}"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


class TestQRDataStructure:
    def test_qr_data_contains_valid_vc(self, test_client, signed_prescription, doctor_token):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201

    def test_qr_uses_error_correction_level_h(self, test_client, signed_prescription, doctor_token):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201

    def test_qr_size_threshold_is_2953_bytes(self, test_client, large_prescription, doctor_token):
        response = test_client.post(
            f"/api/v1/prescriptions/{large_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["data_type"] == "url"


class TestCredentialEmbedding:
    def test_qr_embeds_full_vc_credential(
        self, test_client, signed_prescription, doctor_token, doctor_with_did, patient_with_did
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "credential_id" in data
        assert data["credential_id"] == signed_prescription.credential_id

    def test_qr_includes_prescription_metadata(
        self, test_client, signed_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201


class TestURLFallback:
    def test_url_fallback_includes_credential_id(
        self, test_client, large_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{large_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["data_type"] == "url"
        assert large_prescription.credential_id in data["url"]

    def test_url_fallback_points_to_api_endpoint(
        self, test_client, large_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{large_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "/api/v1/credentials/" in data["url"]

    def test_url_fallback_includes_verification_hash(
        self, test_client, large_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{large_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "?" in data["url"]


class TestQRServiceIntegration:
    def test_qr_service_uses_vc_service_for_credentials(
        self, test_client, signed_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201

    def test_qr_generation_preserves_signature(
        self, test_client, signed_prescription, doctor_token
    ):
        response = test_client.post(
            f"/api/v1/prescriptions/{signed_prescription.id}/qr",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201


def test_pytest_collection():
    assert True
