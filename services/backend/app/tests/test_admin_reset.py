"""Tests for admin reset-demo endpoint.

Tests the demo environment reset functionality:
- Requires confirmation parameter
- Deletes prescriptions, dispensings, and audit logs
- Keeps users, DIDs, and wallets intact
- Optional reseed functionality
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(override_get_db, doctor_user):
    """Create FastAPI TestClient for making requests."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def doctor_auth_token(test_session, doctor_user):
    """Get valid auth token for doctor user."""
    from app.core.auth import create_access_token

    token_data = {
        "sub": str(doctor_user.id),
        "username": doctor_user.username,
        "role": str(doctor_user.role),
    }
    return create_access_token(token_data)


class TestResetDemoEndpoint:
    """Tests for POST /api/v1/admin/reset-demo endpoint."""

    def test_reset_demo_without_confirmation_fails(
        self, test_client, doctor_auth_token
    ):
        """Reset without confirm=true should fail with 400 Bad Request."""
        response = test_client.post(
            "/api/v1/admin/reset-demo",
            headers={"Authorization": f"Bearer {doctor_auth_token}"},
        )

        assert response.status_code == 400
        assert "confirm=true" in response.json()["detail"]

    def test_reset_demo_with_false_confirmation_fails(
        self, test_client, doctor_auth_token
    ):
        """Reset with confirm=false should fail with 400 Bad Request."""
        response = test_client.post(
            "/api/v1/admin/reset-demo?confirm=false",
            headers={"Authorization": f"Bearer {doctor_auth_token}"},
        )

        assert response.status_code == 400
        assert "confirm=true" in response.json()["detail"]

    def test_reset_demo_without_auth_fails(self, test_client):
        """Reset without authentication should fail with 401 Unauthorized."""
        response = test_client.post(
            "/api/v1/admin/reset-demo?confirm=true",
        )

        assert response.status_code == 401

    def test_reset_demo_with_valid_confirmation_succeeds(
        self,
        test_client,
        test_session,
        doctor_user,
        patient_user,
        doctor_auth_token,
    ):
        """Reset with confirm=true should clear data and return success."""
        from datetime import datetime, timedelta
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing
        from app.models.audit import Audit

        prescription = Prescription(
            doctor_id=doctor_user.id,
            patient_id=patient_user.id,
            medication_name="Test Medication",
            medication_code="TEST001",
            dosage="10mg",
            quantity=30,
            instructions="Take once daily",
            date_issued=datetime.utcnow(),
            date_expires=datetime.utcnow() + timedelta(days=30),
            is_repeat=False,
            repeat_count=0,
        )
        test_session.add(prescription)
        test_session.commit()

        initial_prescriptions = test_session.query(Prescription).count()
        assert initial_prescriptions > 0

        response = test_client.post(
            "/api/v1/admin/reset-demo?confirm=true",
            headers={"Authorization": f"Bearer {doctor_auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted"]["prescriptions"] == initial_prescriptions
        assert data["deleted"]["dispensings"] >= 0
        assert data["deleted"]["audit_logs"] >= 0
        assert "Demo environment reset successfully" in data["message"]

        assert test_session.query(Prescription).count() == 0
        assert test_session.query(Dispensing).count() == 0

    def test_reset_demo_preserves_users(
        self, test_client, test_session, doctor_user, patient_user, doctor_auth_token
    ):
        """Reset should preserve user records."""
        from app.models.user import User

        initial_users = test_session.query(User).count()

        test_client.post(
            "/api/v1/admin/reset-demo?confirm=true",
            headers={"Authorization": f"Bearer {doctor_auth_token}"},
        )

        final_users = test_session.query(User).count()
        assert final_users == initial_users
        assert test_session.query(User).filter(User.id == doctor_user.id).first()
        assert test_session.query(User).filter(User.id == patient_user.id).first()

    def test_patient_cannot_reset_demo(self, test_client, patient_user):
        """Patients should not be able to reset demo (only doctor/admin)."""
        from app.core.auth import create_access_token

        token_data = {
            "sub": str(patient_user.id),
            "username": patient_user.username,
            "role": str(patient_user.role),
        }
        patient_token = create_access_token(token_data)

        response = test_client.post(
            "/api/v1/admin/reset-demo?confirm=true",
            headers={"Authorization": f"Bearer {patient_token}"},
        )

        assert response.status_code == 403
        assert "doctor" in response.json()["detail"].lower()

    def test_response_schema_is_valid(
        self, test_client, doctor_user, doctor_auth_token
    ):
        """Response should match ResetDemoResponse schema."""
        response = test_client.post(
            "/api/v1/admin/reset-demo?confirm=true",
            headers={"Authorization": f"Bearer {doctor_auth_token}"},
        )

        data = response.json()
        assert "success" in data
        assert "deleted" in data
        assert "reseeded" in data
        assert "message" in data
        assert isinstance(data["deleted"], dict)
        assert "prescriptions" in data["deleted"]
        assert "dispensings" in data["deleted"]
        assert "audit_logs" in data["deleted"]
