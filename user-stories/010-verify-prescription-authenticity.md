## Title
Verify Prescription Authenticity

## User Story
As a pharmacist receiving a prescription from a patient, I want to verify that the prescription is authentic, issued by a licensed doctor, hasn't been tampered with, and hasn't expired or been revoked, so that I can confidently dispense medications legally and safely.

## Description
Verification is the critical security step in the digital prescription workflow. The pharmacist's system checks the digital signature, validates the doctor's credentials against the trust registry, verifies the prescription hasn't expired or been revoked, and ensures all data integrity. This process happens automatically when a prescription is received.

## Acceptance Criteria

### Automatic Verification on Receipt
- [ ] System automatically verifies prescription when received
- [ ] Verification happens before displaying to pharmacist
- [ ] Progress indicator shows verification steps
- [ ] Results displayed clearly (pass/fail for each check)

### Digital Signature Verification
- [ ] Extract signature from verifiable credential proof
- [ ] Verify signature using doctor's public key from DID document
- [ ] Confirm signature algorithm and proof type
- [ ] Verify proof purpose (assertionMethod)
- [ ] Check signature timestamp

### Doctor Verification
- [ ] Resolve doctor's DID to retrieve DID document
- [ ] Query trust registry for doctor's license status
- [ ] Verify doctor is authorized to prescribe medications
- [ ] Check doctor's credentials are current (not expired)
- [ ] Display doctor's verified information:
  - Name and registration number
  - Practice details
  - Specialization (if applicable)
  - License status

### Prescription Integrity Checks
- [ ] Verify prescription data hash matches signature
- [ ] Check prescription hasn't been altered since issuance
- [ ] Validate all required fields are present
- [ ] Verify prescription format compliance

### Expiration and Validity Checks
- [ ] Check prescription issue date is in the past
- [ ] Check prescription validity period hasn't expired
- [ ] Display days until expiration
- [ ] Warn if prescription expires within 7 days
- [ ] Reject expired prescriptions with clear reason

### Revocation Check
- [ ] Check prescription against revocation registry
- [ ] Verify status is "active" (not revoked or suspended)
- [ ] Query revocation status from issuer's agent
- [ ] Display revocation reason if applicable
- [ ] Log all revocation checks

### Verification Result Display
```
┌─────────────────────────────────────────┐
│ PRESCRIPTION VERIFICATION               │
├─────────────────────────────────────────┤
│ ✓ Digital Signature Valid               │
│   Signed by: Dr. Jane Smith             │
│   Date: 2026-02-11 11:42 AM             │
│                                         │
│ ✓ Doctor Verified                       │
│   Registration: MP12345                 │
│   Status: Active and Licensed           │
│                                         │
│ ✓ Prescription Not Revoked              │
│   Status: Active                        │
│                                         │
│ ✓ Validity Check                        │
│   Valid until: 2026-05-11               │
│   Days remaining: 89                    │
│                                         │
│ ✓ Data Integrity                        │
│   No tampering detected                 │
├─────────────────────────────────────────┤
│ OVERALL: ✓ VERIFIED - SAFE TO DISPENSE  │
└─────────────────────────────────────────┘
```

### Failed Verification Handling
- [ ] Clear error messages for each type of failure
- [ ] Option to retry verification
- [ ] Fallback to manual verification process
- [ ] Contact doctor option for disputed prescriptions
- [ ] Report suspicious prescription functionality

### Verification API
```
POST https://cloudapi.test.didxtech.com/tenant/v1/verifier/verify
Request:
{
  "verifiablePresentation": {...},
  "options": {
    "challenge": "nonce-sent-to-patient",
    "domain": "pharmacy.example.com"
  }
}

Response:
{
  "verified": true,
  "checks": [
    {"check": "signature", "result": "passed"},
    {"check": "issuer", "result": "passed", "details": {...}},
    {"check": "revocation", "result": "passed"},
    {"check": "expiration", "result": "passed"}
  ],
  "prescription": {...},
  "errors": []
}
```

## API Integration Points

```
POST https://cloudapi.test.didxtech.com/tenant/v1/verifier/verify
GET  https://cloudapi.test.didxtech.com/tenant/v1/trust-registry/verify/{did}
GET  https://cloudapi.test.didxtech.com/tenant/v1/issuer/revocation/status/{id}
GET  https://resolver.cheqd.net/1.0/identifiers/{did}
```

## Notes

### Technical Constraints
- Verification must complete within 3 seconds
- Support offline verification using cached trust registry
- Handle network failures gracefully
- Implement retry logic for transient errors

### Security Considerations
- All verification steps must be cryptographically sound
- No trust on first use - always verify
- Independent verification of each component
- Tamper-evident audit trail

### Trust Registry
- Cache trust registry entries (TTL: 1 hour)
- Support multiple trust registries
- Fallback to primary source if cache stale
- Handle trust registry unavailability

### Revocation Mechanisms
- Support status list 2021 for efficient revocation checking
- CRL (Certificate Revocation List) fallback
- Real-time revocation queries
- Batch revocation checking for performance

### Audit Requirements
- Log all verification attempts
- Store verification results with timestamp
- Include prescription ID and pharmacist ID
- Retain logs per regulatory requirements

### Demo Simplifications
- Instant verification (no network delay)
- Pre-populated trust registry
- Mock revocation data
- Always succeed in happy path demo

### Performance Optimization
- Parallel verification checks where possible
- Cache DID documents
- Optimize signature verification
- Pre-fetch trust registry updates

## Estimation
- **Story Points**: 8
- **Time Estimate**: 3-4 days

## Related Stories
- US-003: Sign Prescription with Digital Signature (issuance)
- US-008: Share Prescription with Pharmacist (prerequisite)
- US-011: View Prescription Items for Dispensing (next step)
- US-015: Revoke or Cancel Prescription (revocation mechanism)
