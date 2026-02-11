## Title
Time-Based Prescription Validation

## User Story
As the digital prescription system, I need to enforce time-based validation rules on prescriptions, so that expired prescriptions cannot be dispensed, repeat intervals are respected, and prescription validity windows are properly managed.

## Description
Time-based validation is critical for patient safety and regulatory compliance. Prescriptions have validity periods during which they can be dispensed. Some medications have specific timing requirements. Repeat prescriptions have intervals to prevent abuse. The system must automatically enforce these rules.

## Context

## Acceptance Criteria

### Validity Period Enforcement
- [ ] System validates prescription against validity period
- [ ] Prescriptions cannot be dispensed before issue date
- [ ] Prescriptions cannot be dispensed after expiration date
- [ ] Expiration date calculated based on:
  - Standard validity: 6 months from issue date
  - Controlled substances: 30 days from issue date
  - Schedule 5/6 medications: 30 days from issue date
  - Doctor-specified shorter period (if applicable)

### Expiration Warnings
- [ ] Warning shown when prescription expires within 7 days
- [ ] Warning shown when prescription expires within 24 hours
- [ ] Expired prescriptions clearly marked as invalid
- [ ] Reason for expiration displayed (date passed)

### Repeat Interval Enforcement
- [ ] System tracks when prescription was last dispensed
- [ ] Calculates days since last dispensing
- [ ] Validates repeat interval requirements:
  - Standard: No sooner than 75% of previous supply used
  - Specific medications: Doctor-defined minimum interval
  - Chronic medications: Monthly maximums
- [ ] Blocks dispensing if interval not met
- [ ] Shows days until next repeat is allowed

### Time Zone Handling
- [ ] All timestamps stored in UTC
- [ ] Display converted to local time (South Africa: SAST, UTC+2)
- [ ] Expiration calculated at end of day (23:59:59) in local time
- [ ] Handle daylight saving time transitions (if applicable)

### Dispensing Window Logic
```
VALIDATION RULES:

1. Prescription Status Check
   IF current_date < issue_date:
     → ERROR: Prescription not yet valid
   
   IF current_date > expiration_date:
     → ERROR: Prescription expired
   
2. Repeat Eligibility Check
   IF repeat_requested:
     IF days_since_last_dispense < minimum_interval:
       → ERROR: Too soon for repeat
       → Display: "Next repeat available in X days"
     IF repeats_remaining <= 0:
       → ERROR: No repeats remaining
   
3. Controlled Substance Check
   IF medication_schedule IN [5, 6, 7]:
     IF days_since_issue > 30:
       → ERROR: Controlled substance prescription expired
```

### User Notifications
- [ ] Doctor sees estimated validity period when creating prescription
- [ ] Patient sees validity countdown in wallet
- [ ] Pharmacist sees expiration warning in dispensing view
- [ ] Automated reminder to patient 7 days before expiration (optional)

### Audit Trail Time Stamps
- [ ] All dispensing events timestamped
- [ ] Time zone recorded with each timestamp
- [ ] Chronological ordering maintained
- [ ] Immutable time records for compliance

### Time Override (Emergency)
- [ ] Emergency dispensing override capability
- [ ] Requires senior pharmacist authorization
- [ ] Override reason must be documented
- [ ] Automatic notification to doctor
- [ ] Special audit flag for overrides

### Testing Time Scenarios
For demo/testing purposes:
- [ ] System supports "time travel" mode in test environment
- [ ] Can simulate future dates for testing expiration
- [ ] Can simulate past dates for testing historical data
- [ ] Clear indication when in test time mode

## API Integration Points

```
GET  /api/v1/prescriptions/{id}/validity
POST /api/v1/prescriptions/{id}/validate-time
GET  /api/v1/prescriptions/{id}/repeat-eligibility
```

## Notes

### Technical Implementation
- Use NTP-synchronized servers for accurate time
- Store all times as ISO 8601 with timezone
- Cache validity calculations for performance
- Background job to update expiration status

### Regulatory Compliance
- Follow South African Pharmacy Act regulations
- Comply with Medicine and Related Substances Act
- Adhere to HPCSA guidelines for prescription validity
- Meet SAPC requirements for controlled substances

### Edge Cases
- Leap year handling (February 29)
- Month-end calculations (30/31 days)
- Year boundary crossings
- System clock changes

### Performance
- Time validation must complete in <100ms
- Batch validation for multiple prescriptions
- Pre-calculate expiration warnings

### Demo Configuration
- Default validity: 30 days for demo (not 6 months)
- Controlled substance flag on sample medications
- Visual countdown timer for demonstrations
- Manual date override for testing scenarios

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-013: Handle Prescription Expiration
- US-014: Support Prescription Repeats/Refills
- US-011: View Prescription Items for Dispensing (uses validation)
