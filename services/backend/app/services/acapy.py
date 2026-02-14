"""ACA-Py service layer for SSI operations.

Provides async interface to ACA-Py Admin API for:
- Wallet and DID management
- Credential issuance and verification
- Revocation registry operations
"""

import os
from typing import Dict, Any, Optional
import httpx


class ACAPyService:
    """Service for interacting with ACA-Py Admin API.

    Implements core SSI operations using ACA-Py's HTTP endpoints:
    - DID creation on cheqd testnet
    - W3C Verifiable Credential issuance
    - Credential verification
    - Revocation registry management

    Uses httpx.AsyncClient for async HTTP operations.
    Reads ACAPY_ADMIN_URL from environment (default: http://acapy:8001).
    """

    def __init__(self, admin_url: Optional[str] = None, tenant_id: str = "default", tenant_token: Optional[str] = None):
        """Initialize ACA-Py service with admin API URL.

        Args:
            admin_url: ACA-Py admin API base URL.
                      If None, reads from ACAPY_ADMIN_URL env var.
                      Default: http://acapy:8001
            tenant_id: Tenant identifier for multi-tenancy scoping.
            tenant_token: DIDx tenant JWT token for authenticated requests.
        """
        self.admin_url = admin_url or os.getenv("ACAPY_ADMIN_URL", "http://acapy:8001")
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.admin_url)
        return self._client

    async def close(self):
        """Close HTTP client connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def create_wallet(self) -> Dict[str, Any]:
        """Create wallet DID on cheqd testnet.

        POST to /wallet/did/create

        Returns:
            Dict with keys:
            - did: DID string (did:cheqd:testnet:...)
            - verkey: Verification key
            - public: Boolean indicating public DID
        """
        client = self._get_client()
        try:
            response = await client.post("/wallet/did/create")
            response.raise_for_status()
            data = response.json()

            # Extract result from response wrapper
            if "result" in data:
                return data["result"]
            return data

        except httpx.HTTPError as e:
            return {"error": str(e), "did": None, "verkey": None, "public": False}

    async def get_wallet_status(self) -> Dict[str, Any]:
        """Get wallet status from ACA-Py.

        GET to /status

        Returns:
            Dict with keys:
            - version: ACA-Py version string
            - label: Wallet label
            - wallet: Dict with wallet info (id, type)
            - public_did: Public DID string if set
        """
        client = self._get_client()
        try:
            response = await client.get("/status")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "version": "unknown",
                "label": "unknown",
                "wallet": {},
                "public_did": None,
            }

    async def create_did(
        self, method: str = "cheqd:testnet", public: bool = True
    ) -> Dict[str, Any]:
        """Create DID with specific method.

        POST to /wallet/did/create with method parameter.

        Args:
            method: DID method (e.g., "cheqd:testnet")
            public: Whether DID should be publicly resolvable

        Returns:
            Dict with keys:
            - did: DID string
            - verkey: Verification key
            - public: Boolean
            - method: DID method used
        """
        client = self._get_client()
        try:
            payload = {"method": method, "public": public}
            response = await client.post("/wallet/did/create", json=payload)
            response.raise_for_status()
            data = response.json()

            # Ensure method is included in response
            if "method" not in data:
                data["method"] = method

            return data

        except httpx.HTTPError as e:
            return {"error": str(e), "did": None, "verkey": None, "public": False, "method": method}

    async def issue_credential(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        """Issue W3C Verifiable Credential.

        POST to /issue-credential-2.0/send

        Args:
            credential: Dict containing:
                - issuer_did: Issuer DID string
                - type: List of credential types
                - credentialSubject: Dict with subject claims

        Returns:
            Dict with keys:
            - cred_ex_id: Credential exchange ID
            - state: Exchange state ("done" when complete)
            - credential_id: Issued credential ID
            - credential: Full W3C VC with proof
        """
        client = self._get_client()
        try:
            # Format payload for ACA-Py issue-credential-2.0 API
            payload = {
                "auto_remove": False,
                "credential_preview": {
                    "@type": "issue-credential/2.0/credential-preview",
                    "attributes": [],
                },
                "filter": {"ld_proof": {"credential": credential}},
            }

            response = await client.post("/issue-credential-2.0/send", json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "cred_ex_id": None,
                "state": "failed",
                "credential_id": None,
                "credential": None,
            }

    async def verify_credential(self, vc: Dict[str, Any]) -> Dict[str, Any]:
        """Verify W3C Verifiable Credential.

        POST to /present-proof-2.0/verify-presentation

        Args:
            vc: W3C Verifiable Credential dict with proof

        Returns:
            Dict with keys:
            - verified: Boolean indicating valid proof
            - presentation_id: Presentation exchange ID
            - state: Verification state
            - presentation: Full presentation object
        """
        client = self._get_client()
        try:
            # Wrap credential in presentation format
            payload = {
                "presentation": {
                    "@context": ["https://www.w3.org/2018/credentials/v1"],
                    "type": ["VerifiablePresentation"],
                    "verifiableCredential": [vc],
                }
            }

            response = await client.post("/present-proof-2.0/verify-presentation", json=payload)
            response.raise_for_status()
            data = response.json()

            # Ensure verified field exists
            if "verified" not in data:
                data["verified"] = data.get("state") == "done"

            return data

        except httpx.HTTPError as e:
            # Check if this is validation failure vs network error
            if hasattr(e, "response") and e.response.status_code == 400:
                return {
                    "verified": False,
                    "presentation_id": None,
                    "state": "failed",
                    "error": "Invalid credential proof",
                }

            return {"error": str(e), "verified": False, "presentation_id": None, "state": "failed"}

    async def create_revocation_registry(self, issuer_did: str, cred_def_id: str) -> Dict[str, Any]:
        """Create revocation registry for credential definition.

        POST to /revocation/create-registry

        Args:
            issuer_did: Issuer DID string
            cred_def_id: Credential definition ID

        Returns:
            Dict with keys:
            - revoc_reg_id: Revocation registry ID
            - revoc_reg_def: Registry definition object
            - revoc_reg_entry: Initial registry entry
        """
        client = self._get_client()
        try:
            payload = {
                "issuer_did": issuer_did,
                "credential_definition_id": cred_def_id,
                "max_cred_num": 1000000,
            }

            response = await client.post("/revocation/create-registry", json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "revoc_reg_id": None,
                "revoc_reg_def": None,
                "revoc_reg_entry": None,
            }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
