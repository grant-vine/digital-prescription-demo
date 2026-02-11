## Title
Advanced Audit Trail and Compliance Reporting

## User Story
As a compliance officer, I want comprehensive audit trails and detailed compliance reports so that I can demonstrate regulatory adherence, investigate incidents, and provide required documentation to healthcare authorities.

## Description
This story extends the basic audit logging (US-016) with advanced reporting, analytics, and compliance-specific features. It provides tools for regulatory compliance, incident investigation, and operational oversight.

## Acceptance Criteria

### Enhanced Audit Logging
- [ ] Capture all audit events with:
  - Timestamp (millisecond precision)
  - Actor (user ID, role, DID)
  - Action type (CREATE, READ, UPDATE, DELETE, VERIFY, REVOKE)
  - Resource type and ID
  - IP address and device fingerprint
  - Session ID and correlation ID
  - Geographic location (if available)
  - Before/after state for updates
  - Result (success/failure) with reason
- [ ] Log all prescription lifecycle events:
  - Creation (with draft content hash)
  - Signing (with signature details)
  - Transmission (sender, receiver, method)
  - Receipt confirmation
  - Verification attempts (with results)
  - Dispensing events (with pharmacist details)
  - Expiration
  - Revocation (with reason)
- [ ] Log all authentication events:
  - Login attempts (success and failure)
  - Logout events
  - Session timeouts
  - Password/credential changes
  - DID operations (create, resolve, update)
  - Wallet access events

### Audit Data Storage
- [ ] Immutable audit log storage (append-only)
- [ ] Cryptographic integrity verification (hash chain)
- [ ] Separate audit database or schema
- [ ] Automated archival (hot: 90 days, warm: 1 year, cold: 7 years)
- [ ] Tamper-evident logging with digital signatures
- [ ] Export formats: JSON, CSV, PDF report

### Compliance Reports
- [ ] **Prescription Activity Report**
  - Total prescriptions by period
  - Prescriptions by doctor/pharmacy
  - Average time to dispense
  - Repeat/refill statistics
  - Geographic distribution
- [ ] **Security Audit Report**
  - Failed authentication attempts
  - Unauthorized access attempts
  - Unusual activity patterns
  - Credential verification failures
  - Trust registry anomalies
- [ ] **Regulatory Compliance Report**
  - POPIA data handling log
  - HPCSA/SAPC compliance metrics
  - Data retention policy adherence
  - Patient consent tracking
  - Data subject access requests
- [ ] **Doctor/Pharmacist Activity Report**
  - Prescriptions issued by doctor
  - Medications dispensed by pharmacy
  - Verification success rates
  - Average prescription value
  - Controlled substance tracking

### Real-Time Monitoring
- [ ] Real-time audit dashboard showing:
  - Current active users
  - Prescriptions created in last hour
  - Recent verification events
  - Alert-worthy activities
  - System health metrics
- [ ] Configurable alerts for:
  - Multiple failed logins
  - Unusual prescription volumes
  - After-hours activity
  - Geographic anomalies
  - High-value prescriptions

### Search and Investigation
- [ ] Advanced audit log search:
  - Full-text search across all fields
  - Date/time range filters
  - Actor filtering (by DID, role, ID)
  - Resource filtering (by type, ID)
  - Action type filtering
  - Result filtering (success/failure)
  - Correlation ID tracing
- [ ] Timeline view for investigations
- [ ] Export search results
- [ ] Saved searches and scheduled reports

### Compliance Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ COMPLIANCE DASHBOARD - Last 30 Days                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ PRESCRIPTION ACTIVITY                                      │
│ Total Created: 1,247    Total Dispensed: 1,189            │
│ Average Time to Dispense: 4.2 hours                        │
│                                                            │
│ SECURITY METRICS                                           │
│ Failed Logins: 23 (0.8%)    Unauthorized Access: 0         │
│ Suspicious Activities: 3    Alerts Triggered: 7            │
│                                                            │
│ REGULATORY COMPLIANCE                                      │
│ POPIA Violations: 0    HPCSA Audits: 1 passed              │
│ Data Retention: 100% compliant    Consent Valid: 100%      │
│                                                            │
│ AUDIT LOG HEALTH                                           │
│ Total Events: 45,892    Storage Used: 2.3 GB               │
│ Oldest Record: 2026-01-11    Chain Integrity: ✓ Valid      │
└────────────────────────────────────────────────────────────┘
```

## API Integration Points

```
GET  /api/admin/audit/events
GET  /api/admin/audit/events/{id}
POST /api/admin/audit/search
GET  /api/admin/reports/prescriptions
GET  /api/admin/reports/security
GET  /api/admin/reports/compliance
POST /api/admin/reports/export
GET  /api/admin/dashboard/compliance
```

## Technical Implementation

### Audit Log Schema
```python
@dataclass
class AuditEvent:
    id: str                    # UUID
    timestamp: datetime        # UTC with milliseconds
    actor_did: str            # User's DID
    actor_role: Role          # doctor, patient, pharmacist, admin
    action: ActionType        # CREATE, READ, UPDATE, DELETE, etc.
    resource_type: str        # prescription, credential, user
    resource_id: str          # Resource identifier
    ip_address: str           # Client IP
    session_id: str           # Session identifier
    correlation_id: str       # Request correlation ID
    geo_location: Optional[GeoLocation]
    before_state: Optional[dict]   # Previous state (for updates)
    after_state: Optional[dict]    # New state
    result: Result            # SUCCESS, FAILURE
    reason: Optional[str]     # Failure reason
    signature: str            # Cryptographic signature
    previous_hash: str        # Hash of previous event (chain)
```

### Report Generation
```python
async def generate_prescription_report(
    start_date: datetime,
    end_date: datetime,
    filters: ReportFilters
) -> Report:
    """Generate prescription activity report"""
    prescriptions = await fetch_prescriptions(start_date, end_date, filters)
    metrics = calculate_metrics(prescriptions)
    return Report(
        title="Prescription Activity Report",
        period=f"{start_date} to {end_date}",
        metrics=metrics,
        data=prescriptions,
        generated_at=datetime.utcnow()
    )
```

## Notes

### Regulatory Requirements
- **POPIA (South Africa)**: Log all personal data access
- **HPCSA**: Maintain prescription records for minimum periods
- **SAPC**: Track controlled substance dispensing
- **Retention**: Hot 90 days, archive 7 years

### Privacy Considerations
- Audit logs contain sensitive data - restrict access
- Implement role-based access to audit data
- Anonymize data in reports where possible
- Log access to audit logs (meta-auditing)

### Performance
- Audit logging must not impact API performance (<5ms overhead)
- Use async logging with queue/buffer
- Archive old logs to cold storage
- Index frequently searched fields

### Security
- Audit logs are tamper-evident (hash chain)
- Regular integrity verification
- Separate storage from application data
- Backup and disaster recovery procedures

## Estimation
- **Story Points**: 8
- **Time Estimate**: 4-5 days
- **Dependencies**: US-016 (Basic Audit Trail)

## Related Stories
- US-016: Basic Audit Trail & Compliance Logging
- US-025: Monitoring & Observability (for real-time alerts)
