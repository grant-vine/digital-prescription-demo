## Title
Pharmacist Authentication & DID Setup

## User Story
As a licensed pharmacist, I want to authenticate with the digital prescription system and establish my decentralized identifier (DID), so that I can receive, verify, and dispense digital prescriptions from patients.

## Description
Pharmacists require the same foundational identity setup as doctors to participate in the SSI ecosystem. Their DID allows them to establish trust relationships with patients, verify prescriptions from doctors, and prove their own credentials when dispensing medications.

## Acceptance Criteria

### Authentication
- [ ] Pharmacist can log in using OAuth 2.0 credentials
- [ ] System validates pharmacist's registration number
- [ ] Pharmacy premises license is verified
- [ ] Pharmacist's professional credentials are checked
- [ ] Multi-factor authentication option available

### DID Creation
- [ ] Pharmacist can create a DID on cheqd testnet
- [ ] DID document includes pharmacy business details
- [ ] Pharmacist's professional credentials linked to DID
- [ ] Private keys stored securely in custodial wallet
- [ ] DID resolution available for public verification

### Pharmacy Profile Setup
- [ ] Pharmacist enters pharmacy business details:
  - Pharmacy name and trading name
  - Physical address with GPS coordinates
  - Contact information (phone, email)
  - Operating hours
  - SAPC registration number
- [ ] Pharmacist can upload pharmacy logo
- [ ] Multiple pharmacists can be linked to one pharmacy DID
- [ ] Role-based access (pharmacist vs. pharmacy assistant)

### Trust Registry Registration
- [ ] Pharmacy is registered in trust registry
- [ ] Registration status is verifiable by patients
- [ ] Annual renewal tracked
- [ ] Suspension/revocation status checked

### Wallet Interface
- [ ] Pharmacist dashboard shows:
  - Incoming prescription requests
  - Verification queue
  - Dispensing history
  - Patient connections
- [ ] Real-time notifications for new prescriptions
- [ ] Search and filter for prescription history

### QR Code for Patient Connection
- [ ] Pharmacy can display QR code for patient scanning
- [ ] QR code contains out-of-band invitation with pharmacy DID
- [ ] QR code can be printed for counter display
- [ ] Different QR codes for different purposes (general, specific counter)

## API Integration Points

```
POST https://cloudapi.test.didxtech.com/tenant/v1/auth/token
POST https://cloudapi.test.didxtech.com/tenant/v1/wallet
POST https://cloudapi.test.didxtech.com/tenant/v1/dids
POST https://cloudapi.test.didxtech.com/tenant/v1/trust-registry/register
```

## Notes

### Technical Constraints
- Same SSI infrastructure as doctor workflow
- Support for multiple users per pharmacy
- Role-based permissions
- Audit logging for compliance

### Regulatory Compliance
- SAPC (South African Pharmacy Council) registration required
- Annual license verification
- Record retention per pharmacy regulations
- Dispensing authority validation

### Security Requirements
- Strict access controls
- Session management for shared computers
- Audit trail of all dispensing activities
- Integration with pharmacy management system (future)

### Multi-User Support
- Different roles: Supervising pharmacist, pharmacist, intern, assistant
- Permission levels for each role
- Activity tracking per user
- Shift handover logging

### Demo Simplifications
- Mock SAPC registry integration
- Single pharmacist per pharmacy in demo
- Pre-configured test pharmacy accounts
- Simplified role model

### Hardware Integration (Future)
- Barcode scanner for medication verification
- Label printer integration
- POS system connectivity
- Stock management system API

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- US-001: Doctor Authentication & DID Setup (similar flow)
- US-008: Share Prescription with Pharmacist (interaction)
- US-010: Verify Prescription Authenticity
- US-011: View Prescription Items for Dispensing
