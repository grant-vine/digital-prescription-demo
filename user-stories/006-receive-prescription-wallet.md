## Title
Receive Prescription in Wallet (QR)

## User Story
As a patient with a digital wallet, I want to receive prescriptions issued by my doctor via QR code, so that I can securely store them and access them when needed.

## Description
In the MVP, prescriptions are transferred via QR code scanning, which provides a simple and reliable method for patients to receive their prescriptions. The patient scans a QR code displayed by the doctor, which contains the prescription data as a verifiable credential. The patient reviews and accepts the credential into their wallet.

## Context
When a doctor generates a QR code for a prescription, the patient scans it with their wallet app. The QR code contains the complete prescription as a W3C Verifiable Credential with the doctor's digital signature. The patient reviews the prescription details, verifies the doctor's identity, and accepts it into their wallet. This process is simple, works offline, and maintains cryptographic security.

## Acceptance Criteria

### QR Code Scanning
- [ ] Patient opens wallet app and selects "Scan Prescription"
- [ ] Camera permission requested and granted
- [ ] Camera viewfinder displays with targeting guide
- [ ] QR code detected and parsed automatically
- [ ] Visual/haptic feedback when QR code successfully scanned
- [ ] Support for scanning from screen or printed paper

### Credential Parsing
- [ ] System extracts credential JSON from QR code data
- [ ] If QR contains URL, fetch credential from endpoint
- [ ] Validate credential structure (W3C VC format)
- [ ] Extract key fields: issuer DID, prescription ID, medications
- [ ] Handle parsing errors gracefully with clear messages
- [ ] Support multiple credential formats (embedded vs URL-based)

### Doctor Verification
- [ ] Resolve doctor's DID from credential issuer field
- [ ] Verify doctor's digital signature on credential
- [ ] Check doctor's credentials against trust registry (if available)
- [ ] Display doctor information: name, practice, registration number
- [ ] Show verification status: ✅ Verified or ⚠️ Unverified
- [ ] Warn if doctor not in trust registry (demo: allow anyway)

### Prescription Review
- [ ] Patient can view prescription details before accepting:
  - Doctor information (name, practice, contact)
  - Prescription ID and issue date
  - Medications with dosage and instructions
  - Validity period (issue date to expiration date)
  - Number of repeats allowed
  - Special instructions or warnings
- [ ] Display medications in readable format (not raw FHIR)
- [ ] Highlight any warnings or important notes
- [ ] Show credential metadata (issued date, expires date)

### Credential Acceptance
- [ ] Patient explicitly taps "Accept" or "Reject" button
- [ ] Upon acceptance, credential is stored in wallet database
- [ ] Timestamp of acceptance is recorded
- [ ] Prescription is added to patient's medication list
- [ ] Success confirmation displayed: "Prescription saved"
- [ ] Option to view prescription immediately after acceptance

### Rejection Handling
- [ ] Patient can reject prescription by tapping "Reject"
- [ ] Optional rejection reason: Wrong patient, Concerned about medication, Other
- [ ] Rejected prescription is NOT stored in wallet
- [ ] Rejection event logged locally (for patient's records)
- [ ] Doctor is NOT notified (no backchannel in QR flow)
- [ ] Clear message: "Prescription not saved"

### Wallet Storage
- [ ] Accepted prescription is stored as verifiable credential (JSON)
- [ ] Local database: SQLite or secure storage
- [ ] Indexed by: prescription ID, doctor DID, issue date
- [ ] Patient can view all stored prescriptions in wallet
- [ ] Prescriptions organized by date (newest first)
- [ ] Status indicators: 🟢 Active, 🟡 Partially Used, 🔴 Expired
- [ ] Search and filter: by medication name, doctor, date range

## API Integration Points

```
POST /api/v1/wallet/scan-qr
POST /api/v1/wallet/credentials/accept
POST /api/v1/wallet/credentials/reject
GET  /api/v1/wallet/credentials
GET  /api/v1/wallet/credentials/{id}
```

**DID Resolution & Verification:**
```
GET  https://resolver.cheqd.net/1.0/identifiers/{did}
POST /api/v1/verify-credential
GET  /api/v1/trust-registry/verify-doctor
```

## Technical Implementation

### QR Code Scanning
```typescript
// React Native - Expo Camera
import { Camera } from 'expo-camera';
import { BarCodeScanner } from 'expo-barcode-scanner';

const ScanPrescriptionScreen = () => {
  const handleBarCodeScanned = ({ type, data }) => {
    try {
      // Parse QR data (JSON or URL)
      const credential = JSON.parse(data);
      
      // Verify signature
      const isValid = await verifyCredential(credential);
      
      if (isValid) {
        // Show review screen
        navigation.navigate('ReviewPrescription', { credential });
      } else {
        showError('Invalid prescription signature');
      }
    } catch (error) {
      showError('Failed to scan prescription');
    }
  };
  
  return (
    <Camera
      onBarCodeScanned={handleBarCodeScanned}
      barCodeScannerSettings={{
        barCodeTypes: [BarCodeScanner.Constants.BarCodeType.qr],
      }}
    />
  );
};
```

### Credential Verification
```python
# Backend - FastAPI
from did_resolver import resolve_did
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

async def verify_prescription_credential(credential: dict) -> bool:
    """Verify doctor's signature on prescription credential"""
    
    # 1. Extract issuer DID
    issuer_did = credential.get('issuer')
    
    # 2. Resolve DID to get public key
    did_document = await resolve_did(issuer_did)
    public_key_jwk = did_document['verificationMethod'][0]['publicKeyJwk']
    
    # 3. Verify signature
    proof = credential.get('proof')
    signature = base64.b64decode(proof['proofValue'])
    
    # 4. Reconstruct signed message
    credential_without_proof = {k: v for k, v in credential.items() if k != 'proof'}
    message = json.dumps(credential_without_proof, sort_keys=True).encode()
    
    # 5. Verify
    try:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            base64.b64decode(public_key_jwk['x'])
        )
        public_key.verify(signature, message)
        return True
    except Exception:
        return False
```

### Wallet Storage
```python
# Local Storage - SQLite
CREATE TABLE credentials (
    id TEXT PRIMARY KEY,
    credential_json TEXT NOT NULL,
    issuer_did TEXT NOT NULL,
    subject_id TEXT,
    credential_type TEXT,
    issue_date TIMESTAMP,
    expiration_date TIMESTAMP,
    status TEXT DEFAULT 'active',
    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_credentials_issuer ON credentials(issuer_did);
CREATE INDEX idx_credentials_issue_date ON credentials(issue_date DESC);
CREATE INDEX idx_credentials_status ON credentials(status);
```

## Notes

### Technical Constraints
- QR scanning requires camera permission
- Works completely offline (no network for basic scan)
- Network required for DID resolution and trust registry checks
- Credential stored locally in encrypted database
- No backchannel to doctor (fire-and-forget)

### User Experience
- Simple one-step process: Scan → Review → Accept
- Clear visual feedback during scanning
- Readable prescription display (not technical JSON)
- Prominent "Accept" button for quick approval
- Status indicators for prescription lifecycle

### Offline Capability
- Scan and parse QR code offline
- View prescription details offline
- Accept into wallet offline
- DID resolution deferred until online
- Trust registry check deferred until online
- Warn user: "Verification pending network connection"

### Security
- Verify doctor's DID before displaying prescription
- Check credential signature before acceptance
- Validate credential hasn't expired
- Optional: Check revocation status (requires network)
- Warn if trust registry check fails

### Demo Simplifications
- Auto-grant camera permission in demo mode
- Skip trust registry check (allow any doctor)
- Pre-populated sample QR codes for testing
- No revocation checking in MVP
- Simplified error handling

### Data Display
- Convert FHIR-inspired format to human-readable
- Medication cards with icons
- Dosage schedule visualization (e.g., "3x daily")
- Expiration countdown for time-sensitive prescriptions
- Color-coded status: green (active), yellow (partial), red (expired)

### Error Scenarios
- QR code not detected: Show guidance ("Hold steady, ensure good lighting")
- Invalid QR data: "This is not a valid prescription"
- Expired credential: "This prescription has expired (issued [date])"
- Signature verification failed: "Cannot verify doctor's signature"
- Network error during verification: "Saved, verification pending"

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-004: Send Prescription to Patient Wallet (doctor side)
- US-007: View Prescription Details
- US-008: Share Prescription with Pharmacist
- US-018: DIDComm v2 Messaging (future replacement)
