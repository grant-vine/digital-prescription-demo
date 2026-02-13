"""Unit tests for DemoACAPyService.

Tests the demo mode HMAC-SHA256 signing/verification service that replaces
ACA-Py when USE_DEMO=true. Validates:
- Wallet/DID creation returns valid formats
- Issue credential produces W3C VC with HMAC-SHA256 proof
- Verify credential validates genuine signatures
- Verify credential rejects tampered credentials
- Full sign→verify round-trip
- Async context manager protocol
"""

import pytest
import json
import copy

from app.services.demo_acapy import DemoACAPyService, DEMO_HMAC_SECRET


@pytest.fixture
def demo_service():
    """Create DemoACAPyService instance."""
    return DemoACAPyService()


@pytest.fixture
def sample_credential():
    """Sample unsigned W3C VC for signing tests."""
    return {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "PrescriptionCredential"],
        "issuer": "did:cheqd:testnet:demo-doctor-123",
        "issuanceDate": "2026-02-12T10:00:00Z",
        "expirationDate": "2026-05-12T23:59:59Z",
        "credentialSubject": {
            "id": "did:cheqd:testnet:demo-patient-456",
            "prescription": {
                "id": 1,
                "medication_name": "Amoxicillin",
                "medication_code": "J01CA04",
                "dosage": "500mg",
                "quantity": 21,
                "instructions": "Take one tablet three times daily",
                "date_issued": "2026-02-12T10:00:00Z",
            },
        },
    }


# ============================================================================
# WALLET & DID CREATION
# ============================================================================


@pytest.mark.asyncio
async def test_create_wallet_returns_valid_did(demo_service):
    """Test create_wallet returns dict with valid DID format."""
    result = await demo_service.create_wallet()

    assert "did" in result
    assert result["did"].startswith("did:cheqd:testnet:demo-")
    assert "verkey" in result
    assert result["verkey"].startswith("demo-verkey-")
    assert result["public"] is True


@pytest.mark.asyncio
async def test_create_wallet_unique_dids(demo_service):
    """Test create_wallet generates unique DIDs each call."""
    result1 = await demo_service.create_wallet()
    result2 = await demo_service.create_wallet()

    assert result1["did"] != result2["did"]
    assert result1["verkey"] != result2["verkey"]


@pytest.mark.asyncio
async def test_create_did_returns_valid_format(demo_service):
    """Test create_did returns dict with valid DID format."""
    result = await demo_service.create_did()

    assert "did" in result
    assert result["did"].startswith("did:cheqd:testnet:demo-")
    assert "verkey" in result
    assert "public" in result
    assert result["public"] is True
    assert result["method"] == "cheqd:testnet"


@pytest.mark.asyncio
async def test_create_did_custom_params(demo_service):
    """Test create_did accepts custom method and public params."""
    result = await demo_service.create_did(method="custom:method", public=False)

    assert result["method"] == "custom:method"
    assert result["public"] is False


@pytest.mark.asyncio
async def test_get_wallet_status(demo_service):
    """Test get_wallet_status returns demo status info."""
    result = await demo_service.get_wallet_status()

    assert result["version"] == "demo-1.0.0"
    assert result["label"] == "rx-demo"
    assert "wallet" in result


# ============================================================================
# CREDENTIAL ISSUANCE
# ============================================================================


@pytest.mark.asyncio
async def test_issue_credential_returns_signed_vc(demo_service, sample_credential):
    """Test issue_credential produces signed VC with HMAC proof."""
    result = await demo_service.issue_credential(sample_credential)

    assert "cred_ex_id" in result
    assert result["cred_ex_id"].startswith("cred_demo_")
    assert "credential_id" in result
    assert result["state"] == "done"

    credential = result["credential"]
    assert "proof" in credential
    proof = credential["proof"]
    assert proof["type"] == "Ed25519Signature2020"
    assert proof["proofPurpose"] == "assertionMethod"
    assert "proofValue" in proof
    assert proof["proofValue"].startswith("z")
    assert "verificationMethod" in proof
    assert proof["verificationMethod"].startswith("did:cheqd:testnet:demo-doctor-123#key-1")


@pytest.mark.asyncio
async def test_issue_credential_preserves_fields(demo_service, sample_credential):
    """Test issue_credential preserves all original credential fields."""
    result = await demo_service.issue_credential(sample_credential)
    credential = result["credential"]

    assert credential["@context"] == sample_credential["@context"]
    assert credential["type"] == sample_credential["type"]
    assert credential["issuer"] == sample_credential["issuer"]
    assert credential["issuanceDate"] == sample_credential["issuanceDate"]
    assert credential["credentialSubject"] == sample_credential["credentialSubject"]


@pytest.mark.asyncio
async def test_issue_credential_strips_existing_proof(demo_service, sample_credential):
    """Test issue_credential strips any pre-existing proof before signing."""
    credential_with_proof = dict(sample_credential)
    credential_with_proof["proof"] = {"type": "old", "proofValue": "old-value"}

    result = await demo_service.issue_credential(credential_with_proof)
    credential = result["credential"]

    # Should have new proof, not old one
    assert credential["proof"]["type"] == "Ed25519Signature2020"
    assert credential["proof"]["proofValue"].startswith("z")
    assert credential["proof"]["proofValue"] != "old-value"


@pytest.mark.asyncio
async def test_issue_credential_hmac_signature_format(demo_service, sample_credential):
    """Test HMAC signature is z-prefixed hex string of correct length."""
    result = await demo_service.issue_credential(sample_credential)
    proof_value = result["credential"]["proof"]["proofValue"]

    assert proof_value.startswith("z")
    hex_part = proof_value[1:]
    # SHA-256 produces 64 hex characters
    assert len(hex_part) == 64
    # Validate it's valid hex
    int(hex_part, 16)


# ============================================================================
# CREDENTIAL VERIFICATION
# ============================================================================


@pytest.mark.asyncio
async def test_verify_credential_valid(demo_service, sample_credential):
    """Test verify_credential validates a genuinely signed credential."""
    issued = await demo_service.issue_credential(sample_credential)
    signed_vc = issued["credential"]

    result = await demo_service.verify_credential(signed_vc)

    assert result["verified"] is True
    assert result["state"] == "done"
    assert "presentation_id" in result


@pytest.mark.asyncio
async def test_verify_credential_rejects_tampered_data(demo_service, sample_credential):
    """Test verify_credential rejects credential with tampered data."""
    issued = await demo_service.issue_credential(sample_credential)
    signed_vc = issued["credential"]

    # Tamper with credential data
    tampered = copy.deepcopy(signed_vc)
    tampered["credentialSubject"]["prescription"]["quantity"] = 999

    result = await demo_service.verify_credential(tampered)
    assert result["verified"] is False
    assert result["state"] == "failed"


@pytest.mark.asyncio
async def test_verify_credential_rejects_tampered_proof(demo_service, sample_credential):
    """Test verify_credential rejects credential with tampered proof value."""
    issued = await demo_service.issue_credential(sample_credential)
    signed_vc = issued["credential"]

    # Tamper with proof
    tampered = copy.deepcopy(signed_vc)
    tampered["proof"]["proofValue"] = "z" + "a" * 64

    result = await demo_service.verify_credential(tampered)
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_verify_credential_rejects_missing_proof(demo_service):
    """Test verify_credential rejects credential without proof."""
    no_proof = {"@context": [], "type": [], "issuer": "test"}

    result = await demo_service.verify_credential(no_proof)
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_verify_credential_rejects_invalid_proof_format(demo_service, sample_credential):
    """Test verify_credential rejects credential with non-z-prefixed proof."""
    issued = await demo_service.issue_credential(sample_credential)
    signed_vc = issued["credential"]

    # Remove z prefix
    tampered = copy.deepcopy(signed_vc)
    tampered["proof"]["proofValue"] = "invalid-proof-value"

    result = await demo_service.verify_credential(tampered)
    assert result["verified"] is False
    assert "Invalid proof format" in result.get("error", "")


# ============================================================================
# ROUND-TRIP: ISSUE → VERIFY
# ============================================================================


@pytest.mark.asyncio
async def test_sign_verify_round_trip(demo_service, sample_credential):
    """Test complete sign→verify round-trip succeeds."""
    # Sign
    issued = await demo_service.issue_credential(sample_credential)
    signed_vc = issued["credential"]

    # Verify
    result = await demo_service.verify_credential(signed_vc)
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_sign_verify_different_credentials(demo_service):
    """Test sign→verify works for different credential contents."""
    cred1 = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential"],
        "issuer": "did:cheqd:testnet:demo-doc-a",
        "credentialSubject": {"id": "did:cheqd:testnet:demo-pat-a", "data": "first"},
    }
    cred2 = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential"],
        "issuer": "did:cheqd:testnet:demo-doc-b",
        "credentialSubject": {"id": "did:cheqd:testnet:demo-pat-b", "data": "second"},
    }

    issued1 = await demo_service.issue_credential(cred1)
    issued2 = await demo_service.issue_credential(cred2)

    # Each verifies against itself
    assert (await demo_service.verify_credential(issued1["credential"]))["verified"] is True
    assert (await demo_service.verify_credential(issued2["credential"]))["verified"] is True

    # Cross-verification: credential1 proof on credential2 data should fail
    cross = copy.deepcopy(issued1["credential"])
    cross["credentialSubject"] = issued2["credential"]["credentialSubject"]
    assert (await demo_service.verify_credential(cross))["verified"] is False


# ============================================================================
# ASYNC CONTEXT MANAGER
# ============================================================================


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test DemoACAPyService works as async context manager."""
    async with DemoACAPyService() as service:
        result = await service.create_wallet()
        assert "did" in result


# ============================================================================
# REVOCATION REGISTRY (STUB)
# ============================================================================


@pytest.mark.asyncio
async def test_create_revocation_registry(demo_service):
    """Test create_revocation_registry returns demo response."""
    result = await demo_service.create_revocation_registry(
        "did:cheqd:testnet:demo-issuer", "cred-def-123"
    )

    assert "revoc_reg_id" in result
    assert result["revoc_reg_id"].startswith("demo-rev-reg-")


# ============================================================================
# CONSTRUCTOR
# ============================================================================


def test_constructor_defaults():
    """Test DemoACAPyService default constructor values."""
    service = DemoACAPyService()
    assert service.admin_url == "demo://localhost"
    assert service.tenant_id == "default"
    assert service.tenant_token is None


def test_constructor_custom_params():
    """Test DemoACAPyService accepts custom constructor params."""
    service = DemoACAPyService(
        admin_url="http://custom:8001",
        tenant_id="test-tenant",
        tenant_token="test-token",
    )
    assert service.admin_url == "http://custom:8001"
    assert service.tenant_id == "test-tenant"
    assert service.tenant_token == "test-token"
