## Title
Advanced Revocation Workflows

## User Story
As a doctor or system administrator, I want sophisticated prescription revocation capabilities including bulk operations, scheduled revocations, and detailed audit trails so that I can efficiently manage prescription validity in complex scenarios.

## Description
This story extends the basic revocation functionality (US-015) with advanced workflows for managing prescription validity at scale. It includes bulk operations, conditional revocations, scheduled revocations, and comprehensive tracking of all revocation activities.

## Acceptance Criteria

### Bulk Revocation Operations
- [ ] Revoke multiple prescriptions at once:
  - By patient (revoke all prescriptions for a patient)
  - By date range (revoke all prescriptions from date X to Y)
  - By medication (revoke all prescriptions for specific drug)
  - By status (revoke all draft/expired prescriptions)
  - By tag/category (if tagging implemented)
- [ ] Bulk revocation with reason template
- [ ] Preview mode showing affected prescriptions before confirmation
- [ ] Confirmation dialog with count and details
- [ ] Progress indicator for large operations
- [ ] Result report showing success/failure per prescription
- [ ] Rollback capability for bulk operations (within 24 hours)

### Scheduled Revocation
- [ ] Schedule future revocation date/time:
  - Single prescription scheduled revocation
  - Batch scheduled revocation
  - Recurring revocation patterns (e.g., "revoke all temp prescriptions on 1st of month")
- [ ] Schedule modification (change date/time)
- [ ] Schedule cancellation before execution
- [ ] Notification before scheduled revocation occurs
- [ ] Calendar view of upcoming scheduled revocations

### Conditional Revocation
- [ ] Auto-revoke prescriptions when:
  - Patient reports adverse reaction
  - Drug recall issued
  - Doctor's license suspended
  - Patient opts out of digital system
  - Expiration date reached (automatic)
- [ ] Conditional rules engine for custom triggers
- [ ] Integration with external systems for recall notifications

### Revocation Workflows
- [ ] **Doctor-Initiated Revocation**
  - Simple single-prescription revocation
  - Reason selection from dropdown
  - Custom reason text option
  - Patient notification option
  - Confirmation with prescription details
- [ ] **Administrator Override**
  - System admin can revoke any prescription
  - Enhanced audit trail for admin actions
  - Requires secondary approval for bulk operations
  - Emergency revocation capability (instant, no confirmation)
- [ ] **Patient-Requested Revocation**
  - Patient can request revocation (requires doctor approval)
  - Request workflow with doctor notification
  - Doctor approval/rejection with reason
  - Patient notification of decision

### Revocation States and Tracking
- [ ] Extended revocation states:
  - `PENDING` - Scheduled for future revocation
  - `IN_PROGRESS` - Revocation being processed
  - `REVOKED` - Successfully revoked
  - `FAILED` - Revocation attempt failed (retryable)
  - `PERMANENT` - Cannot be un-revoked
  - `EXPIRED` - Auto-revoked due to expiration
- [ ] Revocation history per prescription:
  - All revocation attempts
  - Reasons for each revocation
  - Actor who initiated revocation
  - Timestamp and method
  - Related prescriptions (if bulk operation)

### Revocation Impact Analysis
- [ ] Before revocation, show impact:
  - Number of patients affected (bulk)
  - Pharmacies that have seen the prescription
  - Dispensing status (none, partial, complete)
  - Refills/repeats that will be invalidated
- [ ] Post-revocation report:
  - List of affected parties
  - Notification delivery status
  - Recommended follow-up actions

### Notification System
- [ ] Automatic notifications when prescription revoked:
  - Patient notification (push/email/SMS)
  - Pharmacy notification (if already shared)
  - Doctor confirmation
  - Audit log entry
- [ ] Notification templates for different revocation reasons
- [ ] Retry logic for failed notifications

### Revocation Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ REVOCATION MANAGEMENT                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ACTIVE REVOCATIONS (Last 30 Days)                          │
│ Total Revoked: 47     By Doctors: 42     By Admin: 5       │
│ Bulk Operations: 3     Scheduled: 2     Failed: 0          │
│                                                            │
│ RECENT ACTIVITY                                            │
│ ✓ RX-2026-001-123 revoked by Dr. Smith (Wrong dosage)      │
│ ✓ 12 prescriptions revoked for Patient #4567 (Opt-out)     │
│ ⏳ 3 prescriptions scheduled for revocation on 2026-03-01  │
│ ✗ Bulk revocation failed: Network error (retrying)         │
│                                                            │
│ UPCOMING SCHEDULED                                         │
│ Tomorrow: 2 prescriptions                                  │
│ This week: 8 prescriptions                                 │
│                                                            │
│ [Search Revocations] [Bulk Revoke] [Schedule Revocation]   │
└────────────────────────────────────────────────────────────┘
```

## API Integration Points

```
POST /api/v1/prescriptions/{id}/revoke
POST /api/v1/prescriptions/bulk-revoke
POST /api/v1/prescriptions/schedule-revoke
PUT  /api/v1/prescriptions/scheduled/{id}
DELETE /api/v1/prescriptions/scheduled/{id}
GET  /api/v1/prescriptions/revocations
GET  /api/v1/prescriptions/revocations/{id}
POST /api/v1/prescriptions/revoke-rollback/{id}
GET  /api/admin/revocations/dashboard
```

## Technical Implementation

### Revocation Service
```python
class RevocationService:
    async def revoke_single(
        self,
        prescription_id: str,
        reason: RevocationReason,
        actor: Actor,
        notify: bool = True
    ) -> RevocationResult:
        prescription = await self.get_prescription(prescription_id)
        revocation = await self.create_revocation_record(
            prescription, reason, actor
        )
        await self.update_revocation_registry(prescription)
        await self.update_prescription_status(prescription, "REVOKED")
        if notify:
            await self.send_notifications(prescription, revocation)
        return RevocationResult(success=True, revocation_id=revocation.id)
    
    async def revoke_bulk(
        self,
        filter_criteria: FilterCriteria,
        reason: RevocationReason,
        actor: Actor,
        preview_only: bool = False
    ) -> BulkRevocationResult:
        prescriptions = await self.find_prescriptions(filter_criteria)
        if preview_only:
            return BulkRevocationResult(
                affected_count=len(prescriptions),
                prescriptions=prescriptions,
                preview=True
            )
        results = []
        for prescription in prescriptions:
            result = await self.revoke_single(
                prescription.id, reason, actor, notify=False
            )
            results.append(result)
        return BulkRevocationResult(results=results)
```

### Revocation Record Schema
```python
@dataclass
class RevocationRecord:
    id: str
    prescription_id: str
    revocation_type: RevocationType  # SINGLE, BULK, SCHEDULED, AUTOMATIC
    reason: RevocationReason
    custom_reason: Optional[str]
    initiated_by: Actor
    initiated_at: datetime
    effective_at: datetime  # When revocation takes effect
    status: RevocationStatus
    affected_prescriptions: List[str]  # For bulk operations
    notifications_sent: List[NotificationStatus]
    rollback_deadline: Optional[datetime]  # 24 hours for bulk
    rolled_back: bool
    rolled_back_at: Optional[datetime]
    rolled_back_by: Optional[Actor]
```

## Notes

### Business Rules
- Once dispensed, prescriptions cannot be fully revoked (mark as "dispensed" instead)
- Bulk revocations can be rolled back within 24 hours
- Scheduled revocations can be modified/cancelled before execution
- Emergency revocations bypass confirmation but require post-hoc approval

### Legal Considerations
- Revocation must not delete historical records (auditing)
- Patient notification required for all revocations
- Reason must be documented for regulatory compliance
- Some revocations may require secondary approval (controlled substances)

### Performance
- Bulk operations limited to 100 prescriptions at once
- Background job for large bulk operations
- Async notification sending
- Progress updates for long operations

### Security
- Only prescription issuer can revoke (or admin override)
- Enhanced audit logging for all revocation actions
- Rate limiting on revocation API
- Secondary confirmation for bulk operations

## Estimation
- **Story Points**: 5
- **Time Estimate**: 3-4 days
- **Dependencies**: US-015 (Basic Revocation)

## Related Stories
- US-015: Revoke or Cancel Prescription (basic functionality)
- US-020: Advanced Audit Trail (for revocation tracking)
- US-016: Audit Trail & Compliance Logging
