"""Tests for demo management API endpoints.

US-019: Demo Preparation & Test Data
Tests the demo management endpoints for seeding, resetting, and querying demo data.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.dependencies.auth import get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.models.dispensing import Dispensing
from app.models.audit import Audit


@pytest.fixture
def client(test_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def doctor_auth_header(valid_jwt_token):
    """Authorization header for doctor user."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def patient_auth_header(valid_patient_jwt_token):
    """Authorization header for patient user."""
    return {"Authorization": f"Bearer {valid_patient_jwt_token}"}


class TestDemoSeedEndpoint:
    """Tests for POST /api/v1/admin/demo/seed endpoint."""
    
    def test_seed_creates_expected_users(self, client, doctor_auth_header, test_session):
        """Test that seed creates expected number of users per role."""
        # Get counts before
        doctors_before = test_session.query(User).filter_by(role="doctor").count()
        patients_before = test_session.query(User).filter_by(role="patient").count()
        pharmacists_before = test_session.query(User).filter_by(role="pharmacist").count()
        
        response = client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["users_created"]["doctors"] == 5
        assert data["users_created"]["patients"] == 10
        assert data["users_created"]["pharmacists"] == 3
        
        # Verify counts in database
        doctors_after = test_session.query(User).filter_by(role="doctor").count()
        patients_after = test_session.query(User).filter_by(role="patient").count()
        pharmacists_after = test_session.query(User).filter_by(role="pharmacist").count()
        
        assert doctors_after == doctors_before + 5
        assert patients_after == patients_before + 10
        assert pharmacists_after == pharmacists_before + 3
    
    def test_seed_creates_prescriptions_in_all_states(self, client, doctor_auth_header, test_session):
        """Test that seed creates prescriptions in all expected states."""
        response = client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["prescriptions_created"] > 0
        
        # Check that prescriptions exist in various states
        statuses = ["DRAFT", "ACTIVE", "EXPIRED", "REVOKED", "DISPENSED"]
        for status in statuses:
            count = test_session.query(Prescription).filter_by(status=status).count()
            assert count > 0, f"No prescriptions found with status {status}"
    
    def test_seed_is_idempotent(self, client, doctor_auth_header, test_session):
        """Test that running seed twice doesn't duplicate data."""
        # First seed
        response1 = client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        assert response1.status_code == 200
        
        # Get counts after first seed
        users_after_first = test_session.query(User).count()
        prescriptions_after_first = test_session.query(Prescription).count()
        
        # Second seed (should skip existing users due to idempotency)
        response2 = client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        assert response2.status_code == 200
        
        # Counts should be the same (users already exist, so 0 new created)
        users_after_second = test_session.query(User).count()
        prescriptions_after_second = test_session.query(Prescription).count()
        
        assert users_after_second == users_after_first
        assert prescriptions_after_second == prescriptions_after_first
    
    def test_seed_requires_doctor_or_admin_role(self, client, patient_auth_header):
        """Test that seed endpoint requires doctor or admin role."""
        response = client.post("/api/v1/admin/demo/seed", headers=patient_auth_header)
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_seed_requires_authentication(self, client):
        """Test that seed endpoint requires authentication."""
        response = client.post("/api/v1/admin/demo/seed")
        
        assert response.status_code == 401


class TestDemoResetEndpoint:
    """Tests for POST /api/v1/admin/demo/reset endpoint."""
    
    def test_reset_clears_all_demo_data(self, client, doctor_auth_header, test_session):
        """Test that reset clears all demo data."""
        # First seed some data
        client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        # Verify data exists
        assert test_session.query(User).count() > 0
        assert test_session.query(Prescription).count() > 0
        
        # Reset without reseed
        response = client.post(
            "/api/v1/admin/demo/reset?confirm=true",
            headers=doctor_auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted"]["users"] > 0
        assert data["deleted"]["prescriptions"] > 0
        assert data["reseeded"] is False
        
        # Verify data is cleared (current user is preserved)
        assert test_session.query(Prescription).count() == 0
        assert test_session.query(Dispensing).count() == 0
        # User count should be 1 (the current authenticated user is preserved)
        assert test_session.query(User).count() == 1
    
    def test_reset_and_reseed(self, client, doctor_auth_header, test_session):
        """Test reset with reseed option."""
        # First seed some data
        client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        # Reset with reseed
        response = client.post(
            "/api/v1/admin/demo/reset?confirm=true&reseed=true",
            headers=doctor_auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["reseeded"] is True
        
        # Verify data exists again
        assert test_session.query(User).count() > 0
        assert test_session.query(Prescription).count() > 0
    
    def test_reset_requires_confirmation(self, client, doctor_auth_header):
        """Test that reset requires confirm=true parameter."""
        response = client.post("/api/v1/admin/demo/reset", headers=doctor_auth_header)
        
        assert response.status_code == 400
        assert "confirm=true" in response.json()["detail"]
    
    def test_reset_requires_doctor_or_admin_role(self, client, patient_auth_header):
        """Test that reset endpoint requires doctor or admin role."""
        response = client.post(
            "/api/v1/admin/demo/reset?confirm=true",
            headers=patient_auth_header
        )
        
        assert response.status_code == 403
    
    def test_reset_requires_authentication(self, client):
        """Test that reset endpoint requires authentication."""
        response = client.post("/api/v1/admin/demo/reset?confirm=true")
        
        assert response.status_code == 401


class TestDemoStatusEndpoint:
    """Tests for GET /api/v1/admin/demo/status endpoint."""
    
    def test_status_returns_correct_counts(self, client, doctor_auth_header, test_session):
        """Test that status endpoint returns correct counts."""
        # Seed some data first
        client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        response = client.get("/api/v1/admin/demo/status", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "users" in data
        assert "prescriptions" in data
        assert "dispensings" in data
        assert "audit_logs" in data
        
        # Verify counts are correct
        expected_doctors = test_session.query(User).filter_by(role="doctor").count()
        expected_patients = test_session.query(User).filter_by(role="patient").count()
        expected_pharmacists = test_session.query(User).filter_by(role="pharmacist").count()
        
        assert data["users"]["doctors"] == expected_doctors
        assert data["users"]["patients"] == expected_patients
        assert data["users"]["pharmacists"] == expected_pharmacists
        
        # Verify prescription states
        assert data["prescriptions"]["draft"] >= 0
        assert data["prescriptions"]["active"] >= 0
        assert data["prescriptions"]["expired"] >= 0
        assert data["prescriptions"]["revoked"] >= 0
        assert data["prescriptions"]["dispensed"] >= 0
        assert data["prescriptions"]["total"] > 0
    
    def test_status_with_minimal_database(self, client, doctor_auth_header):
        """Test status endpoint with minimal database (only current user)."""
        # Reset first to clear demo data (current user is preserved)
        client.post("/api/v1/admin/demo/reset?confirm=true", headers=doctor_auth_header)
        
        response = client.get("/api/v1/admin/demo/status", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        
        # Current user is preserved during reset
        assert data["users"]["total"] == 1
        assert data["prescriptions"]["total"] == 0
    
    def test_status_requires_doctor_or_admin_role(self, client, patient_auth_header):
        """Test that status endpoint requires doctor or admin role."""
        response = client.get("/api/v1/admin/demo/status", headers=patient_auth_header)
        
        assert response.status_code == 403
    
    def test_status_requires_authentication(self, client):
        """Test that status endpoint requires authentication."""
        response = client.get("/api/v1/admin/demo/status")
        
        assert response.status_code == 401


class TestDemoScenariosEndpoint:
    """Tests for GET /api/v1/admin/demo/scenarios endpoint."""
    
    def test_scenarios_returns_all_6_scenarios(self, client, doctor_auth_header):
        """Test that scenarios endpoint returns all 6 demo scenarios."""
        response = client.get("/api/v1/admin/demo/scenarios", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "scenarios" in data
        assert data["total"] == 6
        assert len(data["scenarios"]) == 6
        
        # Verify scenario structure
        for scenario in data["scenarios"]:
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "prescriptions" in scenario
    
    def test_scenarios_contains_expected_scenarios(self, client, doctor_auth_header):
        """Test that scenarios include expected demo scenarios."""
        response = client.get("/api/v1/admin/demo/scenarios", headers=doctor_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        
        scenario_names = [s["name"] for s in data["scenarios"]]
        
        expected_names = [
            "Happy Path",
            "Multi-Medication",
            "Repeat Prescription",
            "Expired Prescription",
            "Revoked Prescription",
            "Doctor Verification",
        ]
        
        for expected in expected_names:
            assert expected in scenario_names, f"Missing scenario: {expected}"
    
    def test_scenarios_requires_doctor_or_admin_role(self, client, patient_auth_header):
        """Test that scenarios endpoint requires doctor or admin role."""
        response = client.get("/api/v1/admin/demo/scenarios", headers=patient_auth_header)
        
        assert response.status_code == 403
    
    def test_scenarios_requires_authentication(self, client):
        """Test that scenarios endpoint requires authentication."""
        response = client.get("/api/v1/admin/demo/scenarios")
        
        assert response.status_code == 401


class TestDemoIntegration:
    """Integration tests for demo management workflow."""
    
    def test_full_demo_workflow(self, client, doctor_auth_header, test_session):
        """Test complete demo workflow: reset -> seed -> status -> reset -> status."""
        # Reset first to ensure clean state
        client.post("/api/v1/admin/demo/reset?confirm=true", headers=doctor_auth_header)
        
        # Verify initial status is empty
        response = client.get("/api/v1/admin/demo/status", headers=doctor_auth_header)
        initial_data = response.json()
        assert initial_data["prescriptions"]["total"] == 0
        
        # Seed data
        response = client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        assert response.status_code == 200
        seed_data = response.json()
        assert seed_data["success"] is True
        
        # Check status after seed
        response = client.get("/api/v1/admin/demo/status", headers=doctor_auth_header)
        after_seed_data = response.json()
        assert after_seed_data["prescriptions"]["total"] > 0
        assert after_seed_data["users"]["total"] > 0
        
        # Reset data
        response = client.post(
            "/api/v1/admin/demo/reset?confirm=true",
            headers=doctor_auth_header
        )
        assert response.status_code == 200
        
        # Check status after reset (current user is preserved)
        response = client.get("/api/v1/admin/demo/status", headers=doctor_auth_header)
        after_reset_data = response.json()
        assert after_reset_data["prescriptions"]["total"] == 0
        # Current user is preserved during reset
        assert after_reset_data["users"]["total"] == 1
    
    def test_scenarios_after_seed(self, client, doctor_auth_header):
        """Test that scenarios can be queried after seeding."""
        # Seed first
        client.post("/api/v1/admin/demo/seed", headers=doctor_auth_header)
        
        # Get scenarios
        response = client.get("/api/v1/admin/demo/scenarios", headers=doctor_auth_header)
        assert response.status_code == 200
        
        scenarios = response.json()["scenarios"]
        assert len(scenarios) == 6
        
        # Each scenario should have a meaningful description
        for scenario in scenarios:
            assert len(scenario["description"]) > 20
            assert len(scenario["prescriptions"]) > 0
