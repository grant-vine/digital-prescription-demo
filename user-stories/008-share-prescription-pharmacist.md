## Title
Share Prescription with Pharmacist (QR)

## User Story
As a patient with an active prescription in my wallet, I want to securely share it with my chosen pharmacist using a QR code, so that they can verify and dispense my medications without me needing a paper prescription.

## Description
In the MVP, patients share prescriptions with pharmacists via QR code. The patient generates a QR code containing the prescription data as a verifiable presentation, which the pharmacist scans to receive and verify the prescription. This simple approach enables secure prescription transfer without requiring complex DIDComm messaging infrastructure.

## Context
When the patient is ready to fill their prescription at a pharmacy, they generate a QR code from their wallet that contains the prescription as a verifiable presentation. The pharmacist scans this QR code with their verification app to receive the prescription and verify its authenticity before dispensing medications. This approach works offline and requires no pre-established connections.

## Acceptance Criteria

### Prescription Selection
- [ ] Patient opens wallet and views their prescriptions list
- [ ] System shows only active, unexpired prescriptions
- [ ] Patient selects which prescription to share
- [ ] Option to select multiple prescriptions for batch sharing
- [ ] Prescription details previewed before generating QR code
- [ ] Patient can add notes for pharmacist (optional: "urgent", "questions about dosage")

### QR Code Generation (Patient Side)
- [ ] Patient taps "Share with Pharmacist" button
- [ ] System generates verifiable presentation from credential
- [ ] Presentation includes:
  - Original prescription credential
  - Patient's digital signature (proof of possession)
  - Timestamp of presentation creation
  - Unique presentation ID (prevents replay)
- [ ] QR code displayed on patient's screen
- [ ] QR code large enough for easy scanning (min 300x300px)
- [ ] Instructions: "Pharmacist: Please scan this code"

### Verifiable Presentation Structure
- [ ] Presentation wraps the original prescription credential
- [ ] Patient's signature proves they control the credential
- [ ] Challenge-response mechanism prevents replay attacks
- [ ] Timestamp ensures freshness (valid for 15 minutes)
- [ ] Presentation is self-contained (no external lookups required)

### QR Code Display (Patient)
- [ ] QR code prominently displayed with high contrast
- [ ] Prescription summary shown alongside QR code
- [ ] Timer shows remaining validity (countdown from 15 minutes)
- [ ] Patient can regenerate QR code if expired
- [ ] Option to keep screen on while displaying
- [ ] "Done" button to close when pharmacist confirms receipt

### QR Code Scanning (Pharmacist Side)
- [ ] Pharmacist opens verification app
- [ ] Camera activated for QR scanning
- [ ] QR code detected and parsed automatically
- [ ] Visual/haptic feedback when successfully scanned
- [ ] Support for scanning from phone screen
- [ ] Handle scanning errors gracefully

### Prescription Verification (Pharmacist)
- [ ] System extracts verifiable presentation from QR data
- [ ] Verify patient's signature on presentation
- [ ] Verify doctor's signature on underlying credential
- [ ] Resolve doctor's DID and check trust registry
- [ ] Check prescription hasn't expired
- [ ] Check presentation timestamp (reject if >15 min old)
- [ ] Optional: Check revocation status (requires network)

### Verification Results Display
- [ ] Clear verification status: ✅ Valid or ❌ Invalid
- [ ] If valid, show prescription details:
  - Patient name (from credential subject)
  - Doctor name and practice
  - Prescription ID
  - Medications with dosage and quantity
  - Issue date and expiration date
  - Repeats remaining
  - Special instructions
- [ ] If invalid, show specific reason:
  - Expired presentation
  - Invalid signature
  - Revoked credential
  - Doctor not in trust registry
  - Tampered data

### Pharmacist Actions
- [ ] Pharmacist reviews prescription details
- [ ] Pharmacist can mark prescription as "Dispensing"
- [ ] Pharmacist records which items are being dispensed
- [ ] Optional: Pharmacist notes partial dispensing
- [ ] System logs dispensing event locally
- [ ] No backchannel to patient or doctor (fire-and-forget)

### Selective Disclosure
- [ ] Patient sees exactly what will be shared (full prescription)
- [ ] System highlights any sensitive information
- [ ] Future: Support selective disclosure (share only specific fields)
- [ ] For MVP: Share entire prescription (no selective disclosure)

### Presentation Data Structure
```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3.org/2018/credentials/examples/v1"
  ],
  "type": "VerifiablePresentation",
  "id": "urn:uuid:presentation-abc123",
  "created": "2026-02-11T14:30:00Z",
  "expiresAt": "2026-02-11T14:45:00Z",
  "holder": "patient-identifier-or-did",
  "verifiableCredential": [{
    "@context": [...],
    "type": ["VerifiableCredential", "MedicalPrescription"],
    "issuer": "did:cheqd:testnet:doctor-did",
    "credentialSubject": {
      "id": "patient-identifier",
      "prescriptionId": "RX-20260211-abc123",
      "patientName": "John Doe",
      "medications": [...],
      "validUntil": "2026-05-11"
    },
    "proof": {
      "type": "Ed25519Signature2020",
      "created": "2026-02-11T10:00:00Z",
      "proofPurpose": "assertionMethod",
      "verificationMethod": "did:cheqd:testnet:doctor-did#key-1",
      "proofValue": "z58DAdF...doctor-signature..."
    }
  }],
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-02-11T14:30:00Z",
    "proofPurpose": "authentication",
    "verificationMethod": "patient-identifier#key-1",
    "challenge": "nonce-abc123",
    "proofValue": "z58DAdF...patient-signature..."
  }
}
```

## API Integration Points

```
POST /api/v1/wallet/prescriptions/{id}/create-presentation
GET  /api/v1/wallet/prescriptions/{id}
POST /api/v1/pharmacy/verify-presentation
POST /api/v1/pharmacy/dispense
GET  /api/v1/trust-registry/verify-doctor
```

**DID Resolution:**
```
GET  https://resolver.cheqd.net/1.0/identifiers/{did}
```

## Technical Implementation

### Generate Verifiable Presentation (Patient Wallet)
```typescript
// React Native - Patient Wallet
import { generatePresentation, signPresentation } from './crypto';

const shareWithPharmacist = async (prescriptionId: string) => {
  // 1. Load prescription credential from wallet
  const credential = await loadCredential(prescriptionId);
  
  // 2. Generate nonce for freshness
  const nonce = generateNonce();
  
  // 3. Create verifiable presentation
  const presentation = {
    '@context': ['https://www.w3.org/2018/credentials/v1'],
    type: 'VerifiablePresentation',
    id: `urn:uuid:${uuidv4()}`,
    created: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(), // 15 min
    holder: credential.credentialSubject.id,
    verifiableCredential: [credential],
  };
  
  // 4. Sign presentation (patient's signature)
  const signedPresentation = await signPresentation(presentation, nonce);
  
  // 5. Generate QR code
  const qrData = JSON.stringify(signedPresentation);
  setQRCode(qrData);
  
  // 6. Start expiration timer
  startExpirationTimer(15 * 60); // 15 minutes
};
```

### Verify Presentation (Pharmacist App)
```python
# Backend - FastAPI (Pharmacist Verification)
from datetime import datetime, timedelta
from did_resolver import resolve_did
from cryptography.hazmat.primitives.asymmetric import ed25519

async def verify_presentation(presentation: dict) -> dict:
    """Verify verifiable presentation from patient"""
    
    # 1. Check presentation timestamp
    created = datetime.fromisoformat(presentation['created'])
    expires = datetime.fromisoformat(presentation['expiresAt'])
    now = datetime.utcnow()
    
    if now < created or now > expires:
        return {'valid': False, 'reason': 'Presentation expired'}
    
    # 2. Extract credential
    credential = presentation['verifiableCredential'][0]
    
    # 3. Verify doctor's signature on credential
    doctor_did = credential['issuer']
    doctor_doc = await resolve_did(doctor_did)
    doctor_valid = await verify_credential_signature(credential, doctor_doc)
    
    if not doctor_valid:
        return {'valid': False, 'reason': 'Invalid doctor signature'}
    
    # 4. Verify patient's signature on presentation
    patient_id = presentation['holder']
    presentation_valid = await verify_presentation_signature(presentation)
    
    if not presentation_valid:
        return {'valid': False, 'reason': 'Invalid patient signature'}
    
    # 5. Check trust registry
    doctor_trusted = await check_trust_registry(doctor_did)
    
    # 6. Check prescription expiration
    prescription_expires = datetime.fromisoformat(
        credential['credentialSubject']['validUntil']
    )
    if now > prescription_expires:
        return {'valid': False, 'reason': 'Prescription expired'}
    
    # 7. All checks passed
    return {
        'valid': True,
        'prescription': credential['credentialSubject'],
        'doctor': doctor_doc.get('name'),
        'patient': credential['credentialSubject']['patientName'],
        'warnings': [] if doctor_trusted else ['Doctor not in trust registry']
    }
```

### QR Code Display (Patient)
```typescript
// React Native QR Display
import QRCode from 'react-native-qrcode-svg';

const PrescriptionShareScreen = ({ prescription }) => {
  const [qrData, setQRData] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(15 * 60); // 15 minutes
  
  useEffect(() => {
    generatePresentationQR(prescription.id);
    
    // Countdown timer
    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <View>
      <Text>Share with Pharmacist</Text>
      {qrData && (
        <>
          <QRCode value={qrData} size={300} />
          <Text>Expires in: {formatTime(timeRemaining)}</Text>
          {timeRemaining === 0 && (
            <Button onPress={regenerateQR}>Regenerate QR Code</Button>
          )}
        </>
      )}
    </View>
  );
};
```

## Notes

### Technical Constraints
- QR code must contain full verifiable presentation
- Presentation size limited by QR capacity (~2953 bytes)
- Use URL fallback if presentation too large
- Time-limited validity (15 minutes) prevents replay
- No network required for basic verification (offline capable)

### Privacy Controls
- Patient shares entire prescription (no selective disclosure in MVP)
- Future: Support BBS+ signatures for selective disclosure
- Pharmacist cannot forward prescription (patient signature tied to timestamp)
- Presentation expires automatically after 15 minutes
- No audit trail sent back to patient or doctor

### Security Features
- Patient's signature proves possession of credential
- Nonce/challenge prevents replay attacks
- Timestamp ensures freshness
- Doctor's signature verified by pharmacist
- Trust registry check for doctor verification
- Optional revocation check (requires network)

### In-Person Flow
1. Patient arrives at pharmacy
2. Patient opens wallet → selects prescription → "Share"
3. QR code displayed on patient's screen
4. Pharmacist scans QR with verification app
5. Pharmacist sees verification results immediately
6. Pharmacist dispenses medications
7. Patient closes wallet (done)

### Demo Simplifications
- No selective disclosure (share full prescription)
- Pre-configured test pharmacies (no pharmacy directory)
- QR code expiration disabled in demo mode
- Simplified trust registry (allow any doctor)
- No revocation checking in MVP
- Instant verification (no loading states)

### Error Handling
- QR generation fails: Show error, retry button
- Presentation expired: Auto-regenerate or show "Regenerate" button
- Pharmacist reports invalid QR: Patient regenerates fresh QR
- Network error during verification: Pharmacist sees warning, can proceed
- Trust registry unavailable: Warn but allow verification

### Performance
- QR generation: <500ms
- QR display: Immediate
- Pharmacist scan: <2 seconds
- Verification: <3 seconds (with network)
- Verification: <1 second (offline mode)

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-006: Receive Prescription in Wallet (prerequisite)
- US-007: View Prescription Details (prerequisite)
- US-009: Pharmacist Authentication & DID Setup (pharmacy side)
- US-010: Verify Prescription Authenticity (pharmacy side)
- US-018: DIDComm v2 Messaging (future replacement)
