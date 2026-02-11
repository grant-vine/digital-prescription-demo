## Title
Advanced Time-Based Validation

## User Story
As a pharmacist and system administrator, I want sophisticated time-based prescription validation including business hour restrictions, time-zone handling, emergency overrides, and prescription scheduling so that prescriptions are dispensed appropriately according to clinical and regulatory timing requirements.

## Description
This story extends the basic time validation (US-012) with advanced temporal logic for complex prescription scenarios. It includes business hours, time zones, holiday calendars, controlled substance timing windows, and prescription scheduling features.

## Acceptance Criteria

### Business Hours Validation
- [ ] Define business hours per pharmacy:
  - Standard operating hours (e.g., 08:00-17:00)
  - Extended hours (e.g., 17:00-21:00 with different rules)
  - Weekend hours
  - Holiday hours
  - 24-hour pharmacies (no restriction)
- [ ] Prescription validity restricted to business hours:
  - Controlled substances: business hours only
  - Emergency medications: 24/7
  - Regular prescriptions: configurable
- [ ] After-hours prescription handling:
  - Queue for next business day
  - Emergency contact protocol
  - 24-hour pharmacy referral

### Time Zone Support
- [ ] Multi-timezone support for national deployments:
  - Store all times in UTC internally
  - Convert to local timezone for display
  - Handle timezone in validation logic
  - Support daylight saving time transitions
- [ ] Timezone per pharmacy location
- [ ] Timezone per user preference
- [ ] Prescription timestamp shows both local and UTC

### Holiday and Special Date Handling
- [ ] Configurable holiday calendar per region:
  - Public holidays (South Africa)
  - Pharmacy-specific closed days
  - Special event days
- [ ] Holiday prescription rules:
  - Extend validity period through holidays
  - Different rules for long weekends
  - Emergency override for holidays
- [ ] Year-end/period-end handling:
  - Handle prescriptions crossing year boundary
  - Fiscal year reporting considerations

### Controlled Substance Timing
- [ ] Schedule-based timing restrictions:
  - Schedule 5: Standard hours
  - Schedule 6: Business hours only
  - Schedule 7: Special dispensing windows
- [ ] Minimum interval between refills:
  - Enforce "not before" dates
  - Calculate based on quantity and dosage
  - Override with doctor authorization
- [ ] Maximum quantity per time period:
  - Daily limits
  - Weekly limits
  - Monthly limits
  - Alert on approaching limits

### Prescription Scheduling
- [ ] Future-dated prescriptions:
  - Doctor can specify "do not dispense before" date
  - Prescription valid only after start date
  - Expiration date calculated from start date
- [ ] Automatic activation:
  - Prescription becomes valid on scheduled date
  - Patient notification on activation
  - Pharmacy notification if shared
- [ ] Recurring prescription schedules:
  - Monthly chronic medication
  - Automatic refill scheduling
  - Patient reminder notifications

### Time-Based Alerting
- [ ] Expiration warnings:
  - 7 days before expiration
  - 24 hours before expiration
  - Expiration day notification
- [ ] Refill timing alerts:
  - Approaching minimum interval
  - Optimal refill window
  - Prescription about to expire
- [ ] Pharmacy closing soon warnings:
  - Alert if prescription valid but pharmacy closing
  - Suggest 24-hour alternatives
  - Queue for next day option

### Emergency Override System
- [ ] Emergency dispensing outside normal hours:
  - Emergency contact verification
  - Override code from on-call doctor
  - Enhanced audit logging
  - Next-day review required
- [ ] Emergency prescription types:
  - Life-saving medications (no restriction)
  - Urgent medications (reduced restriction)
  - Standard medications (business hours only)
- [ ] Post-emergency follow-up:
  - Automatic notification to regular pharmacy
  - Synchronization of dispensing record
  - Doctor notification of emergency dispense

### Validation Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ TIME-BASED VALIDATION                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ CURRENT STATUS                                             │
│ Time: 2026-02-11 14:30 SAST (UTC+2)                        │
│ Pharmacy Status: ✓ Open (Closes in 2h 30m)                 │
│                                                            │
│ PRESCRIPTION TIME RESTRICTIONS                             │
│ ✓ RX-001: Valid now (Standard hours)                       │
│ ✗ RX-002: Schedule 6 - After hours (Open 08:00 tomorrow)   │
│ ⏳ RX-003: Scheduled - Active on 2026-02-15                │
│ ⚠ RX-004: Refill interval - Eligible on 2026-02-18         │
│                                                            │
│ SCHEDULED PRESCRIPTIONS                                    │
│ Activating Today: 2                                        │
│ Activating This Week: 12                                   │
│ Future-dated: 45                                           │
│                                                            │
│ CONTROLLED SUBSTANCE TRACKING                              │
│ Patient #1234: 8/30 days supply used                       │
│ Next eligible refill: 2026-03-05                           │
│                                                            │
│ HOLIDAYS AFFECTING VALIDITY                                │
│ Human Rights Day (2026-03-21) - Closed                     │
│ Good Friday (2026-04-03) - Closed                          │
└────────────────────────────────────────────────────────────┘
```

## API Integration Points

```
GET  /api/v1/pharmacy/{id}/hours
PUT  /api/v1/pharmacy/{id}/hours
GET  /api/v1/prescriptions/{id}/time-validity
POST /api/v1/prescriptions/{id}/schedule
PUT  /api/v1/prescriptions/{id}/schedule
GET  /api/v1/prescriptions/scheduled
GET  /api/v1/holidays
POST /api/v1/holidays
GET  /api/v1/controlled-substances/patient/{id}/limits
POST /api/v1/emergency-override
GET  /api/admin/time-validation/dashboard
```

## Technical Implementation

### Time Validation Service
```python
class TimeValidationService:
    def __init__(self, timezone_service, holiday_service):
        self.timezone_service = timezone_service
        self.holiday_service = holiday_service
    
    async def validate_dispensing_time(
        self,
        prescription: Prescription,
        pharmacy: Pharmacy,
        current_time: datetime
    ) -> TimeValidationResult:
        local_time = self.timezone_service.to_local(
            current_time, pharmacy.timezone
        )
        
        # Check business hours
        if not self.is_business_hours(pharmacy, local_time):
            if prescription.medication.schedule in [6, 7]:
                return TimeValidationResult(
                    valid=False,
                    reason="Schedule 6/7 medications require business hours",
                    next_valid=self.next_business_hours(pharmacy, local_time)
                )
        
        # Check schedule date
        if prescription.schedule_start_date:
            if local_time.date() < prescription.schedule_start_date:
                return TimeValidationResult(
                    valid=False,
                    reason=f"Prescription activates on {prescription.schedule_start_date}",
                    next_valid=prescription.schedule_start_date
                )
        
        # Check refill interval
        if prescription.last_dispensed:
            min_interval = self.calculate_min_interval(prescription)
            if current_time < prescription.last_dispensed + min_interval:
                return TimeValidationResult(
                    valid=False,
                    reason="Minimum refill interval not met",
                    next_valid=prescription.last_dispensed + min_interval
                )
        
        return TimeValidationResult(valid=True)
    
    def is_business_hours(
        self,
        pharmacy: Pharmacy,
        local_time: datetime
    ) -> bool:
        hours = pharmacy.get_hours_for_date(local_time.date())
        return hours.open_time <= local_time.time() <= hours.close_time
```

## Notes

### Regulatory Compliance
- **Medicines and Related Substances Act**: Schedule-based dispensing rules
- **HPCSA**: Professional practice hours guidelines
- **POPIA**: Time-based data access restrictions

### Clinical Considerations
- Emergency medications must be available 24/7
- Controlled substances require strict timing
- Patient safety takes precedence over rules (override capability)
- Refill intervals prevent abuse while ensuring compliance

### Performance
- Cache pharmacy hours and holidays
- Pre-calculate next valid dispensing times
- Timezone conversions at display layer, UTC internally
- Batch scheduled prescription activation

### Edge Cases
- Daylight saving transitions
- Prescriptions spanning year boundary
- Multiple timezones in single organization
- Pharmacy temporarily closed (emergency, power outage)

## Estimation
- **Story Points**: 5
- **Time Estimate**: 3-4 days
- **Dependencies**: US-012 (Basic Time-Based Validation)

## Related Stories
- US-012: Time-Based Prescription Validation (basic)
- US-013: Handle Prescription Expiration
- US-014: Support Prescription Repeats/Refills
