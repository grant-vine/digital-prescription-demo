"""Integration tests for demo mode sign→verify round-trip.

Tests the full pipeline: VCService + DemoACAPyService (or mock) through
the signing and verification service layers, matching what the API endpoints do.
"""

import pytest
import json
import hashlib
import hmac

from app.services.demo_acapy import DemoACAPyService, DEMO_HMAC_SECRET
from app.services.vc import VCService
from app.services.verification import VerificationService


@pytest.fixture
def demo_vc_service():
    """VCService backed by DemoACAPyService."""
    return VCService(acapy_service=DemoACAPyService())


@pytest.fixture
def mock_prescription():
    """Minimal prescription-like object for VCService.create_credential."""
    from datetime import datetime, timedelta

    class FakePrescription:
        id = 42
        medication_name = "Metformin"
        medication_code = "A10BA02"
        dosage = "500mg"
        quantity = 60
        instructions = "Take one tablet twice daily with meals"
        date_issued = datetime(2026, 2, 12, 10, 0, 0)
        date_expires = datetime(2026, 5, 12, 23, 59, 59)

    return FakePrescription()


@pytest.mark.asyncio
async def test_vc_service_sign_verify_round_trip(demo_vc_service, mock_prescription):
    """VCService.sign_credential → VCService.verify_credential succeeds."""
    doctor_did = "did:cheqd:testnet:demo-doctor-abc"
    patient_did = "did:cheqd:testnet:demo-patient-xyz"

    credential = demo_vc_service.create_credential(mock_prescription, doctor_did, patient_did)
    sign_result = await demo_vc_service.sign_credential(credential, doctor_did)

    signed_vc = sign_result["credential"]
    assert "proof" in signed_vc

    verify_result = await demo_vc_service.verify_credential(signed_vc)
    assert verify_result["valid"] is True
    assert verify_result["issuer"] == doctor_did
    assert verify_result["subject"] == patient_did


@pytest.mark.asyncio
async def test_vc_service_sign_result_structure(demo_vc_service, mock_prescription):
    """VCService.sign_credential returns expected keys."""
    doctor_did = "did:cheqd:testnet:demo-doc"
    patient_did = "did:cheqd:testnet:demo-pat"

    credential = demo_vc_service.create_credential(mock_prescription, doctor_did, patient_did)
    result = await demo_vc_service.sign_credential(credential, doctor_did)

    assert "credential" in result
    assert "credential_id" in result
    assert "signature" in result
    assert result["credential_id"].startswith("cred_demo_")


@pytest.mark.asyncio
async def test_signed_vc_json_serializable(demo_vc_service, mock_prescription):
    """Signed VC can be JSON-serialized and deserialized (as stored in DB)."""
    doctor_did = "did:cheqd:testnet:demo-doc"
    patient_did = "did:cheqd:testnet:demo-pat"

    credential = demo_vc_service.create_credential(mock_prescription, doctor_did, patient_did)
    sign_result = await demo_vc_service.sign_credential(credential, doctor_did)
    signed_vc = sign_result["credential"]

    serialized = json.dumps(signed_vc)
    deserialized = json.loads(serialized)

    verify_result = await demo_vc_service.verify_credential(deserialized)
    assert verify_result["valid"] is True


@pytest.mark.asyncio
async def test_seed_script_generate_signed_vc_is_verifiable():
    """The seed script's HMAC signing logic produces verifiable output.

    Reproduces the same signing logic from seed_demo_data.py and verifies
    it matches what DemoACAPyService.verify_credential expects.
    """
    credential = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "PrescriptionCredential"],
        "issuer": "did:cheqd:testnet:demo-seed-doctor",
        "issuanceDate": "2026-02-12T08:00:00Z",
        "credentialSubject": {
            "id": "did:cheqd:testnet:demo-seed-patient",
            "prescription": {
                "id": 100,
                "medication_name": "Aspirin",
                "dosage": "100mg",
                "quantity": 30,
            },
        },
    }

    credential_copy = {k: v for k, v in credential.items() if k != "proof"}
    canonical = json.dumps(credential_copy, sort_keys=True, separators=(",", ":"))
    signature = hmac.new(
        DEMO_HMAC_SECRET, canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    signed_vc = dict(credential)
    signed_vc["proof"] = {
        "type": "Ed25519Signature2020",
        "created": "2026-02-12T08:00:00Z",
        "proofPurpose": "assertionMethod",
        "verificationMethod": "did:cheqd:testnet:demo-seed-doctor#key-1",
        "proofValue": f"z{signature}",
    }

    service = DemoACAPyService()
    result = await service.verify_credential(signed_vc)
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_verification_service_with_demo_backend(test_session, doctor_user, patient_user):
    """VerificationService full pipeline with demo-signed prescription."""
    from app.models.prescription import Prescription
    from app.models.did import DID
    from datetime import datetime

    doctor_did_str = "did:cheqd:testnet:demo-integ-doctor"
    patient_did_str = "did:cheqd:testnet:demo-integ-patient"

    doctor_did = DID(
        user_id=doctor_user.id, did_identifier=doctor_did_str, role="doctor"
    )
    patient_did = DID(
        user_id=patient_user.id, did_identifier=patient_did_str, role="patient"
    )
    test_session.add_all([doctor_did, patient_did])
    test_session.flush()

    vc_service = VCService(acapy_service=DemoACAPyService())

    rx = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Atorvastatin",
        medication_code="C10AA05",
        dosage="20mg",
        quantity=30,
        instructions="Take one tablet daily at bedtime",
        date_issued=datetime(2026, 2, 12, 10, 0, 0),
        date_expires=datetime(2026, 5, 12, 23, 59, 59),
        status="active",
    )
    test_session.add(rx)
    test_session.flush()

    credential = vc_service.create_credential(rx, doctor_did_str, patient_did_str)
    sign_result = await vc_service.sign_credential(credential, doctor_did_str)
    signed_vc = sign_result["credential"]

    rx.digital_signature = json.dumps(signed_vc)
    rx.credential_id = sign_result["credential_id"]
    test_session.commit()

    verification_service = VerificationService()
    verification_service.vc_service = vc_service

    result = await verification_service.verify_prescription(rx.id, test_session)

    assert result["verified"] is True
    assert result["checks"]["signature_valid"] is True
    assert result["checks"]["doctor_trusted"] is True
    assert result["checks"]["not_revoked"] is True
    assert result["issuer_did"] == doctor_did_str
    assert result["subject_did"] == patient_did_str
