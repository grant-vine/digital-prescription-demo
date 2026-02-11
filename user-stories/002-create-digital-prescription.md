## Title
Create Digital Prescription

## User Story
As an authenticated doctor, I want to create a digital prescription for my patient by entering medication details, dosage instructions, and patient information, so that the prescription can be issued as a verifiable credential.

## Description
This story enables doctors to create digital prescriptions using a form interface. The prescription follows FHIR R4 format for interoperability and includes all necessary medical information, medication details, and dispensing instructions. The doctor can save drafts, review before signing, and manage the prescription lifecycle.

## Context
The doctor's web application provides a form interface to enter prescription details. This includes patient identification (linked to their DID), medications with dosage and instructions, and metadata such as diagnosis codes. The prescription data follows FHIR R4 MedicationRequest resource format for interoperability.

## Acceptance Criteria

### Prescription Form
- [ ] Doctor can search for patient by ID number or scan QR code with patient DID
- [ ] System validates patient has a valid wallet/DID
- [ ] Doctor can add one or more medications to the prescription
- [ ] For each medication, doctor enters:
  - Medication name (searchable database with SAHPRA codes)
  - Strength/dosage (e.g., "500mg")
  - Quantity to dispense
  - Dosage instructions (e.g., "Take 1 tablet twice daily")
  - Route of administration (oral, topical, etc.)
  - Duration of treatment
- [ ] Doctor can specify repeat/refill information:
  - Number of repeats allowed (0-5)
  - Repeat interval restrictions (e.g., "no sooner than 30 days")
- [ ] Doctor can add special instructions (allergies, interactions, etc.)
- [ ] Form validates required fields before submission

### Patient Data Handling
- [ ] Patient's DID is resolved to verify identity
- [ ] Patient demographics auto-populate from their verifiable credentials
- [ ] Doctor confirms patient identity matches the prescription recipient
- [ ] System checks for patient allergies and drug interactions (warning only in demo)

### Prescription Metadata
- [ ] System generates unique prescription ID
- [ ] Timestamp is automatically recorded
- [ ] Doctor's practice information is included
- [ ] Diagnosis/ICD-10 code can be added (optional)

### Draft & Review
- [ ] Doctor can save prescription as draft
- [ ] Preview mode shows complete prescription before signing
- [ ] Doctor can edit or discard draft prescriptions
- [ ] Drafts are stored locally (not issued to blockchain)

### Data Structure
Prescription follows FHIR R4 MedicationRequest:
```json
{
  "resourceType": "MedicationRequest",
  "id": "prescription-uuid",
  "status": "draft",
  "intent": "order",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://sahpra.org.za/medication-codes",
      "code": "MED001",
      "display": "Paracetamol 500mg"
    }]
  },
  "subject": {
    "reference": "did:cheqd:testnet:patient-did"
  },
  "authoredOn": "2026-02-11T11:42:00Z",
  "requester": {
    "reference": "did:cheqd:testnet:doctor-did"
  },
  "dosageInstruction": [{
    "text": "Take 1 tablet twice daily",
    "timing": {
      "repeat": {
        "frequency": 2,
        "period": 1,
        "periodUnit": "d"
      }
    }
  }],
  "dispenseRequest": {
    "quantity": {
      "value": 30,
      "unit": "tablets"
    },
    "numberOfRepeatsAllowed": 2,
    "validityPeriod": {
      "start": "2026-02-11",
      "end": "2026-05-11"
    }
  }
}
```

## API Integration Points

```
GET  https://cloudapi.test.didxtech.com/tenant/v1/wallet/dids/{did}
POST /api/v1/prescriptions (internal API)
GET  /api/v1/medications/search (internal medication database)
```

## Notes

### Technical Constraints
- Use FHIR R4 MedicationRequest resource structure
- Include verifiable credential wrapper for SSI compatibility
- Support multiple medications per prescription
- Prescription ID format: `RX-{timestamp}-{uuid}`

### Data Requirements
- SAHPRA medication database (mock subset for demo)
- Patient DID resolution service
- ICD-10 diagnosis codes (subset for demo)

### User Experience
- Auto-complete for medication names
- QR code scanner for patient DID input
- Mobile-responsive form design
- Clear visual feedback on validation errors

### Demo Simplifications
- Use mock medication database (50 common medications)
- No real-time drug interaction checking
- Patient search by ID number (not full registry integration)

### Compliance Notes
- Capture all prescription data required by SAHPRA
- Include doctor's practice details as per regulations
- Timestamp must be auditable and tamper-evident

## Estimation
- **Story Points**: 8
- **Time Estimate**: 3-4 days

## Related Stories
- US-002: Doctor Authentication & DID Setup (prerequisite)
- US-003: Sign Prescription with Digital Signature (next step)
- US-014: Support Prescription Repeats/Refills
