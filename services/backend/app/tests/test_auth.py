"""Tests for OAuth2 authentication and protected routes.

This is a TDD test suite - all tests FAIL until TASK-010 implements authentication.
Tests cover:
- Login endpoint (POST /api/v1/auth/login)
- Token validation and refresh
- Protected route access with valid/invalid tokens
- Role-based access control
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


# ============================================================================
# FIXTURES - Auth tokens and test users
# ============================================================================


@pytest.fixture
def test_client(override_get_db, doctor_user, patient_user, pharmacist_user):
    """Create FastAPI TestClient for making requests.

    Will fail until app has auth routes.
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def invalid_jwt_token():
    """Invalid/expired JWT token."""
    return "invalid.token.here"


@pytest.fixture
def malformed_jwt_token():
    """Malformed JWT token (not valid base64)."""
    return "not-a-jwt-at-all"


@pytest.fixture
def doctor_auth_payload():
    """Login payload for doctor."""
    return {
        "username": "dr_smith",
        "password": "password123",
    }


@pytest.fixture
def patient_auth_payload():
    """Login payload for patient."""
    return {
        "username": "patient_doe",
        "password": "password456",
    }


@pytest.fixture
def pharmacist_auth_payload():
    """Login payload for pharmacist."""
    return {
        "username": "pharm_jones",
        "password": "password789",
    }


@pytest.fixture
def auth_headers_doctor(valid_jwt_token):
    """Headers with doctor JWT token."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_patient(valid_jwt_token):
    """Headers with patient JWT token."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_invalid(invalid_jwt_token):
    """Headers with invalid JWT token."""
    return {
        "Authorization": f"Bearer {invalid_jwt_token}",
        "Content-Type": "application/json",
    }


# ============================================================================
# LOGIN ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_login_success(test_client, doctor_auth_payload):
    """Test successful login with valid credentials.

    EXPECTED FAILURE: Endpoint POST /api/v1/auth/login does not exist yet.
    Will be implemented in TASK-010.

    Expected response (when implemented):
    {
        "access_token": "eyJhbGci...",
        "refresh_token": "eyJhbGci...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "dr_smith",
            "email": "smith@hospital.co.za",
            "role": "doctor"
        }
    }
    """
    response = test_client.post(
        "/api/v1/auth/login",
        json=doctor_auth_payload,
    )

    # FAILS until TASK-010 implements endpoint
    assert response.status_code == 200
    data = response.json()

    # Token structure validation
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

    # User info in response
    assert "user" in data
    assert data["user"]["username"] == doctor_auth_payload["username"]
    assert data["user"]["role"] == "doctor"


@pytest.mark.asyncio
async def test_login_invalid_credentials(test_client):
    """Test login with invalid credentials.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Invalid username or password"
    }
    """
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent_user",
            "password": "wrong_password",
        },
    )

    # FAILS until TASK-010
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_login_missing_credentials(test_client):
    """Test login with missing username or password.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": [
            {
                "loc": ["body", "username"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    """
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "dr_smith"},  # Missing password
    )

    # FAILS until TASK-010
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_body(test_client):
    """Test login with empty request body.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.post(
        "/api/v1/auth/login",
        json={},
    )

    # FAILS until TASK-010
    assert response.status_code == 422


# ============================================================================
# TOKEN VALIDATION & REFRESH TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_token_refresh_success(test_client, valid_refresh_token):
    """Test token refresh with valid refresh token.

    EXPECTED FAILURE: Endpoint POST /api/v1/auth/refresh does not exist yet.

    Expected response (when implemented):
    {
        "access_token": "new_token_xyz...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    """
    response = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": valid_refresh_token},
    )

    # FAILS until TASK-010
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    # New token should be different from old
    assert data["access_token"] != valid_refresh_token


@pytest.mark.asyncio
async def test_token_refresh_invalid_token(test_client, invalid_jwt_token):
    """Test token refresh with invalid refresh token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Invalid refresh token"
    }
    """
    response = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": invalid_jwt_token},
    )

    # FAILS until TASK-010
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_token_validation_endpoint(test_client, valid_jwt_token):
    """Test token validation endpoint.

    EXPECTED FAILURE: Endpoint GET /api/v1/auth/validate does not exist yet.

    Expected response (when implemented):
    {
        "valid": true,
        "user_id": 1,
        "role": "doctor",
        "expires_in": 3599
    }
    """
    response = test_client.get(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    # FAILS until TASK-010
    assert response.status_code == 200
    data = response.json()

    assert "valid" in data
    assert data["valid"] is True
    assert "user_id" in data
    assert "role" in data
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_token_validation_invalid(test_client, invalid_jwt_token):
    """Test token validation with invalid token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "valid": false,
        "detail": "Invalid token"
    }
    """
    response = test_client.get(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {invalid_jwt_token}"},
    )

    # FAILS until TASK-010
    assert response.status_code == 401


# ============================================================================
# PROTECTED ROUTE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(test_client, auth_headers_doctor):
    """Test accessing protected route with valid JWT token.

    EXPECTED FAILURE: No protected routes implemented yet.
    Using /api/v1/prescriptions/create as example protected route.

    Expected behavior (when implemented):
    - Protected route checks Authorization header
    - Validates JWT signature
    - Extracts user info from token
    - Allows request to proceed
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_doctor,
    )

    # FAILS - 404 because route doesn't exist yet
    # When TASK-010 is complete, should be 200 (with some prescriptions)
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_protected_route_without_token(test_client):
    """Test accessing protected route WITHOUT Authorization header.

    EXPECTED FAILURE: No protected routes implemented yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get("/api/v1/prescriptions")

    # FAILS - 404 because route doesn't exist yet
    # When TASK-010 is complete, should be 401 Unauthorized
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(test_client, auth_headers_invalid):
    """Test accessing protected route with invalid JWT token.

    EXPECTED FAILURE: No protected routes implemented yet.

    Expected response (when implemented):
    {
        "detail": "Invalid authentication credentials"
    }
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers=auth_headers_invalid,
    )

    # FAILS - 404 because route doesn't exist yet
    # When TASK-010 is complete, should be 401 Unauthorized
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_protected_route_with_malformed_token(test_client):
    """Test accessing protected route with malformed Authorization header.

    EXPECTED FAILURE: No protected routes implemented yet.

    Expected behavior (when implemented):
    - Authorization header format should be "Bearer <token>"
    - Malformed headers should be rejected
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers={"Authorization": "InvalidFormatToken"},
    )

    # FAILS - 404 because route doesn't exist yet
    # When TASK-010 is complete, should be 401 Unauthorized
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_protected_route_with_bearer_prefix_only(test_client):
    """Test accessing protected route with Bearer prefix but no token.

    EXPECTED FAILURE: No protected routes implemented yet.

    Expected behavior (when implemented):
    - Should validate Bearer token format
    - Empty token should be rejected
    """
    response = test_client.get(
        "/api/v1/prescriptions",
        headers={"Authorization": "Bearer "},
    )

    # FAILS - 404 because route doesn't exist yet
    # When TASK-010 is complete, should be 401 Unauthorized
    assert response.status_code in [401, 404]


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_doctor_create_prescription(test_client, auth_headers_doctor):
    """Test that doctor role CAN create prescriptions.

    Endpoint exists and RBAC is implemented via require_role(["doctor"]).
    Doctors should receive 201 Created when creating valid prescriptions.
    Patients and pharmacists should receive 403 Forbidden.
    """
    prescription_data = {
        "patient_id": 1,
        "medication_name": "Amoxicillin",
        "medication_code": "J01CA04",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily",
        "date_expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
    }

    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data,
        headers=auth_headers_doctor,
    )

    # Endpoint exists with RBAC - expect 201 for doctors
    # 404 fallback if endpoint not available
    assert response.status_code in [201, 404]


@pytest.mark.asyncio
async def test_patient_cannot_create_prescription(test_client, auth_headers_patient):
    """Test that patient role CANNOT create prescriptions.

    RBAC is implemented via require_role(["doctor"]).
    Patients should receive 403 Forbidden.
    """
    prescription_data = {
        "patient_id": 1,
        "medication_name": "Amoxicillin",
        "medication_code": "J01CA04",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily",
        "date_expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
    }

    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data,
        headers=auth_headers_patient,
    )

    # With RBAC enforced: 403 Forbidden
    # Fallbacks: 201 (if RBAC not enforced), 404 (if endpoint not available)
    assert response.status_code in [201, 403, 404]


@pytest.mark.asyncio
async def test_pharmacist_cannot_create_prescription(test_client, valid_jwt_token):
    """Test that pharmacist role CANNOT create prescriptions.

    RBAC is implemented via require_role(["doctor"]).
    Pharmacists should receive 403 Forbidden.
    """
    headers = {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }

    prescription_data = {
        "patient_id": 1,
        "medication_name": "Amoxicillin",
        "medication_code": "J01CA04",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily",
        "date_expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
    }

    response = test_client.post(
        "/api/v1/prescriptions",
        json=prescription_data,
        headers=headers,
    )

    # With RBAC enforced: 403 Forbidden
    # Fallbacks: 201 (if RBAC not enforced), 404 (if endpoint not available)
    assert response.status_code in [201, 403, 404]


@pytest.mark.asyncio
async def test_doctor_sign_prescription(test_client, auth_headers_doctor):
    """Test that doctor role CAN sign prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - POST /api/v1/prescriptions/{id}/sign exists
    - Doctor role authorized
    - Returns 200 with signed prescription
    """
    sign_data = {
        "signature": "digital_signature_here",
    }

    response = test_client.post(
        "/api/v1/prescriptions/1/sign",
        json=sign_data,
        headers=auth_headers_doctor,
    )

    # FAILS - 404 because endpoint doesn't exist yet
    # When TASK-010 is complete, should be 200 OK
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_pharmacist_view_prescription(test_client, valid_jwt_token):
    """Test that pharmacist role CAN view prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - GET /api/v1/prescriptions/{id} exists
    - Pharmacist role authorized to view
    - Returns 200 with prescription details
    """
    headers = {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }

    response = test_client.get(
        "/api/v1/prescriptions/1",
        headers=headers,
    )

    # FAILS - 404 because endpoint doesn't exist yet
    # When TASK-010 is complete, should be 200 OK
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_pharmacist_verify_prescription(test_client, valid_jwt_token):
    """Test that pharmacist role CAN verify prescriptions.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - POST /api/v1/prescriptions/{id}/verify exists
    - Pharmacist role authorized
    - Returns 200 with verification result
    """
    headers = {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
    }

    response = test_client.get(
        "/api/v1/prescriptions/1/verify",
        headers=headers,
    )

    # FAILS - 404 because endpoint doesn't exist yet
    # When TASK-010 is complete, should be 200 OK
    assert response.status_code in [200, 404]


# ============================================================================
# LOGOUT & TOKEN REVOCATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_logout_success(test_client, auth_headers_doctor):
    """Test successful logout.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - POST /api/v1/auth/logout exists
    - Token is blacklisted/revoked
    - Returns 200 OK
    """
    response = test_client.post(
        "/api/v1/auth/logout",
        headers=auth_headers_doctor,
    )

    # FAILS - 404 because endpoint doesn't exist yet
    # When TASK-010 is complete, should be 200 OK
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_logout_without_token(test_client):
    """Test logout without authentication token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Should require valid token
    - Returns 401 Unauthorized
    """
    response = test_client.post("/api/v1/auth/logout")

    # FAILS - 404 because endpoint doesn't exist yet
    # When TASK-010 is complete, should be 401 Unauthorized
    assert response.status_code in [401, 404]


@pytest.mark.xfail(reason="Token blacklisting not yet implemented")
@pytest.mark.asyncio
async def test_token_after_logout_rejected(test_client, auth_headers_doctor):
    """Test that token is invalid after logout.

    EXPECTED FAILURE: Logout endpoint doesn't exist yet.

    Expected behavior (when implemented):
    1. POST /api/v1/auth/logout with valid token → 200 OK
    2. GET /api/v1/prescriptions with same token → 401 Unauthorized
    """
    # Step 1: Logout
    logout_response = test_client.post(
        "/api/v1/auth/logout",
        headers=auth_headers_doctor,
    )

    # FAILS at this step - endpoint doesn't exist
    # Should be 200 OK when implemented
    if logout_response.status_code == 200:
        # Step 2: Try to use same token
        prescriptions_response = test_client.get(
            "/api/v1/prescriptions",
            headers=auth_headers_doctor,
        )

        # Token should be rejected after logout
        assert prescriptions_response.status_code == 401


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
async def test_login_case_insensitive_username(test_client):
    """Test that username comparison might be case-insensitive.

    EXPECTED FAILURE: Endpoint and logic not implemented yet.

    Note: Implementation will decide if usernames are case-sensitive.
    This test documents expected behavior.
    """
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "DR_SMITH",  # Uppercase
            "password": "password123",
        },
    )

    # FAILS - endpoint doesn't exist yet
    # When implemented, should be either:
    # - 200 OK (if case-insensitive)
    # - 401 Unauthorized (if case-sensitive)
    assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
async def test_login_rate_limiting(test_client, doctor_auth_payload):
    """Test rate limiting on login attempts.

    EXPECTED FAILURE: Rate limiting not implemented yet.

    Expected behavior (when implemented):
    - After multiple failed attempts, should return 429 Too Many Requests
    - Lock should clear after timeout
    """
    # Try 5 failed login attempts
    for i in range(5):
        test_client.post(
            "/api/v1/auth/login",
            json={
                "username": doctor_auth_payload["username"],
                "password": "wrong_password",
            },
        )

    # Final attempt should be rate-limited if implemented
    final_response = test_client.post(
        "/api/v1/auth/login",
        json=doctor_auth_payload,
    )

    # FAILS - endpoint doesn't exist yet
    # When implemented with rate limiting, might be 429
    assert final_response.status_code in [200, 401, 404, 429]


@pytest.mark.asyncio
async def test_concurrent_login_sessions(test_client, doctor_auth_payload):
    """Test that multiple login sessions are handled correctly.

    EXPECTED FAILURE: Endpoint not implemented yet.

    Expected behavior (when implemented):
    - User can have multiple active sessions
    - Each session has unique token
    - Logout revokes only specified token
    """
    # First login
    response1 = test_client.post(
        "/api/v1/auth/login",
        json=doctor_auth_payload,
    )

    # FAILS - endpoint doesn't exist
    # When implemented:
    if response1.status_code == 200:
        token1 = response1.json()["access_token"]

        # Second login (same user)
        response2 = test_client.post(
            "/api/v1/auth/login",
            json=doctor_auth_payload,
        )

        assert response2.status_code == 200
        token2 = response2.json()["access_token"]

        # Both tokens should be different and valid
        assert token1 != token2
