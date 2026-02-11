## Title
Send Prescription to Patient Wallet (QR)

## User Story
As a doctor who has signed a prescription, I want to send it to the patient's digital wallet using a QR code, so that the patient can securely receive and manage their prescription.

## Description
After signing, the prescription needs to be transmitted to the patient. In the MVP, this is accomplished via QR code scanning, which provides a simple, reliable method for prescription transfer without requiring complex DIDComm messaging infrastructure.

## Context
The MVP uses QR codes for prescription transfer because they are simple, reliable, and work without network connectivity. The doctor generates a QR code containing the signed prescription as a verifiable credential. The patient scans this QR code with their wallet app to receive the prescription. This approach minimizes infrastructure complexity while maintaining cryptographic security.

## Acceptance Criteria

### QR Code Generation
- [ ] After signing prescription, doctor can generate a QR code
- [ ] QR code contains the complete verifiable credential (prescription)
- [ ] QR code includes doctor's DID and digital signature
- [ ] System displays QR code prominently on screen
- [ ] QR code remains valid for a configurable time period (default: 5 minutes)
- [ ] Doctor can regenerate QR code if expired

### Prescription Packaging
- [ ] Prescription is serialized as W3C Verifiable Credential JSON
- [ ] Credential includes:
  - Prescription ID
  - Doctor DID (issuer)
  - Patient name/identifier
  - Medications with dosage and instructions
  - Issue date and expiration date
  - Number of repeats
  - Doctor's digital signature
- [ ] Credential size is optimized for QR code encoding
- [ ] If credential too large, use URL with credential ID (fallback)

### QR Code Display
- [ ] QR code is large enough for easy scanning (min 300x300px)
- [ ] High contrast (black on white) for reliability
- [ ] Instructions displayed: "Patient: Scan with your wallet app"
- [ ] Prescription summary shown alongside QR code
- [ ] Option to print QR code as backup
- [ ] Copy credential JSON button for debugging

### Transfer Confirmation
- [ ] Doctor cannot confirm patient received prescription (no backchannel)
- [ ] QR code marked as "displayed" in doctor's records
- [ ] Timestamp of QR code generation recorded
- [ ] Doctor can mark prescription as "given to patient" manually
- [ ] Prescription status: Draft → Signed → QR Generated → Marked as Given

### Multiple Prescriptions
- [ ] Doctor can select multiple prescriptions to include in one QR code
- [ ] System warns if combined size exceeds QR code limits
- [ ] Option to generate separate QR codes for each prescription
- [ ] Batch QR code generation for efficiency

### QR Code Data Structure
```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "type": ["VerifiableCredential", "MedicalPrescription"],
  "issuer": "did:cheqd:testnet:7bf81a20-633c-4bf8-b141-8c7e0a05d5a6",
  "issuanceDate": "2026-02-11T14:30:00Z",
  "expirationDate": "2026-05-11T14:30:00Z",
  "credentialSubject": {
    "id": "patient-identifier-or-did",
    "prescriptionId": "RX-20260211-abc123",
    "patientName": "John Doe",
    "medications": [
      {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency": "3 times daily",
        "duration": "7 days",
        "quantity": "21 capsules"
      }
    ],
    "repeatsAllowed": 0,
    "instructions": "Take with food"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-02-11T14:30:00Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:cheqd:testnet:7bf81a20...#key-1",
    "proofValue": "z58DAdFfa9SkqZMVPxAQp..."
  }
}
```

## API Integration Points

```
POST /api/v1/prescriptions/{id}/generate-qr
GET  /api/v1/prescriptions/{id}/credential
POST /api/v1/prescriptions/{id}/mark-given
```

**Optional (if using credential URL instead of embedded data):**
```
POST https://cloudapi.test.didxtech.com/tenant/v1/issuer/credentials
GET  https://cloudapi.test.didxtech.com/tenant/v1/credentials/{id}
```

## Technical Implementation

### QR Code Generation
- **Library:** `qrcode` (Python) or `react-native-qrcode-svg` (mobile)
- **Encoding:** Base64-encoded JSON or URL to credential endpoint
- **Error Correction:** Level H (30% redundancy) for reliability
- **Size Limits:** Max 2953 bytes for QR version 40

### Credential Serialization
```python
import qrcode
import json

def generate_prescription_qr(credential: dict) -> bytes:
    """Generate QR code from verifiable credential"""
    credential_json = json.dumps(credential)
    
    # If too large, use URL instead
    if len(credential_json) > 2500:
        url = f"https://api.example.com/credentials/{credential['id']}"
        qr_data = url
    else:
        qr_data = credential_json
    
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    return qr.make_image(fill_color="black", back_color="white")
```

## Notes

### Technical Constraints
- QR code must be scannable from phone screen (min 300x300px display size)
- Credential size should fit in QR code v40 (2953 bytes max)
- Use URL fallback for large prescriptions
- No network required for credential verification (embedded signature)

### Privacy Considerations
- QR code displayed on doctor's screen is temporarily visible
- Anyone with camera access can scan QR code
- Patient should scan immediately and doctor should clear screen
- No prescription data stored on servers after generation
- QR code expires after 5 minutes to limit exposure window

### Security Measures
- Doctor's digital signature embedded in credential
- QR code contains tamper-evident proof
- Time-limited validity prevents replay attacks
- Patient wallet must verify signature before accepting
- Expired QR codes rejected by wallet

### Demo Simplifications
- QR codes displayed on screen (not printed)
- No QR code expiration in demo mode (for easier testing)
- Pre-configured test credentials
- Single prescription per QR code

### Alternative: URL-Based QR Codes
If credential too large for direct embedding:
```json
{
  "credentialUrl": "https://api.example.com/credentials/abc123",
  "issuer": "did:cheqd:testnet:7bf81a20...",
  "signature": "z58DAdFfa9SkqZMVPxAQp...",
  "expiresAt": "2026-02-11T14:35:00Z"
}
```
Patient wallet fetches full credential from URL after signature verification.

### Error Scenarios
- QR code generation fails: Show error, allow retry
- Credential too large: Automatically switch to URL mode
- Display timeout: Regenerate QR code with new timestamp
- Patient reports not received: Doctor regenerates QR code

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-003: Sign Prescription with Digital Signature (prerequisite)
- US-006: Receive Prescription in Wallet (patient side)
- US-018: DIDComm v2 Messaging (future replacement)
