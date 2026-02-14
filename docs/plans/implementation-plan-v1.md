# Digital Prescription Demo - Technical Implementation Plan

## Executive Summary

This plan outlines the technical approach for building a digital prescription demo using DIDx's verifiable identity infrastructure. After thorough analysis of available options, this document provides a recommended architecture, implementation phases, and risk mitigation strategies.

## Analysis of Base Project Options

### Option 1: DSRCorporation/ssi-medical-prescriptions-demo

**Repository:** https://github.com/DSRCorporation/ssi-medical-prescriptions-demo

**Pros:**
- ✅ Purpose-built for medical prescriptions
- ✅ Complete Go-based backend with prescription logic
- ✅ Uses Hyperledger Aries (framework-go) and cheqd-node
- ✅ Includes OpenAPI specs, mock server, integration tests
- ✅ W3C Verifiable Credentials implementation
- ✅ DIDComm messaging protocols
- ✅ Docker-based deployment ready

**Cons:**
- ❌ Uses Go (smaller talent pool than Python/Node)
- ❌ Uses framework-go (different from DIDx's ACA-Py)
- ❌ May require adaptation to connect to DIDx CloudAPI
- ❌ AGPL-3.0 license (more restrictive than Apache-2.0)
- ❌ Less active development (last update unknown)

**Integration Complexity:** MEDIUM-HIGH
- Would need to replace cheqd-node integration with DIDx CloudAPI calls
- Prescription logic is solid but needs API adaptation layer

---

### Option 2: DIDx Native Stack (RECOMMENDED)

**Repositories:**
- **acapy-cloud**: https://github.com/didx-xyz/acapy-cloud (Python/FastAPI)
- **aries-cloudcontroller-python**: https://github.com/didx-xyz/aries-cloudcontroller-python
- **yoma-mobile**: https://github.com/didx-xyz/yoma-mobile (React Native reference)

**Pros:**
- ✅ Direct compatibility with DIDx CloudAPI
- ✅ Active development (updated Feb 2026)
- ✅ Apache-2.0 license (business-friendly)
- ✅ Cloud-native with Kubernetes/Tilt
- ✅ Comprehensive documentation
- ✅ FastAPI = modern, fast, typed Python
- ✅ Python = larger developer community
- ✅ Client library available (aries-cloudcontroller)
- ✅ Real mobile app example (Yoma)

**Cons:**
- ❌ No prescription-specific logic (generic SSI platform)
- ❌ Requires building prescription domain layer
- ❌ More setup complexity (K8s/Tilt vs Docker Compose)

**Integration Complexity:** MEDIUM
- Direct API compatibility
- Need to build prescription business logic layer
- More upfront work but cleaner integration

---

## Recommendation: Hybrid Approach

**Primary Base:** DIDx acapy-cloud + aries-cloudcontroller-python

**Rationale:**
1. **API Compatibility**: Direct integration with DIDx testnet (https://cloudapi.test.didxtech.com)
2. **Support**: Being a DIDx partner, using their stack ensures better support
3. **Future-Proof**: Aligned with DIDx's roadmap
4. **Licensing**: Apache-2.0 is more permissive for commercial use
5. **Community**: Python/FastAPI has broader adoption

**Prescription Logic Source:** Adapt concepts from DSRCorporation project
- Study their prescription data model
- Adapt FHIR-based prescription structure
- Use their workflow as reference implementation

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DIGITAL PRESCRIPTION DEMO                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   DOCTOR     │  │   PATIENT    │  │  PHARMACIST  │      Web Applications │
│  │    WEB APP   │  │  WALLET APP  │  │    WEB APP   │      (React/Vue.js)   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                 │                               │
│         └─────────────────┼─────────────────┘                               │
│                           │                                                 │
│                    ┌──────▼───────┐                                        │
│                    │  FRONTEND    │                                        │
│                    │    PROXY     │        API Gateway                     │
│                    │   (Nginx)    │                                        │
│                    └──────┬───────┘                                        │
│                           │                                                 │
│  ┌────────────────────────┼─────────────────────────────────────────┐     │
│  │                        ▼                                         │     │
│  │  ┌─────────────────────────────────────────────────────────────┐ │     │
│  │  │              PRESCRIPTION API LAYER                         │ │     │
│  │  │              (FastAPI - Python)                             │ │     │
│  │  │                                                             │ │     │
│  │  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │ │     │
│  │  │  │  Auth       │ │ Prescription │ │    Verification       │ │ │     │
│  │  │  │  Service    │ │   Service    │ │     Service           │ │ │     │
│  │  │  └─────────────┘ └──────────────┘ └───────────────────────┘ │ │     │
│  │  └─────────────────────────────────────────────────────────────┘ │     │
│  │                        │                                         │     │
│  │  ┌─────────────────────┼─────────────────────────────────────┐  │     │
│  │  │                     ▼                                     │  │     │
│  │  │  ┌─────────────────────────────────────────────────────┐  │  │     │
│  │  │  │              DIDx CLOUD API CLIENT                   │  │  │     │
│  │  │  │         (aries-cloudcontroller-python)              │  │  │     │
│  │  │  └─────────────────────────────────────────────────────┘  │  │     │
│  │  └───────────────────────────────────────────────────────────┘  │     │
│  │                              │                                   │     │
│  │                              ▼                                   │     │
│  │  ┌─────────────────────────────────────────────────────────────┐│     │
│  │  │                 DIDx TESTNET                                ││     │
│  │  │    https://cloudapi.test.didxtech.com                       ││     │
│  │  │                                                             ││     │
│  │  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ ││     │
│  │  │  │   ACA-Py    │ │   Trust      │ │    DID Registry       │ ││     │
│  │  │  │   Agents    │ │   Registry   │ │    (cheqd)            │ ││     │
│  │  │  └─────────────┘ └──────────────┘ └───────────────────────┘ ││     │
│  │  └─────────────────────────────────────────────────────────────┘│     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Stack

### Backend (Prescription API)
- **Framework**: FastAPI (Python 3.12+)
- **Key Libraries**:
  - `aries-cloudcontroller` - DIDx API client
  - `fhir.resources` - FHIR R4 data models
  - `pydantic` - Data validation
  - `sqlalchemy` - Database ORM (for prescription state)
  - `alembic` - Database migrations
  - `pytest` - Testing
- **Database**: PostgreSQL (prescription state, audit logs)
- **Cache**: Redis (session management, repeat tracking)

### Frontend (3 Web Apps)
- **Framework**: React 18+ with TypeScript
- **UI Library**: TailwindCSS + HeadlessUI
- **State Management**: Zustand
- **HTTP Client**: Axios
- **QR Code**: qrcode.react
- **Date/Time**: date-fns

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **API Documentation**: OpenAPI 3.0 + Swagger UI
- **Development**: Tilt (for K8s) or Docker Compose

### External APIs
- **DIDx CloudAPI**: https://cloudapi.test.didxtech.com
- **Authentication**: OAuth 2.0
- **DID Method**: did:cheqd:testnet

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Working backend with DIDx integration

**Stories**: None (infrastructure)

**Tasks**:
1. Fork/setup acapy-cloud reference
2. Create Prescription API project structure
3. Set up Docker Compose environment
4. Integrate aries-cloudcontroller-python
5. Implement OAuth 2.0 authentication with DIDx
6. Create DID management endpoints
7. Set up PostgreSQL + Redis
8. Create basic FHIR prescription model

**Deliverables**:
- Backend API running locally
- Authentication with DIDx testnet
- API documentation (Swagger)
- Database schema

**Success Criteria**:
- Can authenticate with DIDx
- Can create/read DIDs
- API responds to requests

---

### Phase 2: Doctor Flow (Week 2)
**Goal**: Doctor can create and sign prescriptions

**Stories**: US-001, US-002, US-003

**Tasks**:
1. Build Doctor web app
2. Implement DID setup wizard
3. Create prescription form (FHIR-based)
4. Integrate with DIDx credential issuance
5. Implement digital signing flow
6. Create prescription preview
7. Test end-to-end doctor flow

**Deliverables**:
- Doctor web app (responsive)
- Prescription creation workflow
- Digital signing working
- 3-5 test prescriptions

**Success Criteria**:
- Doctor can authenticate
- Doctor can create prescription
- Doctor can sign prescription
- Prescription stored as VC

---

### Phase 3: Patient Flow (Week 3)
**Goal**: Patient can receive and view prescriptions

**Stories**: US-005, US-006, US-007

**Tasks**:
1. Build Patient wallet web app
2. Implement wallet setup
3. Create credential receiving flow (DIDComm)
4. Build prescription list view
5. Create prescription detail view
6. Implement QR code display
7. Add notification system

**Deliverables**:
- Patient wallet web app
- Prescription receiving workflow
- Prescription viewing interface
- QR code generation

**Success Criteria**:
- Patient can set up wallet
- Patient receives prescription
- Patient can view prescription details
- QR code scannable

---

### Phase 4: Pharmacist Flow (Week 4)
**Goal**: Pharmacist can verify and dispense

**Stories**: US-009, US-010, US-011

**Tasks**:
1. Build Pharmacist web app
2. Implement pharmacist DID setup
3. Create prescription verification flow
4. Build dispensing interface
5. Implement verification status display
6. Create dispensing confirmation
7. Add medication checklist

**Deliverables**:
- Pharmacist web app
- Verification workflow
- Dispensing interface
- Test dispensing records

**Success Criteria**:
- Pharmacist can authenticate
- Can verify prescription authenticity
- Can view prescription items
- Can record dispensing

---

### Phase 5: Advanced Features (Week 5-6)
**Goal**: Complete all remaining stories

**Stories**: US-004, US-008, US-012, US-013, US-014, US-015, US-016

**Tasks**:
1. Implement DIDComm messaging (US-004, US-008)
2. Build time-based validation (US-012)
3. Create expiration handling (US-013)
4. Implement repeat/refill logic (US-014)
5. Add revocation capability (US-015)
6. Build audit logging system (US-016)
7. Create demo scripts and test data

**Deliverables**:
- Complete end-to-end flow
- Time-based validation working
- Repeat/refill tracking
- Audit trail viewable
- Demo video/script

**Success Criteria**:
- Full workflow: Doctor → Patient → Pharmacist
- All 16 user stories functional
- Demo-ready system

---

## Story Mapping to Phases

| Phase | Stories | Focus |
|-------|---------|-------|
| 1 | Infrastructure | Backend setup |
| 2 | US-001, US-002, US-003 | Doctor flow |
| 3 | US-005, US-006, US-007 | Patient flow |
| 4 | US-009, US-010, US-011 | Pharmacist flow |
| 5 | US-004, US-008, US-012-016 | Integration & advanced |

---

## MVP for Demo

**Must-Have for Initial Demo** (Week 4):
1. ✅ Doctor authentication and DID setup
2. ✅ Create and sign prescription
3. ✅ Patient wallet setup
4. ✅ Receive prescription in wallet
5. ✅ View prescription details
6. ✅ Pharmacist authentication
7. ✅ Verify prescription authenticity
8. ✅ View items for dispensing

**Nice-to-Have** (Week 5-6):
- DIDComm messaging automation
- Time-based validation warnings
- Repeat/refill tracking
- Audit trail view
- Revocation flow

---

## Risk Analysis & Mitigation

### Risk 1: DIDx API Integration Complexity
**Impact**: HIGH | **Probability**: MEDIUM

**Mitigation**:
- Start with aries-cloudcontroller-python (official client)
- Use existing Yoma mobile as reference
- Contact DIDx early for API credentials
- Build simple "hello world" integration first

### Risk 2: Time Constraints
**Impact**: HIGH | **Probability**: HIGH

**Mitigation**:
- Prioritize MVP stories (8 must-haves)
- Defer DIDComm to Phase 5 (can demo with manual steps)
- Use mock data for complex scenarios
- Parallel development (2-3 developers)

### Risk 3: FHIR Complexity
**Impact**: MEDIUM | **Probability**: MEDIUM

**Mitigation**:
- Use simplified FHIR subset
- Start with basic MedicationRequest resource
- Use fhir.resources library for validation
- Mock complex clinical scenarios

### Risk 4: SSI Learning Curve
**Impact**: MEDIUM | **Probability**: HIGH

**Mitigation**:
- Study DSRCorporation implementation
- Use DIDx documentation
- Test with mock server first
- Simplify credential schemas for demo

### Risk 5: Browser/Web vs Mobile
**Impact**: LOW | **Probability**: LOW

**Mitigation**:
- Build responsive web apps (work on mobile too)
- Use React for all frontends
- Test on mobile browsers
- Can wrap as PWA later

---

## Data Model

### Prescription (FHIR R4 Based)
```python
class Prescription(BaseModel):
    prescription_id: str  # RX-{timestamp}-{uuid}
    status: PrescriptionStatus  # draft | signed | issued | active | completed | expired | revoked
    
    # Doctor Info
    doctor_did: str
    doctor_name: str
    doctor_practice: str
    doctor_registration: str
    
    # Patient Info
    patient_did: str
    patient_name: str
    patient_id_number: str
    
    # Medications
    medications: List[Medication]
    
    # Metadata
    diagnosis_code: Optional[str]  # ICD-10
    issued_date: datetime
    valid_until: datetime
    repeats_allowed: int = 0
    repeats_remaining: int = 0
    last_dispensed: Optional[datetime]
    
    # Digital signature
    credential_id: Optional[str]
    revocation_id: Optional[str]

class Medication(BaseModel):
    name: str
    generic_name: Optional[str]
    strength: str
    quantity: int
    dosage_instructions: str
    route: str  # oral | topical | etc.
    duration: str
    sahpra_code: Optional[str]
```

---

## API Endpoints

### Authentication
- `POST /auth/login` - OAuth with DIDx
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout

### DIDs
- `POST /dids/create` - Create new DID
- `GET /dids/{did}` - Resolve DID
- `GET /dids` - List my DIDs

### Prescriptions (Doctor)
- `POST /prescriptions` - Create prescription
- `POST /prescriptions/{id}/sign` - Sign prescription
- `POST /prescriptions/{id}/send` - Send to patient
- `GET /prescriptions/issued` - List issued prescriptions
- `POST /prescriptions/{id}/revoke` - Revoke prescription

### Prescriptions (Patient)
- `GET /prescriptions/received` - List received prescriptions
- `POST /prescriptions/{id}/accept` - Accept prescription
- `POST /prescriptions/{id}/share` - Share with pharmacist
- `GET /prescriptions/{id}` - View prescription details

### Verification (Pharmacist)
- `POST /verify` - Verify prescription VC
- `GET /prescriptions/{id}/validity` - Check validity
- `POST /dispensing/record` - Record dispensing
- `GET /dispensing/history` - View dispensing history

### Admin
- `GET /audit/logs` - View audit logs
- `GET /trust-registry` - Query trust registry

---

## Development Environment

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Git

### Quick Start
```bash
# Clone repository
git clone <your-fork>
cd digital-prescription-demo

# Start infrastructure
docker-compose up -d postgres redis

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn main:app --reload

# Install frontend dependencies
cd ../frontend
cd doctor-app && npm install
cd ../patient-app && npm install
cd ../pharmacist-app && npm install

# Start frontends (in separate terminals)
npm run dev
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend/doctor-app
npm test
```

---

## Success Criteria

### Functional
- [ ] Doctor can create and sign a prescription
- [ ] Prescription appears in patient's wallet
- [ ] Patient can share prescription with pharmacist
- [ ] Pharmacist can verify prescription authenticity
- [ ] Pharmacist can view prescription items
- [ ] Prescription includes digital signature
- [ ] Verification shows doctor's credentials
- [ ] System prevents dispensing of expired prescriptions

### Technical
- [ ] All API calls succeed to DIDx testnet
- [ ] DIDs created and resolvable
- [ ] VCs issued and verifiable
- [ ] Docker Compose runs complete stack
- [ ] 3 web apps responsive and functional
- [ ] Audit logs capture all actions
- [ ] Documentation complete

### Demo-Ready
- [ ] End-to-end workflow demonstrable
- [ ] Test data pre-populated
- [ ] Demo script written
- [ ] Video recording capability
- [ ] Reset/cleanup functionality

---

## Next Steps

1. **Decision**: Confirm use of DIDx native stack vs DSRCorporation
2. **Setup**: Obtain DIDx testnet credentials (hello@didx.co.za)
3. **Team**: Assign developers to parallel tracks
4. **Sprint**: Begin Phase 1 (Foundation)
5. **Review**: Weekly check-ins against plan

---

## Open Questions

1. Can we get early access to DIDx testnet credentials?
2. Is there a simplified API for demo purposes?
3. Can DIDx provide technical support during development?
4. Are there sample/test DIDs we can use?
5. What's the preferred frontend framework (React/Vue/Angular)?
6. Should we support mobile apps or web-only for demo?

---

## Conclusion

The recommended approach is to use DIDx's native stack (acapy-cloud + aries-cloudcontroller-python) as the foundation. While this requires building prescription-specific logic from scratch, it ensures:

1. **Native compatibility** with DIDx CloudAPI
2. **Better support** as a DIDx partner
3. **Future alignment** with DIDx roadmap
4. **Cleaner architecture** purpose-built for your use case

The DSRCorporation project serves as an excellent reference for prescription domain logic and FHIR implementation, but adapting its Go codebase to DIDx's Python/ACA-Py stack would require significant rework.

**Timeline Estimate**: 5-6 weeks for complete implementation
**MVP Timeline**: 4 weeks for demo-ready system
