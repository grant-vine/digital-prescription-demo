"""Tests for DID creation and wallet setup endpoints.

This is a TDD test suite - all tests FAIL until TASK-014 implements endpoints.
Tests cover:
- DID creation for authenticated users (POST /api/v1/dids)
- Wallet initialization (POST /api/v1/wallet/setup)
- DID resolution (GET /api/v1/dids/{user_id})
- Wallet status (GET /api/v1/wallet/status)
- Error cases: unauthorized, duplicate DID, invalid DID format
- RBAC: all roles (doctor, patient, pharmacist) can create DIDs
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES - DID data and test client
# ============================================================================


@pytest.fixture
def test_client(override_get_db, doctor_user, patient_user, pharmacist_user):
    """Create FastAPI TestClient for making requests.

    Will fail until app has DID routes.
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
def invalid_jwt_token():
    """Invalid/expired JWT token."""
    return "invalid.token.here"


@pytest.fixture
def auth_headers_invalid(invalid_jwt_token):
    """Headers with invalid JWT token."""
    return {
        "Authorization": f"Bearer {invalid_jwt_token}",
        "Content-Type": "application/json",
    }


# ============================================================================
# DID CREATION TESTS (POST /api/v1/dids)
# ============================================================================


@pytest.mark.asyncio
async def test_doctor_create_did_success(test_client, auth_headers_doctor, doctor_user):
    """Test successful DID creation for doctor role.

    EXPECTED FAILURE: Endpoint POST /api/v1/dids does not exist yet.
    Will be implemented in TASK-014.

    User Story: US-001 - Doctor Authentication & DID Setup

    Expected response (when implemented):
    {
        "did": "did:cheqd:testnet:abc123def456...",
        "user_id": 1,
        "role": "doctor",
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},  # Empty body - user identified by JWT token
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014 implements endpoint
    assert response.status_code == 201
    data = response.json()

    # DID format validation
    assert "did" in data
    assert data["did"].startswith("did:cheqd:testnet:")
    assert len(data["did"]) > 30  # Typical DID length

    # User identification
    assert data["user_id"] == doctor_user.id
    assert data["role"] == "doctor"

    # Timestamp should be present
    assert "created_at" in data


@pytest.mark.asyncio
async def test_patient_create_did_success(test_client, auth_headers_patient, patient_user):
    """Test successful DID creation for patient role.

    EXPECTED FAILURE: Endpoint does not exist yet.

    User Story: US-005 - Patient Wallet Setup & Authentication

    Expected response (when implemented):
    {
        "did": "did:cheqd:testnet:...",
        "user_id": 2,
        "role": "patient",
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_patient,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    assert "did" in data
    assert data["did"].startswith("did:cheqd:testnet:")
    assert data["user_id"] == patient_user.id
    assert data["role"] == "patient"


@pytest.mark.asyncio
async def test_pharmacist_create_did_success(
    test_client, auth_headers_pharmacist, pharmacist_user
):
    """Test successful DID creation for pharmacist role.

    EXPECTED FAILURE: Endpoint does not exist yet.

    User Story: US-009 - Pharmacist Authentication & DID Setup

    Expected response (when implemented):
    {
        "did": "did:cheqd:testnet:...",
        "user_id": 3,
        "role": "pharmacist",
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    assert "did" in data
    assert data["did"].startswith("did:cheqd:testnet:")
    assert data["user_id"] == pharmacist_user.id
    assert data["role"] == "pharmacist"


@pytest.mark.asyncio
async def test_create_did_without_authentication(test_client):
    """Test DID creation fails without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},
    )

    # FAILS until TASK-014
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_create_did_with_invalid_token(test_client, auth_headers_invalid):
    """Test DID creation fails with invalid JWT token.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Invalid authentication credentials"
    }
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_invalid,
    )

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_duplicate_did(test_client, auth_headers_doctor):
    """Test that creating a second DID for same user fails.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - First POST /api/v1/dids → 201 Created
    - Second POST /api/v1/dids → 409 Conflict
    """
    # First DID creation
    response1 = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS at this step - endpoint doesn't exist
    # When implemented, should be 201
    if response1.status_code == 201:
        # Try to create second DID with same user
        response2 = test_client.post(
            "/api/v1/dids",
            json={},
            headers=auth_headers_doctor,
        )

        # Second attempt should fail with 409 Conflict
        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_create_did_with_invalid_body(test_client, auth_headers_doctor):
    """Test DID creation with unexpected request body.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Extra fields in body should be ignored (not cause error)
    - DID created successfully with empty body
    """
    # Send extra fields that should be ignored
    response = test_client.post(
        "/api/v1/dids",
        json={"extra_field": "should_be_ignored"},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    # When implemented, should ignore extra fields and return 201
    assert response.status_code in [201, 422]


# ============================================================================
# DID RESOLUTION TESTS (GET /api/v1/dids/{user_id})
# ============================================================================


@pytest.mark.asyncio
async def test_resolve_did_by_user_id(test_client, auth_headers_doctor, doctor_user):
    """Test retrieving DID by user ID.

    EXPECTED FAILURE: Endpoint GET /api/v1/dids/{user_id} does not exist yet.

    Expected response (when implemented):
    {
        "did": "did:cheqd:testnet:...",
        "user_id": 1,
        "role": "doctor",
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    # First create a DID
    create_response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS at this step - endpoint doesn't exist
    # When implemented, create_response should be 201
    if create_response.status_code == 201:
        did_data = create_response.json()

        # Now try to resolve it
        resolve_response = test_client.get(
            f"/api/v1/dids/{doctor_user.id}",
            headers=auth_headers_doctor,
        )

        # Should return the same DID
        assert resolve_response.status_code == 200
        resolved_data = resolve_response.json()

        assert resolved_data["did"] == did_data["did"]
        assert resolved_data["user_id"] == doctor_user.id


@pytest.mark.asyncio
async def test_resolve_nonexistent_did(test_client, auth_headers_doctor):
    """Test resolving DID for user who has no DID.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "DID not found for user"
    }
    """
    # Try to resolve DID for non-existent user ID
    response = test_client.get(
        "/api/v1/dids/99999",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_resolve_did_without_authentication(test_client, doctor_user):
    """Test DID resolution fails without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get(f"/api/v1/dids/{doctor_user.id}")

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resolve_did_with_invalid_token(test_client, auth_headers_invalid):
    """Test DID resolution fails with invalid token.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.get(
        "/api/v1/dids/1",
        headers=auth_headers_invalid,
    )

    # FAILS until TASK-014
    assert response.status_code == 401


# ============================================================================
# WALLET SETUP TESTS (POST /api/v1/wallet/setup)
# ============================================================================


@pytest.mark.asyncio
async def test_wallet_setup_success(test_client, auth_headers_doctor, doctor_user):
    """Test successful wallet initialization for user.

    EXPECTED FAILURE: Endpoint POST /api/v1/wallet/setup does not exist yet.

    Expected response (when implemented):
    {
        "wallet_id": "wallet-uuid-here",
        "user_id": 1,
        "status": "active",
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    response = test_client.post(
        "/api/v1/wallet/setup",
        json={},  # Empty body - wallet for current user
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    # Wallet identification
    assert "wallet_id" in data
    assert data["user_id"] == doctor_user.id
    assert data["status"] == "active"

    # Timestamp should be present
    assert "created_at" in data


@pytest.mark.asyncio
async def test_wallet_setup_patient(test_client, auth_headers_patient, patient_user):
    """Test wallet setup for patient role.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.post(
        "/api/v1/wallet/setup",
        json={},
        headers=auth_headers_patient,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == patient_user.id
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_wallet_setup_pharmacist(
    test_client, auth_headers_pharmacist, pharmacist_user
):
    """Test wallet setup for pharmacist role.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.post(
        "/api/v1/wallet/setup",
        json={},
        headers=auth_headers_pharmacist,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == pharmacist_user.id
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_wallet_setup_without_authentication(test_client):
    """Test wallet setup fails without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.post(
        "/api/v1/wallet/setup",
        json={},
    )

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_setup_with_invalid_token(test_client, auth_headers_invalid):
    """Test wallet setup fails with invalid token.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.post(
        "/api/v1/wallet/setup",
        json={},
        headers=auth_headers_invalid,
    )

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_wallet_setup(test_client, auth_headers_doctor):
    """Test that setting up wallet twice fails gracefully.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - First POST /api/v1/wallet/setup → 201 Created
    - Second POST /api/v1/wallet/setup → 409 Conflict
    """
    # First wallet setup
    response1 = test_client.post(
        "/api/v1/wallet/setup",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS at this step - endpoint doesn't exist
    # When implemented, should be 201
    if response1.status_code == 201:
        # Try to setup wallet again
        response2 = test_client.post(
            "/api/v1/wallet/setup",
            json={},
            headers=auth_headers_doctor,
        )

        # Second attempt should fail with 409 Conflict
        assert response2.status_code == 409


# ============================================================================
# WALLET STATUS TESTS (GET /api/v1/wallet/status)
# ============================================================================


@pytest.mark.asyncio
async def test_wallet_status_success(test_client, auth_headers_doctor):
    """Test retrieving wallet status for authenticated user.

    EXPECTED FAILURE: Endpoint GET /api/v1/wallet/status does not exist yet.

    Expected response (when implemented):
    {
        "status": "active",
        "wallet_id": "wallet-uuid-here",
        "user_id": 1,
        "created_at": "2026-02-11T10:30:00Z"
    }
    """
    response = test_client.get(
        "/api/v1/wallet/status",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "active"
    assert "wallet_id" in data
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_wallet_status_without_setup(test_client, auth_headers_patient):
    """Test wallet status when wallet not yet initialized.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Wallet not initialized for user"
    }
    """
    response = test_client.get(
        "/api/v1/wallet/status",
        headers=auth_headers_patient,
    )

    # FAILS until TASK-014
    # Might be 404 (wallet not found) or 400 (wallet not initialized)
    assert response.status_code in [404, 400]


@pytest.mark.asyncio
async def test_wallet_status_without_authentication(test_client):
    """Test wallet status fails without authentication.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected response (when implemented):
    {
        "detail": "Not authenticated"
    }
    """
    response = test_client.get("/api/v1/wallet/status")

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_status_with_invalid_token(test_client, auth_headers_invalid):
    """Test wallet status fails with invalid token.

    EXPECTED FAILURE: Endpoint does not exist yet.
    """
    response = test_client.get(
        "/api/v1/wallet/status",
        headers=auth_headers_invalid,
    )

    # FAILS until TASK-014
    assert response.status_code == 401


# ============================================================================
# INTEGRATION TESTS - DID + WALLET WORKFLOW
# ============================================================================


@pytest.mark.asyncio
async def test_did_and_wallet_complete_workflow(test_client, auth_headers_doctor, doctor_user):
    """Test complete workflow: setup wallet → create DID → verify status.

    EXPECTED FAILURE: Endpoints do not exist yet.

    Expected workflow (when implemented):
    1. Setup wallet for user → 201 Created, wallet_id returned
    2. Create DID for user → 201 Created, did returned
    3. Check wallet status → 200 OK, same wallet_id
    4. Resolve DID by user_id → 200 OK, same did
    """
    # Step 1: Setup wallet
    wallet_response = test_client.post(
        "/api/v1/wallet/setup",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS at this step
    # When implemented, should be 201
    if wallet_response.status_code == 201:
        wallet_data = wallet_response.json()
        wallet_id = wallet_data["wallet_id"]

        # Step 2: Create DID
        did_response = test_client.post(
            "/api/v1/dids",
            json={},
            headers=auth_headers_doctor,
        )

        assert did_response.status_code == 201
        did_data = did_response.json()
        did = did_data["did"]

        # Step 3: Check wallet status
        status_response = test_client.get(
            "/api/v1/wallet/status",
            headers=auth_headers_doctor,
        )

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["wallet_id"] == wallet_id

        # Step 4: Resolve DID
        resolve_response = test_client.get(
            f"/api/v1/dids/{doctor_user.id}",
            headers=auth_headers_doctor,
        )

        assert resolve_response.status_code == 200
        resolved_data = resolve_response.json()
        assert resolved_data["did"] == did


@pytest.mark.asyncio
async def test_all_roles_can_create_dids(
    test_client, auth_headers_doctor, auth_headers_patient, auth_headers_pharmacist
):
    """Test that all three roles (doctor, patient, pharmacist) can create DIDs.

    EXPECTED FAILURE: Endpoint does not exist yet.

    This test verifies no role restrictions on DID creation.
    All roles should be able to create their own DIDs.
    """
    # Doctor creates DID
    doc_response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert doc_response.status_code == 201

    # Patient creates DID
    patient_response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_patient,
    )

    assert patient_response.status_code == 201

    # Pharmacist creates DID
    pharm_response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_pharmacist,
    )

    assert pharm_response.status_code == 201

    # All should have different DIDs
    doc_did = doc_response.json()["did"]
    patient_did = patient_response.json()["did"]
    pharm_did = pharm_response.json()["did"]

    assert doc_did != patient_did
    assert patient_did != pharm_did
    assert doc_did != pharm_did


@pytest.mark.asyncio
async def test_did_format_validation(test_client, auth_headers_doctor):
    """Test that DID follows expected cheqd testnet format.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected DID format: did:cheqd:testnet:[unique-identifier]
    - Must start with "did:cheqd:testnet:"
    - Should be at least 40 characters total
    - Must be URL-safe characters only
    """
    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert response.status_code == 201
    data = response.json()

    did = data["did"]

    # Format checks
    assert did.startswith("did:cheqd:testnet:")
    assert len(did) >= 40
    assert len(did) <= 200  # Sanity check - DIDs shouldn't be too long

    # Should only contain URL-safe characters: a-z, 0-9, :, -
    import re

    assert re.match(r"^did:cheqd:testnet:[a-z0-9-]+$", did), \
        f"DID {did} contains invalid characters"


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_user_id_format_in_resolve(test_client, auth_headers_doctor):
    """Test resolving DID with invalid user_id format in URL.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Non-numeric user_id should return 404 or 422
    """
    response = test_client.get(
        "/api/v1/dids/not-a-number",
        headers=auth_headers_doctor,
    )

    # FAILS until TASK-014
    assert response.status_code in [404, 422, 400]


@pytest.mark.asyncio
async def test_malformed_authorization_header(test_client):
    """Test DID creation with malformed Authorization header.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Missing "Bearer " prefix should be rejected
    - Returns 401 Unauthorized
    """
    headers = {
        "Authorization": "BadPrefix xyz123",
        "Content-Type": "application/json",
    }

    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=headers,
    )

    # FAILS until TASK-014
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_authorization_header_completely(test_client):
    """Test DID creation with no Authorization header at all.

    EXPECTED FAILURE: Endpoint does not exist yet.

    Expected behavior (when implemented):
    - Returns 401 Unauthorized
    """
    headers = {
        "Content-Type": "application/json",
    }

    response = test_client.post(
        "/api/v1/dids",
        json={},
        headers=headers,
    )

    # FAILS until TASK-014
    assert response.status_code == 401
