## Title
Audit Trail & Compliance Logging

## User Story
As a healthcare regulator and system administrator, I want a comprehensive audit trail of all prescription-related activities, so that we can ensure compliance with healthcare regulations, investigate issues, and maintain accountability across the digital prescription ecosystem.

## Description
Audit trails are essential for regulatory compliance in healthcare. Every action in the prescription lifecycle must be logged immutably: creation, signing, transmission, verification, dispensing, revocation, and access. These logs support regulatory reporting, fraud detection, dispute resolution, and system monitoring.

## Context

## Acceptance Criteria

### Event Logging
All events logged with:
- [ ] Timestamp (UTC with timezone)
- [ ] Actor (DID of user/system)
- [ ] Action type (create, sign, send, verify, dispense, revoke, access)
- [ ] Object (prescription ID)
- [ ] Result (success, failure, pending)
- [ ] IP address and geolocation (if available)
- [ ] User agent/device info
- [ ] Reason/cause (for failures)

### Events to Log

#### Doctor Actions
- [ ] Authentication/login
- [ ] DID creation
- [ ] Prescription created (draft)
- [ ] Prescription signed
- [ ] Prescription sent to patient
- [ ] Prescription sent to pharmacy
- [ ] Prescription revoked
- [ ] Prescription viewed
- [ ] Connection established with patient

#### Patient Actions
- [ ] Wallet created
- [ ] Authentication/login
- [ ] Prescription received
- [ ] Prescription accepted/rejected
- [ ] Prescription shared with pharmacy
- [ ] Prescription viewed
- [ ] Connection established with doctor/pharmacy

#### Pharmacist Actions
- [ ] Authentication/login
- [ ] DID created
- [ ] Prescription received from patient
- [ ] Prescription verification attempted
- [ ] Prescription verification result
- [ ] Prescription dispensed
- [ ] Partial dispensing recorded
- [ ] Dispensing declined
- [ ] Connection established with patient

#### System Events
- [ ] Background validity checks
- [ ] Expiration status updates
- [ ] Revocation registry updates
- [ ] Trust registry queries
- [ ] DID resolution requests
- [ ] API errors and exceptions

### Log Storage
- [ ] Logs written to immutable storage
- [ ] Distributed ledger for critical events
- [ ] Encrypted at rest
- [ ] Retention period: 7 years (regulatory requirement)
- [ ] Backup and disaster recovery
- [ ] Tamper-evident logging

### Audit Trail Query Interface
- [ ] Search by prescription ID
- [ ] Search by patient DID
- [ ] Search by doctor DID
- [ ] Search by pharmacist/pharmacy DID
- [ ] Date range filtering
- [ ] Event type filtering
- [ ] Export to CSV/PDF
- [ ] Timeline visualization

### Compliance Reports
- [ ] Monthly dispensing report by pharmacy
- [ ] Doctor prescription volume report
- [ ] Expired prescription report
- [ ] Revoked prescription report
- [ ] Controlled substance dispensing report
- [ ] Repeat dispensing pattern report
- [ ] Failed verification report

### Real-Time Monitoring
- [ ] Dashboard for system administrators
- [ ] Real-time event stream
- [ ] Alerting for suspicious patterns:
  - Multiple failed verifications
  - Unusual dispensing volumes
  - Rapid repeat requests
  - Revocation spikes
- [ ] Integration with SIEM (future)

### Privacy Protection
- [ ] Access controls on audit data
- [ ] Role-based permissions:
  - System admin: Full access
  - Regulator: Aggregated reports only
  - Pharmacy: Own data only
  - Doctor: Own data only
  - Patient: Own data only
- [ ] Data anonymization for analytics
- [ ] GDPR/South African POPIA compliance

### Audit Trail Viewer (Admin Interface)
```
┌─────────────────────────────────────────────┐
│ AUDIT TRAIL - Prescription #RX-20260211     │
├─────────────────────────────────────────────┤
│                                             │
│ 11 Feb 2026 11:42:15 SAST                   │
│ 👤 Dr. Jane Smith (did:cheqd:doc123)        │
│ 📝 ACTION: Prescription Created             │
│ ✅ RESULT: Success                          │
│                                             │
│ 11 Feb 2026 11:43:22 SAST                   │
│ 👤 Dr. Jane Smith (did:cheqd:doc123)        │
│ ✍️  ACTION: Prescription Signed             │
│ ✅ RESULT: Success                          │
│ Proof: z58DAdF...                           │
│                                             │
│ 11 Feb 2026 11:45:08 SAST                   │
│ 👤 Dr. Jane Smith (did:cheqd:doc123)        │
│ 📤 ACTION: Sent to Patient                  │
│ 👥 TO: John Doe (did:cheqd:patient456)      │
│ ✅ RESULT: Delivered                        │
│                                             │
│ 11 Feb 2026 14:22:33 SAST                   │
│ 👤 John Doe (did:cheqd:patient456)          │
│ 📥 ACTION: Prescription Accepted            │
│ ✅ RESULT: Success                          │
│                                             │
│ 15 Feb 2026 09:15:47 SAST                   │
│ 👤 John Doe (did:cheqd:patient456)          │
│ 📤 ACTION: Shared with Pharmacy             │
│ 👥 TO: Cape Town Pharmacy (did:cheqd:ph789) │
│ ✅ RESULT: Delivered                        │
│                                             │
│ 15 Feb 2026 09:16:12 SAST                   │
│ 👤 Pharmacist Sarah (did:cheqd:pharm012)    │
│ 🔍 ACTION: Verification Attempt             │
│ ✅ RESULT: Verified                         │
│                                             │
│ 15 Feb 2026 09:23:55 SAST                   │
│ 👤 Pharmacist Sarah (did:cheqd:pharm012)    │
│ 💊 ACTION: Prescription Dispensed           │
│ 📦 Quantity: 30 tablets                     │
│ ✅ RESULT: Success                          │
└─────────────────────────────────────────────┘
```

### Tamper Evidence
- [ ] Cryptographic hashes for log entries
- [ ] Blockchain anchoring for critical events
- [ ] Digital signatures on log files
- [ ] Regular integrity verification
- [ ] Alert if tampering detected

## API Integration Points

```
POST /api/v1/audit/log (internal)
GET  /api/v1/audit/query (internal)
GET  /api/v1/audit/reports/{type} (internal)
POST /api/v1/audit/export (internal)
```

## Notes

### Regulatory Requirements
- South African Pharmacy Act: 5-year retention
- HPCSA guidelines: Complete audit trail required
- POPIA compliance for personal information
- Electronic Communications and Transactions Act

### Technical Architecture
- Event sourcing pattern for audit log
- Separate audit database (read-only replicas)
- Immutable storage (WORM - Write Once Read Many)
- Time-series database for metrics

### Performance
- Asynchronous logging (don't block user actions)
- Batch writes for efficiency
- Archival of old logs to cold storage
- Indexing for fast queries

### Security
- Logs are append-only
- Access strictly controlled
- Encryption in transit and at rest
- Regular security audits

### Demo Simplifications
- In-memory logging for demo (no persistence)
- Pre-populated audit trail examples
- Simplified query interface
- Sample compliance reports

### Integration Points
- DIDx CloudAPI logs
- Application logs
- System logs
- Ledger transactions

## Estimation
- **Story Points**: 8
- **Time Estimate**: 3-4 days

## Related Stories
- All stories generate audit events
- US-010: Verify Prescription Authenticity (verification events)
- US-015: Revoke or Cancel Prescription (revocation events)
