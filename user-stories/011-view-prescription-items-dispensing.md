## Title
View Prescription Items for Dispensing

## User Story
As a pharmacist who has verified a prescription's authenticity, I want to view the detailed medication items, quantities, and dispensing instructions, so that I can prepare and issue the correct medications to the patient.

## Description
After successful verification, the pharmacist sees the full prescription details needed for dispensing. This includes each medication, exact quantities, dosage instructions, and any special notes from the doctor. The interface guides the pharmacist through the dispensing process with checks and confirmations.

## Context

## Acceptance Criteria

### Prescription Header Display
- [ ] Show prescription ID and verification status badge
- [ ] Display doctor information (name, practice, contact)
- [ ] Show patient information (name, ID number last 4 digits)
- [ ] Display prescription date and validity period
- [ ] Show number of repeats and repeats remaining
- [ ] Indicate if this is an original or repeat dispensing

### Medication Line Items
For each medication:
- [ ] Display medication name (generic and brand if applicable)
- [ ] Show strength/concentration (e.g., "500mg")
- [ ] Display exact quantity to dispense
- [ ] Show dosage instructions clearly
- [ ] Display route of administration
- [ ] Show duration of treatment
- [ ] Include any special instructions or warnings
- [ ] Display SAHPRA registration number

### Dispensing Interface
- [ ] Checklist for each medication item
- [ ] Pharmacist marks each item as "prepared"
- [ ] Barcode scanning to verify correct medication (if scanner available)
- [ ] Quantity confirmation input
- [ ] Batch/lot number capture (optional, for demo)
- [ ] Expiry date capture (optional, for demo)

### Safety Checks
- [ ] System warns about potential drug interactions
- [ ] Allergy alerts displayed prominently
- [ ] Contraindication warnings
- [ ] Duplicate therapy alerts
- [ ] Pediatric dosing alerts (if applicable)
- [ ] Pregnancy/lactation warnings

### Professional Notes Section
- [ ] Display doctor's special instructions
- [ ] Show any patient counseling points
- [ ] Space for pharmacist to add notes
- [ ] Flag for generic substitution allowed/prohibited
- [ ] Special storage requirements

### Repeat Information
- [ ] Clear display of repeats remaining
- [ ] Show repeat interval restrictions
- [ ] Display when next repeat is available
- [ ] Option to note partial fills
- [ ] Track repeat history

### Dispensing Actions
- [ ] "Mark as Dispensed" button (enabled when all items prepared)
- [ ] "Partial Dispense" option with reason
- [ ] "Decline to Dispense" with reason selection:
  - Out of stock
  - Patient declined
  - Safety concern
  - Other (specify)
- [ ] "Contact Doctor" button

### Patient Counseling
- [ ] Display counseling points for each medication
- [ ] Checklist for pharmacist to confirm counseling given
- [ ] Space to record patient questions/concerns
- [ ] Option to schedule follow-up

### Display Layout
```
┌─────────────────────────────────────────────┐
│ PRESCRIPTION #RX-20260211-abc123     ✓ VERIFIED │
│ Dr. Jane Smith | Cape Town Medical Practice     │
│ Patient: John Doe (ID: ****1234)               │
│ Valid until: 2026-05-11 | Repeats: 2 of 3      │
├─────────────────────────────────────────────┤
│ MEDICATION 1 OF 2                            │
│ ☑ Amoxicillin 500mg Capsules                 │
│   Quantity: 21 capsules                      │
│   Instructions: Take 1 capsule 3 times daily │
│   For: 7 days                                │
│   ⚠️ Take with food                          │
│   [✓] Prepared                               │
│                                              │
│ MEDICATION 2 OF 2                            │
│ ☐ Paracetamol 500mg Tablets                  │
│   Quantity: 24 tablets                       │
│   Instructions: Take 2 tablets every 6 hours │
│   [ ] Prepared                               │
├─────────────────────────────────────────────┤
│ Professional Notes:                          │
│ - Complete full course of antibiotics        │
│ - May cause drowsiness                       │
├─────────────────────────────────────────────┤
│ [Mark as Dispensed] [Partial] [Decline]     │
└─────────────────────────────────────────────┘
```

## API Integration Points

```
GET  https://cloudapi.test.didxtech.com/tenant/v1/credentials/{id}
POST /api/v1/dispensing/record (internal)
POST /api/v1/dispensing/complete (internal)
```

## Notes

### Technical Constraints
- Read-only access to prescription data
- All dispensing actions logged
- Integration with pharmacy management system (future)
- Support for barcode scanning

### Safety Features
- Double-check all quantities
- Visual confirmation of medication names
- Warning highlights for high-risk medications
- Required fields must be completed

### Workflow Integration
- Queue management for high-volume pharmacies
- Priority flagging for urgent prescriptions
- Integration with stock management
- Label printing integration (future)

### Demo Simplifications
- Manual medication selection (no barcode scanning)
- Mock drug interaction database
- No integration with external pharmacy systems
- Simplified dispensing workflow

### Compliance Requirements
- All dispensing actions recorded
- Pharmacist ID captured for each action
- Timestamp for all events
- Audit trail for regulatory inspection

### Multi-Language Support
- Medication names in English with local language option
- Instructions translated where available
- Professional notes remain in doctor's language

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-010: Verify Prescription Authenticity (prerequisite)
- US-014: Support Prescription Repeats/Refills
- US-016: Audit Trail & Compliance Logging
