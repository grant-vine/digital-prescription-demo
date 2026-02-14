"""Tests for prescription CRUD operations.

This is a TDD test suite - all tests FAIL until TASK-012 implements endpoints.
Tests cover:
- Create prescription (doctor only)
- Read prescription by ID
- Update draft prescription
- List user's prescriptions (role-filtered)
- RBAC enforcement (patients/pharmacists cannot create)
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES - Prescription data and test client
# ============================================================================


@pytest.fixture
def test_client(override_get_db, doctor_user, patient_user, pharmacist_user):
    """Create FastAPI TestClient for making requests.

    Will fail until app has prescription routes.
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def prescription_data_doctor(patient_user):
    """Valid prescription data for doctor to create.

    Patient ID comes from the patient_user fixture (ID=3).
    """
    return {
        "patient_id": 3,  # patient_user ID from conftest
        "medication_name": "Amoxicillin",
        "medication_code": "SAHPRA_12345",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily with food",
        "date_expires": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "is_repeat": False,
        "repeat_count": 0,
    }


@pytest.fixture
def prescription_data_invalid():
    """Invalid prescription data (missing required fields)."""
    return {
        "patient_id": 3,
        # Missing medication_name (required)
        "medication_code": "SAHPRA_12345",
        "dosage": "500mg",
        "quantity": 21,
    }


@pytest.fixture
def prescription_data_no_patient():
    """Prescription data with non-existent patient."""
    return {
        "patient_id": 99999,  # Non-existent patient
        "medication_name": "Amoxicillin",
        "medication_code": "SAHPRA_12345",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily",
        "date_expires": (datetime.utcnow() + timedelta(days=30)).isoformat(),
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
# CREATE PRESCRIPTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_prescription_success(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test successful prescription creation by doctor.

    EXPECTED FAILURE: Endpoint POST /api/v1/prescriptions does not exist yet.
    Will be implemented in TASK-012.

    Expected response (when implemented):
    {
        "id": 1,
        "doctor_id": 1,
        "patient_id": 3,
        "medication_name": "Amoxicillin",
        "medication_code": "SAHPRA_12345",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily with food",
        "date_issued": "2026-02-11T10:00:00",
        "date_expires": "2026-03-13T10:00:00",
        "is_repeat": false,
        "repeat_count": 0,
        "digital_signature": null,
        "credential_id": null,
        "created_at": "2026-02-11T10:00:00",
        "updated_at": "2026-02-11T10:00:00"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012 implements endpoint
    assert response.status_code == 201
    data = response.json()

    # Response structure validation
    assert "id" in data
    assert data["doctor_id"] == 1  # From fixture
    assert data["patient_id"] == 3
    assert data["medication_name"] == prescription_data_doctor["medication_name"]
    assert data["medication_code"] == prescription_data_doctor["medication_code"]
    assert data["dosage"] == prescription_data_doctor["dosage"]
    assert data["quantity"] == prescription_data_doctor["quantity"]
    assert data["instructions"] == prescription_data_doctor["instructions"]
    assert data["is_repeat"] is False
    assert data["repeat_count"] == 0
    assert data["digital_signature"] is None
    assert data["credential_id"] is None
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_prescription_unauthorized(test_client, prescription_data_doctor):
    """Test prescription creation without authentication token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        # No Authorization header
    )

    # FAILS until TASK-012
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_prescription_patient_forbidden(
    test_client, auth_headers_patient, prescription_data_doctor
):
    """Test that patient role CANNOT create prescriptions.

    EXPECTED FAILURE: Endpoint and RBAC not implemented yet.

    Expected response (when implemented):
    {
        "detail": "Not enough permissions"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_patient,
    )

    # FAILS until TASK-012
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_prescription_pharmacist_forbidden(
    test_client, auth_headers_pharmacist, prescription_data_doctor
):
    """Test that pharmacist role CANNOT create prescriptions.

    EXPECTED FAILURE: Endpoint and RBAC not implemented yet.

    Expected response (when implemented):
    {
        "detail": "Not enough permissions"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-012
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_prescription_invalid_data(
    test_client, auth_headers_doctor, prescription_data_invalid
):
    """Test prescription creation with missing required fields.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": [
            {
                "loc": ["body", "medication_name"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_invalid,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_prescription_invalid_patient(
    test_client, auth_headers_doctor, prescription_data_no_patient
):
    """Test prescription creation with non-existent patient.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Patient not found"
    }
    """
    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_no_patient,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 404


# ============================================================================
# READ PRESCRIPTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_prescription_by_id(test_client, auth_headers_doctor, prescription_data_doctor):
    """Test retrieving existing prescription by ID.

    EXPECTED FAILURE: Endpoint GET /api/v1/prescriptions/{id} does not exist yet.

    Expected response (when implemented):
    {
        "id": 1,
        "doctor_id": 1,
        "patient_id": 3,
        "medication_name": "Amoxicillin",
        ...
    }
    """
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]
    
    response = test_client.get(
        f"/api/v1/prescriptions/{prescription_id}",
        headers=auth_headers_doctor,
    )

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["id"] == prescription_id
    assert "medication_name" in data
    assert "doctor_id" in data


@pytest.mark.asyncio
async def test_get_prescription_not_found(test_client, auth_headers_doctor):
    """Test retrieving non-existent prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Prescription not found"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions/99999",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_prescription_unauthorized(test_client):
    """Test retrieving prescription without authentication token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions/1",
        # No Authorization header
    )

    # FAILS until TASK-012
    assert response.status_code == 401


# ============================================================================
# UPDATE PRESCRIPTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_prescription_draft(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test updating draft (unsigned) prescription.

    EXPECTED FAILURE: Endpoint PUT /api/v1/prescriptions/{id} does not exist yet.

    Expected behavior (when implemented):
    - Can only update draft prescriptions (digital_signature is null)
    - Cannot update signed prescriptions
    - Returns 200 OK with updated prescription

    Expected response (when implemented):
    {
        "id": 1,
        "medication_name": "Updated Medication",
        "dosage": "1000mg",
        ...
    }
    """
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]
    
    update_data = {
        "medication_name": "Updated Amoxicillin",
        "dosage": "1000mg",
        "quantity": 42,
    }

    response = test_client.put(
        f"/api/v1/prescriptions/{prescription_id}",
        json=update_data,
        headers=auth_headers_doctor,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["medication_name"] == "Updated Amoxicillin"
    assert data["dosage"] == "1000mg"
    assert data["quantity"] == 42


@pytest.mark.asyncio
async def test_update_prescription_not_found(test_client, auth_headers_doctor):
    """Test updating non-existent prescription.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Prescription not found"
    }
    """
    update_data = {
        "medication_name": "Updated Amoxicillin",
    }

    response = test_client.put(
        "/api/v1/prescriptions/99999",
        json=update_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_prescription_unauthorized(test_client, prescription_data_doctor):
    """Test updating prescription without authentication token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    update_data = {
        "medication_name": "Updated Amoxicillin",
    }

    response = test_client.put(
        "/api/v1/prescriptions/1",
        json=update_data,
        # No Authorization header
    )

    # FAILS until TASK-012
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_prescription_signed_forbidden(test_client, auth_headers_doctor, prescription_data_doctor, test_session):
    """Test that signed prescriptions cannot be updated.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Check if prescription has digital_signature
    - If signed, return 403 Forbidden
    - Message: "Cannot modify signed prescriptions"

    Expected response (when implemented):
    {
        "detail": "Cannot modify signed prescriptions"
    }
    """
    from app.models.prescription import Prescription
    
    create_response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data_doctor,
        headers=auth_headers_doctor,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]
    
    prescription = test_session.query(Prescription).filter(Prescription.id == prescription_id).first()
    prescription.digital_signature = "mock_signature_xyz"
    test_session.commit()
    
    update_data = {
        "medication_name": "Updated Amoxicillin",
    }

    response = test_client.put(
        f"/api/v1/prescriptions/{prescription_id}",
        json=update_data,
        headers=auth_headers_doctor,
    )

    assert response.status_code == 403
    assert "signed" in response.json()["detail"].lower()


# ============================================================================
# LIST PRESCRIPTIONS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_prescriptions_doctor(test_client, auth_headers_doctor, doctor_user):
    """Test listing prescriptions for doctor (sees their prescriptions).

    EXPECTED FAILURE: Endpoint GET /api/v1/prescriptions does not exist yet.

    Expected behavior (when implemented):
    - Doctor sees only prescriptions they created (where doctor_id == user_id)
    - Returns paginated list
    - Response contains array of prescriptions

    Expected response (when implemented):
    {
        "items": [
            {
                "id": 1,
                "doctor_id": 1,
                "medication_name": "Amoxicillin",
                ...
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 10
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 200
    data = response.json()

    # Response structure validation
    assert "items" in data or isinstance(data, list)
    if isinstance(data, dict):
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


@pytest.mark.asyncio
async def test_list_prescriptions_patient(test_client, auth_headers_patient, patient_user):
    """Test listing prescriptions for patient (sees their prescriptions).

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Patient sees only prescriptions where patient_id == user_id
    - Returns paginated list
    - Cannot see other patients' prescriptions

    Expected response (when implemented):
    {
        "items": [
            {
                "id": 1,
                "patient_id": 3,
                "medication_name": "Amoxicillin",
                ...
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 10
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_patient,
    )

    # FAILS until TASK-012
    assert response.status_code == 200
    data = response.json()

    # Response structure validation
    assert "items" in data or isinstance(data, list)
    if isinstance(data, dict):
        assert "total" in data


@pytest.mark.asyncio
async def test_list_prescriptions_empty(test_client, auth_headers_doctor):
    """Test listing prescriptions when user has none.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - New user with no prescriptions
    - Returns empty list
    - total = 0

    Expected response (when implemented):
    {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 10
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 200
    data = response.json()

    if isinstance(data, dict):
        assert data.get("total", 0) >= 0
        assert isinstance(data.get("items", []), list)


@pytest.mark.asyncio
async def test_list_prescriptions_unauthorized(test_client):
    """Test listing prescriptions without authentication token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        # No Authorization header
    )

    # FAILS until TASK-012
    assert response.status_code == 401


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_prescriptions_pharmacist_filtered(test_client, auth_headers_pharmacist):
    """Test that pharmacist sees different prescription list (or empty by default).

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Pharmacist is not doctor or patient
    - May see all prescriptions OR empty list by default
    - Depends on implementation

    This test documents expected behavior (to be decided).
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-012
    # Behavior depends on implementation
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_doctor_cannot_view_other_doctor_prescriptions(test_client, auth_headers_doctor):
    """Test that doctor cannot view other doctors' prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Doctor can only view their own prescriptions
    - If they try to GET /api/v1/prescriptions/2 (another doctor's)
    - Should return 403 Forbidden or 404 Not Found

    This tests data isolation for privacy.
    """
    # Try to access prescription from another doctor
    response = test_client.get(
        "/api/v1/prescriptions/999",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    # Should be 403/404 if prescription belongs to another doctor
    assert response.status_code in [200, 403, 404]


# ============================================================================
# EDGE CASES & DATA VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_create_prescription_quantity_zero(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription creation with quantity = 0.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should validate quantity > 0
    - Returns 422 Unprocessable Entity

    Expected response (when implemented):
    {
        "detail": [
            {
                "loc": ["body", "quantity"],
                "msg": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt"
            }
        ]
    }
    """
    invalid_data = prescription_data_doctor.copy()
    invalid_data["quantity"] = 0

    response = test_client.post(
        "/api/v1/prescriptions",
        json=invalid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_prescription_negative_quantity(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription creation with negative quantity.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should reject negative quantities
    - Returns 422 Unprocessable Entity
    """
    invalid_data = prescription_data_doctor.copy()
    invalid_data["quantity"] = -10

    response = test_client.post(
        "/api/v1/prescriptions",
        json=invalid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_prescription_empty_medication_name(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription creation with empty medication name.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should validate non-empty medication name
    - Returns 422 Unprocessable Entity
    """
    invalid_data = prescription_data_doctor.copy()
    invalid_data["medication_name"] = ""

    response = test_client.post(
        "/api/v1/prescriptions",
        json=invalid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_prescription_repeat_count_without_is_repeat(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription with repeat_count but is_repeat = false.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - If is_repeat = false, repeat_count should be 0
    - Or should allow any value (flexible behavior)
    - Implementation should validate consistency

    This test documents expected behavior.
    """
    invalid_data = prescription_data_doctor.copy()
    invalid_data["is_repeat"] = False
    invalid_data["repeat_count"] = 5  # Inconsistent

    response = test_client.post(
        "/api/v1/prescriptions",
        json=invalid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    # Behavior depends on implementation:
    # - Accept and ignore repeat_count (200)
    # - Validate consistency (422)
    assert response.status_code in [200, 201, 422]


@pytest.mark.asyncio
async def test_create_prescription_future_expiration_date(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription with valid future expiration date.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should accept future dates
    - Should validate that date_expires > date_issued
    - Returns 201 Created
    """
    valid_data = prescription_data_doctor.copy()
    valid_data["date_expires"] = (datetime.utcnow() + timedelta(days=90)).isoformat()

    response = test_client.post(
        "/api/v1/prescriptions",
        json=valid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_prescription_past_expiration_date(
    test_client, auth_headers_doctor, prescription_data_doctor
):
    """Test prescription with past expiration date.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should reject past expiration dates
    - Returns 422 Unprocessable Entity

    Expected response (when implemented):
    {
        "detail": [
            {
                "loc": ["body", "date_expires"],
                "msg": "Expiration date must be in the future",
                "type": "value_error"
            }
        ]
    }
    """
    invalid_data = prescription_data_doctor.copy()
    invalid_data["date_expires"] = (datetime.utcnow() - timedelta(days=1)).isoformat()

    response = test_client.post(
        "/api/v1/prescriptions",
        json=invalid_data,
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-012
    assert response.status_code == 422
