## Title
Sign Prescription with Digital Signature

## User Story
As a doctor who has created a prescription, I want to digitally sign it using my cryptographic keys, so that the prescription becomes tamper-proof and verifiable by any pharmacist.

## Description
Digital signing transforms a draft prescription into a valid, legally-binding verifiable credential. The doctor's private key creates a cryptographic signature that proves the prescription was issued by an authenticated doctor and has not been altered. This signature is the foundation of trust in the entire system.

## Context
Digital signing transforms a draft prescription into a valid, legally-binding verifiable credential. The doctor's private key (associated with their DID) creates a cryptographic signature that proves the prescription was issued by an authenticated doctor and has not been altered. This signature is the foundation of trust in the entire system.

## Acceptance Criteria

### Signature Process
- [ ] Doctor reviews complete prescription before signing
- [ ] System displays warning about legal responsibility
- [ ] Doctor confirms intent to sign (explicit action required)
- [ ] System retrieves doctor's private key from secure wallet
- [ ] Prescription data is serialized in a canonical format (JSON-LD)
- [ ] Cryptographic signature is generated using Ed25519 algorithm
- [ ] Signature is embedded in the verifiable credential proof
- [ ] Signed prescription is ready for issuance

### Verifiable Credential Structure
The signed prescription must follow W3C Verifiable Credentials Data Model v2.0:
```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://didx.co.za/schemas/medical-prescription/v1"
  ],
  "type": ["VerifiableCredential", "MedicalPrescription"],
  "issuer": "did:cheqd:testnet:doctor-did",
  "issuanceDate": "2026-02-11T11:42:00Z",
  "credentialSubject": {
    "id": "did:cheqd:testnet:patient-did",
    "prescription": {
      "prescriptionId": "RX-20260211-abc123",
      "medications": [...],
      "diagnosis": "J06.9",
      "issuedDate": "2026-02-11",
      "validUntil": "2026-05-11",
      "repeatsAllowed": 2
    }
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-02-11T11:42:30Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:cheqd:testnet:doctor-did#key-1",
    "proofValue": "z58DAdF...base58-encoded-signature"
  }
}
```

### Signature Verification
- [ ] System verifies the signature immediately after creation
- [ ] Verification confirms prescription data integrity
- [ ] Doctor receives confirmation of successful signing
- [ ] Failed signatures show clear error messages

### Security Measures
- [ ] Private key never leaves the wallet context
- [ ] Signing operation requires active session
- [ ] All signing events are logged with timestamp
- [ ] Doctor must re-authenticate if session expired
- [ ] PIN or biometric confirmation required (for demo, use confirmation dialog)

### Post-Signing State
- [ ] Prescription status changes from "draft" to "signed"
- [ ] Signed prescription is locked from further editing
- [ ] Doctor can view the signed credential in JSON format
- [ ] QR code is generated representing the prescription

## API Integration Points

```
POST https://cloudapi.test.didxtech.com/tenant/v1/issuer/credentials
POST https://cloudapi.test.didxtech.com/tenant/v1/verifier/verify
```

## Notes

### Technical Constraints
- Use Ed25519 for digital signatures (Hyperledger Aries default)
- Follow LD-proofs specification for linked data signatures
- Include proof purpose: assertionMethod
- Credential must be revocable (set up revocation registry)

### Cryptographic Details
- Algorithm: Ed25519
- Proof type: Ed25519Signature2020
- Canonicalization: RDF Dataset Canonicalization (URDNA2015)
- Hash: SHA-256

### Legal Considerations
- Digital signature must meet Electronic Communications and Transactions Act (ECTA) requirements
- Signature proves doctor's intent and accountability
- Timestamp must be from a trusted time source

### Demo Simplifications
- Use testnet DIDs and keys
- Provide "Demo Mode" with pre-generated test prescriptions
- Allow "unsign" for testing purposes (not possible in production)

### Error Handling
- Clear error if private key unavailable
- Retry mechanism for network failures
- Backup option if DIDx API temporarily unavailable

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-001: Doctor Authentication & DID Setup (prerequisite)
- US-002: Create Digital Prescription (prerequisite)
- US-010: Verify Prescription Authenticity (verification counterpart)
