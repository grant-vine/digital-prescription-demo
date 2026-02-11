## Title
Support Prescription Repeats/Refills

## User Story
As a patient with chronic medication needs, I want my digital prescription to support repeats/refills, so that I can obtain additional supplies of my medication without visiting the doctor each time, within the limits set by my doctor.

## Description
Many prescriptions, especially for chronic conditions, include authorization for repeats (also called refills). The doctor specifies how many times the prescription can be filled and any interval restrictions. The system must track repeat usage, enforce interval rules, and update the prescription status after each dispensing.

## Context

## Acceptance Criteria

### Repeat Configuration
- [ ] Doctor can specify number of repeats when creating prescription (0-5)
- [ ] Doctor can set minimum interval between repeats
- [ ] Doctor can set maximum quantity per repeat
- [ ] System displays repeat information clearly to patient
- [ ] Patient sees total authorized supply (initial + repeats)

### Repeat Tracking
- [ ] System tracks each dispensing event
- [ ] Remaining repeats calculated automatically
- [ ] Last dispense date recorded
- [ ] Next available repeat date calculated
- [ ] Prescription status updates based on repeats:
  - Active (repeats remaining)
  - Final Repeat (1 repeat remaining)
  - Completed (no repeats remaining)

### Patient View of Repeats
- [ ] Patient sees repeats remaining in wallet
- [ ] Visual indicator shows repeat status
- [ ] Patient can see dispensing history
- [ ] Next repeat date displayed
- [ ] Countdown to next available repeat shown

### Repeat Eligibility Validation
- [ ] System validates repeat request against:
  - Repeats remaining > 0
  - Minimum interval since last dispensing
  - Prescription not expired
  - Prescription not revoked
- [ ] Patient informed if repeat not yet available
- [ ] Days until next repeat calculated and displayed

### Repeat Dispensing Flow

#### First Dispense (Original)
```
Prescription: 3 repeats authorized
Status: Active (3 repeats remaining)
Pharmacist: Dispenses original
System: Records dispensing
        Updates status: Active (3 repeats remaining → 2 after dispensing)
```

#### Subsequent Repeat
```
Patient: Shares prescription for repeat
Pharmacist: Receives prescription
System: Validates:
         - Repeats remaining: 2
         - Days since last dispense: 32
         - Minimum interval: 28 days
         - Status: ELIGIBLE
Pharmacist: Dispenses repeat
System: Records dispensing
        Updates repeats remaining: 1
        Updates last dispense date
```

#### Final Repeat
```
System: Repeats remaining reaches 0
Status: Changes to "Completed"
Notification: Sent to patient
Message: "All repeats used. Contact doctor for new prescription."
```

### Interval Enforcement
- [ ] Standard interval: 75% of days supply (e.g., 30-day supply = 23-day minimum interval)
- [ ] Doctor can specify custom minimum interval
- [ ] System calculates: Next available date = Last dispense + Minimum interval
- [ ] Early repeat requests blocked with clear message

### Partial Fills
- [ ] Pharmacist can record partial dispensing
- [ ] Partial quantities tracked
- [ ] Remaining quantity from original still available
- [ ] Patient informed of partial fill

### Repeat Status Display

#### Patient Wallet View
```
┌─────────────────────────────────────────────┐
│ PRESCRIPTION #RX-20260211-abc123            │
│                                             │
│ Repeats: 1 of 3 remaining                   │
│ ▓▓▓▓░░░░░░ (33% used)                       │
│                                             │
│ Last dispensed: 15 March 2026               │
│ Next repeat available: 12 April 2026        │
│ (In 15 days)                                │
│                                             │
│ Status: Active                              │
└─────────────────────────────────────────────┘
```

#### Pharmacist View
```
┌─────────────────────────────────────────────┐
│ REPEAT AUTHORIZATION                        │
│                                             │
│ Original Issue: 11 Feb 2026                 │
│ Repeats Authorized: 3                       │
│ Repeats Used: 2                             │
│ Repeats Remaining: 1                        │
│                                             │
│ Dispensing History:                         │
│ • 11 Feb 2026 - Original (30 tablets)       │
│ • 15 Mar 2026 - Repeat #1 (30 tablets)      │
│                                             │
│ ✓ Eligible for repeat dispensing            │
│                                             │
│ [Proceed with Dispensing]                   │
└─────────────────────────────────────────────┘
```

### Doctor Notification
- [ ] Doctor notified when final repeat is used
- [ ] Optional: Doctor notified on each repeat dispensing
- [ ] Notification includes patient name and medication
- [ ] Doctor can view full dispensing history

### Prescription Renewal
- [ ] When repeats exhausted, patient can request renewal
- [ ] System pre-populates renewal request with previous prescription details
- [ ] Doctor can approve renewal with single click
- [ ] New prescription issued with fresh repeat authorization

### Emergency Override
- [ ] Emergency repeat override capability
- [ ] Requires doctor approval
- [ ] Pharmacist can request emergency override with justification
- [ ] Doctor receives urgent notification
- [ ] Approved override bypasses interval restriction

## API Integration Points

```
GET  /api/v1/prescriptions/{id}/repeats
POST /api/v1/prescriptions/{id}/record-dispensing
GET  /api/v1/prescriptions/{id}/dispensing-history
POST /api/v1/prescriptions/{id}/request-emergency-override
```

## Notes

### Regulatory Compliance
- Follow SAPC guidelines for repeat dispensing
- Comply with Medical Schemes Act for chronic medication
- Adhere to HPCSA repeat prescription policies
- Track all dispensing for regulatory reporting

### Data Model
```json
{
  "repeats": {
    "authorized": 3,
    "remaining": 1,
    "minimumIntervalDays": 28,
    "dispensingHistory": [
      {
        "date": "2026-02-11",
        "type": "original",
        "quantity": 30,
        "pharmacy": "..."
      },
      {
        "date": "2026-03-15",
        "type": "repeat",
        "quantity": 30,
        "pharmacy": "..."
      }
    ]
  }
}
```

### Safety Considerations
- Monitor for repeat abuse patterns
- Flag excessive early repeat requests
- Track medication adherence through dispensing dates
- Alert doctor if patient not collecting repeats regularly

### Demo Simplifications
- Pre-populated dispensing history for demo
- Accelerated time for repeat availability
- Visual progress bars for demonstration
- Sample repeat scenarios

## Estimation
- **Story Points**: 8
- **Time Estimate**: 3-4 days

## Related Stories
- US-002: Create Digital Prescription (sets repeats)
- US-011: View Prescription Items for Dispensing
- US-012: Time-Based Prescription Validation
