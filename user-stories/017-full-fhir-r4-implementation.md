## Title
Implement Full FHIR R4 MedicationRequest

## User Story
As the digital prescription system, I want to migrate from a simplified prescription schema to full FHIR R4 MedicationRequest resource, so that we can achieve healthcare interoperability and compliance with international healthcare data standards.

## Description
Currently using a simplified "FHIR-inspired" schema with 10 fields. For production use and integration with existing healthcare systems, we need full FHIR R4 compliance with all standard fields, extensions, and relationships.

## Context
Currently using a simplified "FHIR-inspired" schema with 10 fields. For production use and integration with existing healthcare systems, we need full FHIR R4 compliance with all standard fields, extensions, and relationships.

## Acceptance Criteria

### Schema Implementation
- [ ] Implement complete FHIR R4 MedicationRequest resource structure
- [ ] Support all required fields per FHIR spec
- [ ] Support all optional fields used in prescriptions
- [ ] Implement FHIR data types correctly (CodeableConcept, Reference, etc.)
- [ ] Support FHIR extensions for prescription-specific data
- [ ] Implement resource relationships (Patient, Practitioner, Medication)

### Required FHIR Fields
```json
{
  "resourceType": "MedicationRequest",
  "id": "prescription-id",
  "identifier": [...],
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {...},
  "subject": {"reference": "Patient/..."},
  "authoredOn": "2026-02-11",
  "requester": {"reference": "Practitioner/..."},
  "dosageInstruction": [...],
  "dispenseRequest": {...}
}
```

### Validation
- [ ] Validate against FHIR R4 specification
- [ ] Pass FHIR validation tools
- [ ] Schema validation on create/update
- [ ] Error messages for invalid FHIR data

### Serialization
- [ ] JSON serialization per FHIR spec
- [ ] XML serialization support (optional for demo)
- [ ] FHIR Bundle support for batch operations
- [ ] Pretty printing option

### Search & Query
- [ ] Implement FHIR search parameters
- [ ] Support _include for related resources
- [ ] Support _revinclude for reverse includes
- [ ] Date range queries
- [ ] Status filtering
- [ ] Patient-specific queries

### Migration
- [ ] Backward compatibility with existing prescriptions
- [ ] Migration script for existing data
- [ ] Dual-mode support (simplified + full FHIR)
- [ ] Gradual migration path

### Interoperability
- [ ] Import FHIR bundles from external systems
- [ ] Export prescriptions as FHIR bundles
- [ ] Support standard terminologies (SNOMED CT, LOINC, RxNorm)
- [ ] National drug codes (SAHPRA)

## API Integration Points

```
POST /fhir/MedicationRequest
GET  /fhir/MedicationRequest/{id}
PUT  /fhir/MedicationRequest/{id}
GET  /fhir/MedicationRequest?patient={id}&status=active
POST /fhir/Bundle (batch operations)
GET  /fhir/metadata (capability statement)
```

## Technical Implementation

**Library:** fhir.resources (Python)  
**Validation:** fhir-validator or HAPI FHIR  
**Terminology:** Local terminology server or external (SNOMED CT)

## Estimation
- **Story Points**: 13
- **Time Estimate**: 5-7 days
- **Dependencies**: US-002 (Create Prescription) - extends it

## Notes

### Why Full FHIR?
- Integration with existing EHR systems
- International standard compliance
- Future interoperability with healthcare networks
- Regulatory requirements in production

### Simplified Mode
Keep simplified mode for:
- Demo environments
- Quick testing
- Educational purposes
- Mobile app performance

### Configuration
```python
# config.py
FHIR_MODE = "full"  # or "simplified"
FHIR_VERSION = "R4"
VALIDATION_STRICT = True
```

## Related Stories
- Extends: US-002 (Create Digital Prescription)
- Related: US-019 (Mobile Wallet Deep Integration)
