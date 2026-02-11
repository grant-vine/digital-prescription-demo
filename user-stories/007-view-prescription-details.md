## Title
View Prescription Details

## User Story
As a patient with prescriptions in my wallet, I want to view detailed information about each prescription including medications, dosage instructions, and validity, so that I can understand my treatment and manage my medications effectively.

## Description
The prescription detail view provides comprehensive information about a specific prescription. This includes all medications, dosage schedules, special instructions, doctor contact information, and metadata like issue date and expiration. The view also shows the prescription's current status and any relevant warnings.

## Acceptance Criteria

### Prescription Header
- [ ] Display prescription ID prominently
- [ ] Show issuing doctor's name and practice
- [ ] Display doctor's contact information
- [ ] Show issue date and time
- [ ] Display validity period (start and end dates)
- [ ] Show current status: Active, Partially Used, Completed, Expired, Cancelled

### Medication Details
For each medication in the prescription:
- [ ] Medication name and strength
- [ ] Generic and brand names
- [ ] Dosage instructions (plain language)
- [ ] Quantity prescribed
- [ ] Route of administration
- [ ] Duration of treatment
- [ ] Visual medication icon or image
- [ ] Link to medication information leaflet (mock)

### Dosage Schedule
- [ ] Visual representation of dosage timing
- [ ] Daily schedule view (morning, afternoon, evening)
- [ ] Calendar view for multi-day treatments
- [ ] Reminder setup option (push notification)
- [ ] Check-off boxes for tracking doses taken

### Repeat/Refill Information
- [ ] Show number of repeats originally allowed
- [ ] Display repeats remaining
- [ ] Show repeat interval restrictions
- [ ] Indicate if repeat is currently available
- [ ] Button to request repeat (if applicable)

### Safety Information
- [ ] Display patient's known allergies
- [ ] Highlight any contraindications
- [ ] Show drug interaction warnings
- [ ] Special instructions (take with food, etc.)
- [ ] Storage requirements

### Actions Available
- [ ] Share prescription with pharmacy
- [ ] Download/print prescription PDF
- [ ] Contact doctor
- [ ] Mark as completed (patient tracking)
- [ ] Archive prescription

### Verification Section
- [ ] Display prescription QR code for pharmacy scanning
- [ ] Show "Verify Authenticity" button
- [ ] Display verification status (✓ Valid)
- [ ] Show revocation status if applicable

### Expiration Warnings
- [ ] Visual warning if prescription expires within 7 days
- [ ] Warning if prescription has expired
- [ ] Information about validity extension (if applicable)

## Display Structure

```
┌─────────────────────────────────────┐
│ Prescription #RX-20260211-abc123    │
│ Status: ● Active                    │
├─────────────────────────────────────┤
│ From: Dr. Jane Smith                │
│ Cape Town Medical Practice          │
│ Tel: 021-555-0123                   │
├─────────────────────────────────────┤
│ Valid: 11 Feb 2026 - 11 May 2026    │
│ Expires in: 87 days                 │
├─────────────────────────────────────┤
│ MEDICATIONS (2)                     │
│                                     │
│ 1. Amoxicillin 500mg                │
│    Take 1 capsule 3 times daily     │
│    For 7 days (21 capsules)         │
│                                     │
│ 2. Paracetamol 500mg                │
│    Take 2 tablets every 6 hours     │
│    For pain relief                  │
├─────────────────────────────────────┤
│ REPEATS: 2 remaining of 3           │
│ Next repeat available: 11 Mar 2026  │
├─────────────────────────────────────┤
│ [Share] [Download] [Contact Doctor] │
└─────────────────────────────────────┘
```

## API Integration Points

```
GET  https://cloudapi.test.didxtech.com/tenant/v1/credentials/{id}
POST https://cloudapi.test.didxtech.com/tenant/v1/verifier/verify
```

## Notes

### Technical Constraints
- Convert FHIR format to user-friendly display
- Lazy load medication images
- Cache prescription details for offline viewing
- Support zoom for accessibility

### Accessibility
- Screen reader compatible
- High contrast mode support
- Font size adjustment
- VoiceOver/TalkBack support

### Internationalization
- Support for multiple languages (English, Afrikaans, isiZulu)
- Medication names in local terminology
- Date/number formatting per locale

### Demo Features
- Interactive 3D medication models
- Video explanation of dosage
- Integration with pharmacy price comparison (mock)

### Privacy
- Hide patient ID number by default (show last 4 digits)
- Require authentication for full details
- Auto-lock after period of inactivity
- No screenshots in sensitive areas (if possible)

## Estimation
- **Story Points**: 3
- **Time Estimate**: 1-2 days

## Related Stories
- US-006: Receive Prescription in Wallet (prerequisite)
- US-008: Share Prescription with Pharmacist
