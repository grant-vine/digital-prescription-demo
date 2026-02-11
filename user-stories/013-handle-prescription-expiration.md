## Title
Handle Prescription Expiration

## User Story
As a patient or pharmacist, I want the system to handle prescription expiration gracefully, providing clear notifications, preventing dispensing of expired prescriptions, and offering guidance on next steps when a prescription expires.

## Description
Prescriptions expire for patient safety and regulatory reasons. When a prescription expires, it can no longer be legally dispensed. The system must clearly communicate expiration status, prevent accidental dispensing, and guide users on how to obtain a new prescription if needed.

## Context

## Acceptance Criteria

### Expiration Detection
- [ ] System automatically detects expired prescriptions
- [ ] Expiration checked on every access attempt
- [ ] Background job marks expired prescriptions daily
- [ ] Expiration timestamp recorded with timezone

### Patient Experience
- [ ] Expired prescriptions visually marked in wallet (red indicator)
- [ ] Expiration date clearly displayed
- [ ] Message: "This prescription has expired and can no longer be used"
- [ ] Action button: "Request New Prescription from Doctor"
  - Opens messaging interface to doctor
  - Pre-populates with expired prescription reference
- [ ] Option to archive expired prescription
- [ ] Historical record maintained for patient records

### Pharmacist Experience
- [ ] Expired prescriptions rejected at verification stage
- [ ] Clear error message: "Prescription expired on [date]"
- [ ] Days overdue displayed
- [ ] Option to contact doctor on patient's behalf
- [ ] Suggestion to request new prescription
- [ ] Cannot proceed to dispensing view for expired prescriptions

### Expiration Notification
- [ ] Patient receives notification 7 days before expiration
- [ ] Patient receives notification 24 hours before expiration
- [ ] Notification includes quick action to contact doctor
- [ ] Notification respects user's quiet hours preference

### Expiration Scenarios

#### Scenario 1: Patient Tries to Use Expired Prescription
```
Patient: Opens expired prescription in wallet
System: Shows "EXPIRED" banner
        Displays expiration date
        Disables "Share with Pharmacy" button
        Shows "Request Renewal" button
Patient: Clicks "Request Renewal"
System: Opens message to doctor
        Includes reference to expired prescription
        Patient can add notes
```

#### Scenario 2: Pharmacist Receives Expired Prescription
```
Pharmacist: Receives prescription from patient
System: Verification fails with "EXPIRED" error
         Shows expiration date
         Displays doctor contact information
Pharmacist: Can click "Contact Doctor" 
            Or inform patient to get new prescription
```

#### Scenario 3: Prescription Expires While Pending
```
Patient: Shares prescription with pharmacy
         Prescription is in "pending" queue
System: Background job checks daily
         Marks prescription expired if past validity
Pharmacist: Sees prescription in queue marked EXPIRED
            Cannot process
Patient: Receives notification that prescription expired
```

### Expiration Handling Interface

#### Patient Wallet View (Expired)
```
┌─────────────────────────────────────────────┐
│ ⚠️ PRESCRIPTION EXPIRED                     │
│                                             │
│ Prescription #RX-20260211-abc123            │
│                                             │
│ This prescription expired on:               │
│ 11 May 2026 (5 days ago)                    │
│                                             │
│ It can no longer be used at a pharmacy.     │
│                                             │
│ [Request New Prescription]                  │
│ [View History] [Archive]                    │
└─────────────────────────────────────────────┘
```

#### Pharmacist View (Expired Prescription Attempt)
```
┌─────────────────────────────────────────────┐
│ ❌ VERIFICATION FAILED                      │
│                                             │
│ This prescription has EXPIRED               │
│                                             │
│ Expiration Date: 11 May 2026                │
│ Days Overdue: 5                             │
│                                             │
│ Cannot dispense expired prescriptions.      │
│ Please request a new prescription.          │
│                                             │
│ [Contact Doctor] [Return to Queue]          │
└─────────────────────────────────────────────┘
```

### Expiration Extensions
- [ ] Emergency expiration extension capability
- [ ] Only doctor can extend expiration
- [ ] Extension requires justification
- [ ] Maximum extension: 30 days
- [ ] Audit trail for all extensions

### Archiving Expired Prescriptions
- [ ] Patient can archive expired prescriptions
- [ ] Archived prescriptions moved to "History" section
- [ ] Still viewable but clearly marked as historical
- [ ] Included in medication history reports
- [ ] Auto-archive after 90 days (configurable)

### Statistical Reporting
- [ ] Track expiration rates
- [ ] Analyze time-to-expiration patterns
- [ ] Identify frequently expiring prescriptions
- [ ] Report on renewal request patterns

## API Integration Points

```
GET  /api/v1/prescriptions/expired
POST /api/v1/prescriptions/{id}/archive
POST /api/v1/prescriptions/{id}/request-renewal
POST /api/v1/prescriptions/{id}/extend (doctor only)
```

## Notes

### Legal Considerations
- Expired prescriptions cannot be legally dispensed in South Africa
- No exceptions except emergency provisions (separate process)
- Patient must obtain new prescription from doctor
- Pharmacist has legal duty to refuse expired prescriptions

### User Experience
- Empathetic messaging (not punitive)
- Clear next steps provided
- Easy path to renewal
- Preserve patient dignity

### Technical Implementation
- Daily cron job to mark expired prescriptions
- Event-driven architecture for real-time updates
- Efficient querying of expiration status
- Timezone-aware calculations

### Demo Considerations
- Include sample expired prescriptions
- Demonstrate renewal request flow
- Show pharmacist rejection handling
- Time acceleration for testing

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-012: Time-Based Prescription Validation
- US-002: Create Digital Prescription (sets expiration)
- US-007: View Prescription Details (shows expiration)
