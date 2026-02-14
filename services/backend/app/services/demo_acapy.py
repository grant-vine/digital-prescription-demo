"""Demo mode ACA-Py service mock.

Provides a drop-in replacement for ACAPyService that uses HMAC-SHA256
for deterministic, verifiable signatures without requiring ACA-Py infrastructure.

DEMO ONLY — not cryptographically secure for production use.
"""

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


# Shared secret for demo signing — hardcoded, demo only
DEMO_HMAC_SECRET = os.getenv(
    "DEMO_HMAC_SECRET", "rxdistribute-demo-mode-secret-key-2026"
).encode("utf-8")


class DemoACAPyService:
    """Mock ACAPyService using HMAC-SHA256 for demo mode.

    Provides the same interface as ACAPyService but operates entirely
    in-memory without any external HTTP calls. Uses HMAC-SHA256 for
    deterministic signing that enables sign→verify round-trips.
    """

    def __init__(self, admin_url: Optional[str] = None, tenant_id: str = "default", tenant_token: Optional[str] = None):
        self.admin_url = admin_url or "demo://localhost"
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token

    async def close(self):
        """No-op — no connections to close."""
        pass

    async def create_wallet(self) -> Dict[str, Any]:
        unique_id = uuid.uuid4().hex[:24]
        return {
            "did": f"did:cheqd:testnet:demo-{unique_id}",
            "verkey": f"demo-verkey-{unique_id}",
            "public": True,
        }

    async def get_wallet_status(self) -> Dict[str, Any]:
        return {
            "version": "demo-1.0.0",
            "label": "rx-demo",
            "wallet": {"id": "demo-wallet", "type": "demo"},
            "public_did": None,
        }

    async def create_did(self, method: str = "cheqd:testnet", public: bool = True) -> Dict[str, Any]:
        unique_id = uuid.uuid4().hex[:24]
        return {
            "did": f"did:cheqd:testnet:demo-{unique_id}",
            "verkey": f"demo-verkey-{unique_id}",
            "public": public,
            "method": method,
        }

    async def issue_credential(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        """Issue credential with HMAC-SHA256 proof."""
        cred_ex_id = f"cred_demo_{uuid.uuid4().hex[:16]}"

        # Create a copy for signing (exclude any existing proof)
        credential_copy = {k: v for k, v in credential.items() if k != "proof"}

        # Create HMAC-SHA256 signature
        canonical = json.dumps(credential_copy, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(DEMO_HMAC_SECRET, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        proof_value = f"z{signature}"

        # Add W3C proof
        signed_credential = dict(credential_copy)
        signed_credential["proof"] = {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat() + "Z",
            "proofPurpose": "assertionMethod",
            "verificationMethod": f"{credential.get('issuer', 'did:cheqd:testnet:demo')}#key-1",
            "proofValue": proof_value,
        }

        return {
            "cred_ex_id": cred_ex_id,
            "credential_id": cred_ex_id,
            "credential": signed_credential,
            "state": "done",
        }

    async def verify_credential(self, vc: Dict[str, Any]) -> Dict[str, Any]:
        """Verify credential by recomputing HMAC-SHA256."""
        proof = vc.get("proof", {})
        stored_proof_value = proof.get("proofValue", "")

        if not stored_proof_value.startswith("z"):
            return {"verified": False, "state": "failed", "error": "Invalid proof format"}

        stored_signature = stored_proof_value[1:]  # Remove z prefix

        # Recompute HMAC from credential without proof
        credential_copy = {k: v for k, v in vc.items() if k != "proof"}
        canonical = json.dumps(credential_copy, sort_keys=True, separators=(",", ":"))
        expected = hmac.new(DEMO_HMAC_SECRET, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

        verified = hmac.compare_digest(expected, stored_signature)

        return {
            "verified": verified,
            "state": "done" if verified else "failed",
            "presentation_id": f"pres_demo_{uuid.uuid4().hex[:16]}",
        }

    async def create_revocation_registry(self, issuer_did: str, cred_def_id: str) -> Dict[str, Any]:
        return {
            "revoc_reg_id": f"demo-rev-reg-{uuid.uuid4().hex[:16]}",
            "revoc_reg_def": {"type": "demo"},
            "revoc_reg_entry": {"type": "demo"},
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
