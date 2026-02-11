## Title
Revoke or Cancel Prescription

## User Story
As a doctor, I want to be able to revoke or cancel a prescription I've issued, so that if I discover an error, the patient's condition changes, or for safety reasons, the prescription can be invalidated and prevented from being dispensed.

## Description
Prescription revocation is a critical safety feature. Doctors may need to cancel prescriptions due to errors (wrong medication, dosage, or patient), adverse reactions, changes in diagnosis, or patient misuse concerns. Once revoked, the prescription becomes invalid and cannot be dispensed at any pharmacy.

## Context

## Acceptance Criteria

### Revocation Authorization
- [ ] Only the issuing doctor can revoke their prescriptions
- [ ] System verifies doctor's identity before allowing revocation
- [ ] Revocation requires explicit confirmation
- [ ] Reason for revocation must be provided
- [ ] Timestamp recorded for all revocations

### Revocation Reasons
Doctor must select reason:
- [ ] Incorrect medication prescribed
- [ ] Incorrect dosage/strength
- [ ] Wrong patient
- [ ] Drug interaction discovered
- [ ] Allergic reaction reported
- [ ] Patient condition changed
- [ ] Duplicate prescription
- [ ] Patient request
- [ ] Safety concern
- [ ] Other (specify)

### Revocation Process
- [ ] Doctor views issued prescriptions list
- [ ] Doctor selects prescription to revoke
- [ ] System shows prescription details for confirmation
- [ ] Doctor selects revocation reason
- [ ] Doctor enters additional notes (optional)
- [ ] Doctor confirms revocation with password/re-authentication
- [ ] System publishes revocation to ledger
- [ ] Revocation credential created
- [ ] Revocation status updated in real-time

### Immediate Effect
- [ ] Prescription status immediately changes to "Revoked"
- [ ] Revocation published to revocation registry
- [ ] Verifiers can query revocation status
- [ ] Timestamp of revocation recorded immutably
- [ ] Prescription becomes invalid for all future verification attempts

### Patient Notification
- [ ] Patient receives immediate notification of revocation
- [ ] Notification includes reason category
- [ ] Patient advised to destroy or disregard prescription
- [ ] If prescription already at pharmacy, patient notified to collect it
- [ ] Option for doctor to include explanatory message

### Pharmacist Handling
- [ ] Revoked prescriptions fail verification
- [ ] Pharmacist sees clear "REVOKED" status
- [ ] Revocation reason displayed to pharmacist
- [ ] Revocation timestamp shown
- [ ] Pharmacist cannot proceed with dispensing
- [ ] Pharmacist advised to contact doctor if needed

### Revocation Display

#### Patient Wallet View (Revoked)
```
┌─────────────────────────────────────────────┐
│ ❌ PRESCRIPTION REVOKED                     │
│                                             │
│ Prescription #RX-20260211-abc123            │
│                                             │
│ This prescription was revoked by:           │
│ Dr. Jane Smith                              │
│                                             │
│ Revocation Date: 12 Feb 2026 09:15 AM       │
│                                             │
│ Reason: Drug interaction discovered         │
│                                             │
│ Note: Alternative prescription issued.      │
│       Please check your wallet.             │
│                                             │
│ [View Replacement Prescription]             │
└─────────────────────────────────────────────┘
```

#### Pharmacist Verification View (Revoked)
```
┌─────────────────────────────────────────────┐
│ ❌ VERIFICATION FAILED - REVOKED            │
│                                             │
│ This prescription has been REVOKED          │
│ by the issuing doctor and cannot be         │
│ dispensed.                                  │
│                                             │
│ Revoked by: Dr. Jane Smith                  │
│ Revocation Date: 12 Feb 2026 09:15 AM       │
│                                             │
│ Reason: Drug interaction discovered         │
│                                             │
│ ⚠️ DO NOT DISPENSE                          │
│                                             │
│ [Contact Doctor] [Return to Queue]          │
└─────────────────────────────────────────────┘
```

### Replacement Prescription
- [ ] Doctor can issue replacement after revocation
- [ ] System links replacement to revoked prescription
- [ ] Patient notified of replacement
- [ ] Historical record shows revocation and replacement

### Partial Revocation (Future)
- [ ] Future: Revoke specific medications from multi-item prescription
- [ ] Other items remain valid
- [ ] Patient notified which items were revoked

### Emergency Revocation
- [ ] Emergency hotline for urgent revocations
- [ ] Pharmacist can flag suspicious prescriptions
- [ ] Rapid revocation process for safety concerns
- [ ] Immediate broadcast to all pharmacies

## API Integration Points

```
POST https://cloudapi.test.didxtech.com/tenant/v1/issuer/revoke
GET  https://cloudapi.test.didxtech.com/tenant/v1/issuer/revocation/status/{id}
POST /api/v1/prescriptions/{id}/revoke (internal)
GET  /api/v1/prescriptions/{id}/revocation-status (internal)
```

## Notes

### Technical Implementation
- Use Status List 2021 for efficient revocation checking
- Publish revocation to cheqd ledger
- Implement CRL (Certificate Revocation List) as fallback
- Real-time revocation status queries
- Cache revocation status with short TTL

### Revocation Data Model
```json
{
  "revocation": {
    "revoked": true,
    "revokedBy": "did:cheqd:testnet:doctor-did",
    "revocationDate": "2026-02-12T09:15:00Z",
    "reason": "drug_interaction_discovered",
    "reasonDescription": "Discovered interaction with patient's current medication",
    "replacementPrescriptionId": "RX-20260212-def456"
  }
}
```

### Legal and Safety
- Revocation is permanent and binding
- Doctor has legal duty to revoke erroneous prescriptions
- Pharmacist must verify revocation status before dispensing
- Malicious revocation by doctor is auditable and traceable

### Audit Trail
- All revocation events logged
- Immutable record on distributed ledger
- Include: who, when, why, prescription ID
- Report available for regulatory review

### Recovery
- If revoked in error, doctor issues new prescription
- No "unrevoke" function (prevents abuse)
- Historical record preserved even after reissue

### Demo Simplifications
- Instant revocation propagation
- Mock emergency hotline
- Pre-configured revocation scenarios
- Visual demonstration of before/after

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-003: Sign Prescription with Digital Signature (prerequisite)
- US-010: Verify Prescription Authenticity (checks revocation)
- US-002: Create Digital Prescription (original issuance)
