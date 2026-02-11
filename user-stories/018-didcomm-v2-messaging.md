## Title
Implement DIDComm v2 for Prescription Exchange

## User Story
As the digital prescription system, I want to replace QR code flows with full DIDComm v2 peer-to-peer messaging, so that prescription transmission is secure, automated, and provides end-to-end encryption between doctor, patient, and pharmacist.

## Description
Current MVP uses QR codes for simplicity and speed. For production, we need proper DIDComm v2 messaging which provides end-to-end encryption, authentication, and asynchronous message delivery.

## Context
Current MVP uses QR codes for simplicity and speed. For production, we need proper DIDComm v2 messaging which provides end-to-end encryption, authentication, and asynchronous message delivery.

## Acceptance Criteria

### Connection Management
- [ ] Create DIDComm connections (Out-of-Band invitations)
- [ ] Accept connection requests
- [ ] Manage connection state
- [ ] Connection persistence across app restarts
- [ ] Display active connections list
- [ ] Revoke/close connections

### Doctor → Patient Flow
- [ ] Doctor creates connection invitation
- [ ] Patient accepts invitation (scans QR or clicks link)
- [ ] Secure DIDComm channel established
- [ ] Doctor sends prescription via issue-credential protocol
- [ ] Patient receives and processes credential offer
- [ ] Patient accepts credential into wallet
- [ ] Acknowledgment sent back to doctor

### Patient → Pharmacist Flow
- [ ] Patient creates connection with pharmacy
- [ ] Pharmacist accepts connection
- [ ] Patient sends proof request (selective disclosure)
- [ ] Pharmacist receives proof request
- [ ] Pharmacist sends proof presentation
- [ ] Patient verifies proof
- [ ] Prescription details shared securely

### Protocol Support
- [ ] Out-of-Band (OOB) protocol v1.1
- [ ] DIDComm Messaging v2.0
- [ ] Issue Credential v2.0
- [ ] Present Proof v2.0
- [ ] Trust Ping (connection health check)

### Encryption & Security
- [ ] Authcrypt (sender authenticated encryption)
- [ ] Anoncrypt (anonymous encryption where needed)
- [ ] Digital signatures on all messages
- [ ] Key rotation support
- [ ] Forward secrecy

### Mediator Support
- [ ] Mediator coordination for offline delivery
- [ ] Message pickup protocol
- [ ] Queue management
- [ ] Delivery confirmation

### Error Handling
- [ ] Connection timeout handling
- [ ] Message delivery failures
- [ ] Retry logic with exponential backoff
- [ ] Dead letter queue for failed messages
- [ ] Error notification to user

## DIDComm Message Examples

### Connection Invitation (Doctor → Patient)
```json
{
  "@id": "uuid-invitation",
  "@type": "https://didcomm.org/out-of-band/1.1/invitation",
  "label": "Dr. Smith's Office",
  "goal_code": "connect-prescription",
  "goal": "Exchange prescriptions securely",
  "requests~attach": [{
    "@id": "request-0",
    "mime-type": "application/json",
    "data": {
      "json": {
        "@type": "https://didcomm.org/didexchange/1.0/request"
      }
    }
  }],
  "service": [{
    "id": "#inline",
    "type": "did-communication",
    "recipientKeys": ["did:key:z6Mk..."],
    "routingKeys": [],
    "serviceEndpoint": "https://mediator.example.com"
  }]
}
```

### Credential Offer (Doctor → Patient)
```json
{
  "@id": "uuid-offer",
  "@type": "https://didcomm.org/issue-credential/2.0/offer-credential",
  "~thread": {"thid": "uuid-thread"},
  "comment": "Prescription for Amoxicillin",
  "credential_preview": {
    "@type": "https://didcomm.org/issue-credential/2.0/credential-preview",
    "attributes": [
      {"name": "prescriptionId", "value": "RX-001"},
      {"name": "medication", "value": "Amoxicillin 500mg"},
      {"name": "quantity", "value": "21"}
    ]
  },
  "offers~attach": [...]
}
```

## API Integration Points

```
POST /didcomm/connections/create-invitation
POST /didcomm/connections/receive-invitation
GET  /didcomm/connections
POST /didcomm/messaging/send
GET  /didcomm/messaging/receive
POST /didcomm/credentials/send-offer
POST /didcomm/credentials/send-request
POST /didcomm/proofs/send-request
POST /didcomm/proofs/send-presentation
```

## Technical Implementation

**Library:** didcomm-python  
**DID Method:** did:peer or did:key for connections  
**Encryption:** libsodium (NaCl) via PyNaCl  
**Mediators:** ACA-Py built-in mediator or standalone

## User Experience

### Doctor App
- "Send to Patient" button triggers DIDComm flow
- Shows connection status (connecting → connected → sent → received)
- Retry option if delivery fails

### Patient App
- Notification: "Dr. Smith wants to connect"
- Approve connection → auto-receive prescription
- Badge on prescription when received

### Pharmacist App
- "Request Prescription" sends proof request
- Real-time status updates
- Automatic verification on receipt

## Estimation
- **Story Points**: 13
- **Time Estimate**: 5-7 days
- **Dependencies**: US-004, US-006, US-008 (replaces QR flows)

## Migration from QR Codes

### Strategy
1. Keep QR codes as fallback
2. Add DIDComm as "enhanced mode"
3. Auto-detect: If both parties support DIDComm, use it
4. Otherwise, fall back to QR codes

### Configuration
```python
MESSAGING_MODE = "didcomm"  # or "qr" or "auto"
MEDIATOR_URL = "https://mediator.didxtech.com"
```

## Notes

### Complexity
DIDComm adds significant complexity:
- Connection management
- Mediator infrastructure
- Message queuing
- Error handling
- Key management

### Benefits
- True peer-to-peer (no intermediary servers)
- End-to-end encryption
- Authentication guaranteed
- Asynchronous (works offline)
- Standard protocol (interoperable)

### Demo Consideration
For demo, QR codes are sufficient and easier to explain. DIDComm is for production.

## Related Stories
- Replaces/extends: US-004, US-006, US-008 (QR code flows)
- Related: US-023 (Mobile Wallet Deep Integration)
