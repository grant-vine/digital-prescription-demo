"""QR code generation service for prescription credentials."""

import base64
import io
import json
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlencode

import qrcode
from qrcode.constants import ERROR_CORRECT_H

from app.services.vc import VCService


QR_SIZE_THRESHOLD = 2953


class QRService:
    def __init__(self, base_url: Optional[str] = None, tenant_id: str = "default"):
        self.base_url = base_url or "https://api.rxdistribute.com"
        self.tenant_id = tenant_id

    def generate_qr(self, data: str) -> str:
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return qr_base64

    def create_url_fallback(self, credential_id: str, credential: Dict[str, Any]) -> str:
        credential_json = json.dumps(credential, sort_keys=True)
        credential_hash = hashlib.sha256(credential_json.encode()).hexdigest()

        params = {"hash": credential_hash[:16]}
        query_string = urlencode(params)

        url = f"{self.base_url}/api/v1/credentials/{credential_id}?{query_string}"
        return url

    def generate_prescription_qr(
        self,
        prescription: Any,
        doctor_did: str,
        patient_did: str,
        credential_id: str,
    ) -> Dict[str, Any]:
        vc_service = VCService()
        credential = vc_service.create_credential(prescription, doctor_did, patient_did)

        credential["id"] = credential_id

        if prescription.digital_signature:
            try:
                stored_vc = json.loads(prescription.digital_signature)
                if isinstance(stored_vc, dict) and "proof" in stored_vc:
                    credential["proof"] = stored_vc["proof"]
                else:
                    credential["proof"] = {
                        "type": "Ed25519Signature2020",
                        "proofValue": prescription.digital_signature,
                    }
            except (json.JSONDecodeError, TypeError):
                credential["proof"] = {
                    "type": "Ed25519Signature2020",
                    "proofValue": prescription.digital_signature,
                }

        credential_json = json.dumps(credential, separators=(",", ":"))
        credential_size = len(credential_json.encode("utf-8"))

        if credential_size <= QR_SIZE_THRESHOLD:
            qr_code = self.generate_qr(credential_json)
            return {
                "qr_code": qr_code,
                "data_type": "embedded",
                "credential_id": credential_id,
            }
        else:
            url = self.create_url_fallback(credential_id, credential)
            qr_code = self.generate_qr(url)

            return {
                "qr_code": qr_code,
                "data_type": "url",
                "credential_id": credential_id,
                "url": url,
            }
