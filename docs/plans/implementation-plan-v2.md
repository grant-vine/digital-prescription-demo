# Digital Prescription Demo - REVISED Implementation Plan v2.0

## Executive Summary

**Status:** ✅ Ready for Development (Critical Issues Resolved)  
**Timeline:** 4-week MVP Demo OR 8-10 week Full Implementation  
**Base Decision:** DIDx Native Stack (confirmed)  
**Architecture:** React frontend + Python/FastAPI backend + DIDx CloudAPI

---

## ✅ Critical Issues Resolved (Based on Momus Review)

### 1. Architecture Decision: CONFIRMED - DIDx Native Stack

**Decision:** Use DIDx's acapy-cloud ecosystem (NOT DSRCorporation fork)

**Rationale:**
- Direct DIDx CloudAPI compatibility
- Better partner support
- Apache-2.0 license (business-friendly)
- Active development (Python/FastAPI)
- DSRCorporation project serves as reference for prescription domain logic only

**Stack:**
- **Backend:** Python 3.12 + FastAPI + aries-cloudcontroller-python
- **Frontend:** React 18 + TypeScript + TailwindCSS (single app, role-based views)
- **Infrastructure:** Docker Compose (not Kubernetes for demo simplicity)
- **API:** DIDx CloudAPI testnet

---

### 2. DIDx Access: PREREQUISITE - Must Confirm Before Day 1

**Action Required:** Contact DIDx BEFORE starting development

**Contact:** hello@didx.co.za  
**Request:**
- [ ] OAuth 2.0 client credentials for testnet
- [ ] API documentation access
- [ ] Technical support channel (Slack/Discord/email)
- [ ] Testnet availability guarantees

**Fallback Plan:** If DIDx access delayed >3 days:
1. Use local ACA-Py instance for development
2. Build with mock DIDx client interface
3. Switch to real DIDx when available

---

### 3. DIDComm Strategy: SIMPLIFIED for Demo

**Decision:** Use QR Code Flow (NOT full DIDComm) for 4-week MVP

**Why:**
- DIDComm adds 2-3 weeks complexity
- QR codes achieve same demo goals
- Easier to understand for demo audience
- Can upgrade to DIDComm post-demo

**QR Code Flow:**
1. Doctor creates prescription → generates QR code
2. Patient scans QR code → prescription loads into wallet
3. Patient shares with pharmacist → displays new QR code
4. Pharmacist scans → verifies and dispenses

**Post-Demo:** Implement full DIDComm messaging

---

### 4. Timeline: REALISTIC - Two Options

#### Option A: MVP Demo (RECOMMENDED) - 4 Weeks
**For:** Quick demo to stakeholders, proof of concept

**Includes:**
- ✅ Doctor authentication & DID setup (US-001, US-003)
- ✅ Create & sign prescription (US-002)
- ✅ Patient wallet setup (US-005)
- ✅ Receive prescription via QR (US-006 simplified)
- ✅ View prescription (US-007)
- ✅ Share with pharmacist via QR (US-008 simplified)
- ✅ Pharmacist authentication (US-009)
- ✅ Verify prescription (US-010)
- ✅ View items for dispensing (US-011)
- ✅ Basic time validation (US-012)
- ✅ Demo test data & scripts (US-017 - NEW)

**Excludes (Post-Demo):**
- Full DIDComm messaging
- Prescription repeats (US-014)
- Revocation (US-015)
- Full audit trail (US-016)
- Complex expiration workflows

#### Option B: Full Implementation - 8-10 Weeks
**For:** Production-ready system with all features

**Includes:** All 16 user stories + full DIDComm + advanced features

---

### 5. FHIR: SIMPLIFIED - Not Full R4

**Decision:** Use "FHIR-inspired" schema, not strict FHIR R4

**Prescription Schema (10 fields max):**
```python
class Prescription(BaseModel):
    prescription_id: UUID  # RX-{uuid}
    doctor_did: str
    doctor_name: str
    patient_did: str
    patient_name: str
    medications: List[Medication]
    issued_date: datetime
    valid_until: datetime
    status: str  # draft | signed | active | dispensed | expired
    signature: str  # VC proof

class Medication(BaseModel):
    name: str
    strength: str
    quantity: int
    instructions: str
```

**Rationale:**
- Simpler to implement
- Easier for demo audience to understand
- Faster development
- Can migrate to full FHIR later

---

## Revised Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MVP ARCHITECTURE (4-WEEK DEMO)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         SINGLE REACT APP (Role-Based Views)             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │    Doctor    │  │    Patient   │  │  Pharmacist  │   │   │
│  │  │    View      │  │    Wallet    │  │    View      │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PRESCRIPTION API (FastAPI)                 │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐ │   │
│  │  │  Auth       │ │ Prescription │ │   Verification    │ │   │
│  │  │  Service    │ │   Service    │ │     Service       │ │   │
│  │  └─────────────┘ └──────────────┘ └───────────────────┘ │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                       │                                         │
│           ┌───────────┴───────────┐                            │
│           ▼                       ▼                            │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │   PostgreSQL     │    │   DIDx CloudAPI  │                 │
│  │   (Prescriptions,│    │   (DIDs, VCs,    │                 │
│  │    Audit Logs)   │    │   Verification)  │                 │
│  └──────────────────┘    └──────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Revised Technical Stack

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **API Client:** `aries-cloudcontroller-python`
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Testing:** pytest
- **Auth:** OAuth 2.0 via DIDx

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** TailwindCSS
- **Components:** shadcn/ui (pre-built accessible components)
- **State:** Zustand
- **HTTP:** Axios
- **QR Codes:** qrcode.react
- **Dates:** date-fns

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** Traefik (simpler than Nginx for local dev)
- **Docs:** Swagger UI (auto-generated from FastAPI)

---

## Revised Implementation Phases (MVP - 4 Weeks)

### Week 1: Foundation + Architecture
**Goal:** Working backend with DIDx integration proof-of-concept

**Tasks:**
1. Set up project structure (backend/frontend folders)
2. Create Docker Compose environment (PostgreSQL, backend, frontend)
3. **CRITICAL:** Obtain DIDx testnet credentials
4. Build "Hello DIDx" integration test (create DID, verify connection)
5. Set up FastAPI project structure
6. Create database schema (prescriptions, audit_logs)
7. Implement OAuth 2.0 authentication with DIDx
8. Create simplified prescription model (FHIR-inspired)
9. Add medication seed data (50 common drugs)
10. Create trust registry mock (in-memory, hardcoded trusted DIDs)

**Deliverables:**
- [ ] Backend running at http://localhost:8000
- [ ] Frontend running at http://localhost:3000
- [ ] Can authenticate with DIDx testnet
- [ ] Can create/resolve DIDs
- [ ] Database schema created

**Success Criteria:**
- DIDx "hello world" works
- Database migrations run
- API documentation available at /docs

---

### Week 2: Doctor Flow
**Goal:** Doctor can create, sign, and generate QR code for prescription

**Stories:** US-001, US-002, US-003

**Tasks:**
1. Build Doctor view (React component)
2. Implement DID setup wizard
3. Create prescription form:
   - Patient DID input (manual or scan)
   - Medication selector (from seed data)
   - Dosage & quantity inputs
   - Validity period selector
4. Implement prescription signing:
   - Call DIDx to issue VC
   - Generate proof
   - Store in database
5. Generate QR code for prescription
6. Create prescription preview screen
7. Add prescription list view (doctor's issued prescriptions)

**Deliverables:**
- [ ] Doctor can authenticate
- [ ] Doctor can create prescription
- [ ] Doctor can sign prescription (VC issued)
- [ ] Doctor can generate QR code
- [ ] 3-5 test prescriptions created

**Success Criteria:**
- End-to-end doctor flow works
- QR code scannable
- Prescription stored in database

---

### Week 3: Patient Flow
**Goal:** Patient can scan QR code, view, and share prescription

**Stories:** US-005, US-006 (simplified), US-007, US-008 (simplified)

**Tasks:**
1. Build Patient wallet view (React component)
2. Implement wallet setup:
   - DID creation via DIDx
   - Basic profile setup
3. Create QR code scanner component
4. Implement prescription receiving:
   - Scan doctor's QR code
   - Load prescription into wallet
   - Verify signature
5. Build prescription list view
6. Create prescription detail view
7. Implement "Share with Pharmacist" (generate new QR code)
8. Add notification system (in-app only for demo)

**Deliverables:**
- [ ] Patient can set up wallet
- [ ] Patient can scan QR to receive prescription
- [ ] Patient can view prescription details
- [ ] Patient can generate QR to share with pharmacist
- [ ] 5-10 test patients with prescriptions

**Success Criteria:**
- Doctor → Patient flow via QR code works
- Patient → Pharmacist flow via QR code works

---

### Week 4: Pharmacist Flow + Demo Prep
**Goal:** Pharmacist can verify and record dispensing

**Stories:** US-009, US-010, US-011, US-017 (NEW - Demo Prep)

**Tasks:**
1. Build Pharmacist view (React component)
2. Implement pharmacist DID setup
3. Create QR code scanner for receiving prescriptions
4. Build verification flow:
   - Verify VC signature via DIDx
   - Check doctor in trust registry
   - Verify not expired
5. Create dispensing interface:
   - Medication checklist
   - Mark as dispensed
   - Record dispensing event
6. Add verification result display
7. **Demo Prep (US-017):**
   - Create 3 test doctors with profiles
   - Create 5 test patients
   - Create 2 test pharmacies
   - Seed 15 sample prescriptions in various states
   - Write demo script with timing
   - Build "reset demo" button
   - Create demo video script
8. Polish UI/UX
9. Bug fixes
10. Performance optimization

**Deliverables:**
- [ ] Pharmacist can authenticate
- [ ] Can verify prescription authenticity
- [ ] Can view prescription items
- [ ] Can record dispensing
- [ ] Demo script complete
- [ ] Test data seeded

**Success Criteria:**
- Full end-to-end workflow: Doctor → Patient → Pharmacist
- Demo can be run from start to finish in 5 minutes
- System is stable and demo-ready

---

## MVP Story Mapping

| Week | Primary Stories | Dependencies |
|------|----------------|--------------|
| 1 | Infrastructure | DIDx access (CRITICAL) |
| 2 | US-001, US-002, US-003 | Week 1 |
| 3 | US-005, US-006, US-007, US-008 | Week 2 |
| 4 | US-009, US-010, US-011, US-017 | Week 3 |

**Total Stories:** 11 (16 original minus 5 deferred)

---

## Database Schema (Revised)

```sql
-- Prescriptions table
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id VARCHAR(50) UNIQUE NOT NULL, -- RX-{uuid}
    
    -- Doctor info
    doctor_did VARCHAR(255) NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    doctor_practice VARCHAR(255),
    
    -- Patient info
    patient_did VARCHAR(255) NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    
    -- Prescription details
    medications JSONB NOT NULL,
    diagnosis_code VARCHAR(50),
    
    -- Status and dates
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    issued_date TIMESTAMP NOT NULL,
    valid_until TIMESTAMP NOT NULL,
    
    -- Digital signature
    credential_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dispensing events table
CREATE TABLE dispensing_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_id UUID REFERENCES prescriptions(id),
    pharmacist_did VARCHAR(255) NOT NULL,
    pharmacy_name VARCHAR(255),
    dispensed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    medications_dispensed JSONB NOT NULL
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_did VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    prescription_id UUID REFERENCES prescriptions(id),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trust registry (mock for demo)
CREATE TABLE trusted_entities (
    did VARCHAR(255) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- doctor | pharmacist | pharmacy
    name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## API Endpoints (Revised - Simplified)

### Authentication
```
POST /auth/login          # OAuth with DIDx
POST /auth/callback       # OAuth callback
POST /auth/logout         # Logout
GET  /auth/me             # Current user
```

### DIDs
```
POST /dids                # Create DID
GET  /dids/:did           # Resolve DID
GET  /dids                # List my DIDs
```

### Prescriptions (Doctor)
```
POST /prescriptions                    # Create prescription
POST /prescriptions/:id/sign           # Sign (issue VC)
GET  /prescriptions/issued             # List my issued prescriptions
GET  /prescriptions/:id/qr             # Generate QR code
```

### Prescriptions (Patient)
```
POST /prescriptions/scan               # Scan QR code to receive
GET  /prescriptions/received           # List received prescriptions
GET  /prescriptions/:id                # View prescription
POST /prescriptions/:id/share          # Generate share QR
```

### Verification (Pharmacist)
```
POST /verify                           # Verify prescription VC
POST /verify/scan                      # Scan QR and verify
POST /dispensing                       # Record dispensing
GET  /dispensing/history               # View dispensing history
```

### Admin/Demo
```
POST /demo/reset                       # Reset demo data
GET  /demo/seed                        # Seed test data
GET  /health                           # Health check
```

---

## QR Code Data Format

### Doctor → Patient QR Code
```json
{
  "type": "prescription",
  "version": "1.0",
  "prescription_id": "RX-uuid-here",
  "doctor_did": "did:cheqd:testnet:abc123",
  "patient_did": "did:cheqd:testnet:xyz789",
  "issued_at": "2026-02-11T10:00:00Z",
  "signature": "base64-encoded-signature"
}
```

### Patient → Pharmacist QR Code
```json
{
  "type": "prescription_share",
  "version": "1.0",
  "prescription_id": "RX-uuid-here",
  "patient_did": "did:cheqd:testnet:xyz789",
  "shared_at": "2026-02-11T14:30:00Z",
  "signature": "base64-encoded-signature"
}
```

---

## Medication Seed Data (Sample)

```csv
name,generic_name,strength,schedule
Amoxicillin,Amoxicillin,500mg,4
Paracetamol,Paracetamol,500mg,0
Ibuprofen,Ibuprofen,400mg,2
Aspirin,Acetylsalicylic acid,100mg,2
Metformin,Metformin,500mg,4
Amlodipine,Amlodipine,5mg,4
Lisinopril,Lisinopril,10mg,4
Atorvastatin,Atorvastatin,20mg,4
Omeprazole,Omeprazole,20mg,0
Cetirizine,Cetirizine,10mg,0
```

*(Full list: 50 common medications in meds.csv)*

---

## Risk Mitigation (Revised)

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| DIDx access delayed | Medium | Critical | Fallback to local ACA-Py |
| QR code flow too simple | Low | Medium | Can upgrade to DIDComm later |
| Timeline slip | Medium | High | Cut features, not quality |
| DIDx API changes | Low | Medium | Use stable API version |
| Developer learning curve | High | Medium | Start with "Hello DIDx" |

---

## Success Criteria (MVP)

### Functional
- [ ] Doctor can create prescription
- [ ] Doctor can sign prescription (VC issued)
- [ ] Doctor can generate QR code
- [ ] Patient can scan QR to receive
- [ ] Patient can view prescription
- [ ] Patient can generate QR to share
- [ ] Pharmacist can scan QR
- [ ] Pharmacist can verify authenticity
- [ ] Pharmacist can record dispensing

### Technical
- [ ] All API calls to DIDx succeed
- [ ] DIDs created and resolvable
- [ ] VCs issued and verifiable
- [ ] Docker Compose runs complete stack
- [ ] Database persists data
- [ ] Demo reset works

### Demo-Ready
- [ ] End-to-end workflow demonstrable in 5 minutes
- [ ] Test data pre-populated
- [ ] Demo script written
- [ ] Reset/cleanup works
- [ ] UI is polished and professional

---

## Next Steps (Immediate)

### Before Development Starts (This Week)

1. **✅ Confirm DIDx Access**
   - Email hello@didx.co.za
   - Request testnet credentials
   - Confirm within 3 days or activate fallback plan

2. **✅ Confirm Team & Timeline**
   - Decide: 4-week MVP or 8-10 week full?
   - Confirm team size (recommend 2 developers)
   - Set start date

3. **✅ Setup Development Environment**
   - Clone repository structure
   - Install Docker, Python 3.12, Node.js 20
   - Run `docker-compose up`
   - Verify everything starts

4. **✅ Create Detailed Design**
   - Wireframes for 5 key screens
   - Database schema (SQL files)
   - OpenAPI spec (YAML)

5. **✅ Sprint Planning**
   - Break Week 1 into daily tasks
   - Assign owners
   - Set daily standup time

---

## Post-Demo Roadmap (After MVP)

### Phase 2: Enhanced Features (Weeks 5-6)
- Prescription repeats (US-014)
- Expiration handling (US-013)
- Basic audit trail (US-016)
- Revocation (US-015)

### Phase 3: Production Hardening (Weeks 7-8)
- Full DIDComm messaging
- Complete FHIR R4 support
- Security audit
- Performance optimization
- Full audit trail

### Phase 4: Scale (Weeks 9-10)
- Kubernetes deployment
- Monitoring & alerting
- Load testing
- Documentation
- Training materials

---

## Conclusion

This revised plan addresses all **5 critical issues** identified by Momus:

✅ **Architecture:** Confirmed DIDx native stack  
✅ **DIDx Access:** Prerequisite with fallback plan  
✅ **DIDComm:** Simplified to QR codes for MVP  
✅ **Timeline:** Realistic 4-week MVP defined  
✅ **FHIR:** Simplified schema, not full R4  

**The project is now ready for development.**

**Recommended Path:** 4-week MVP with QR code flows, then iterate to full DIDComm implementation.

---

**Plan Version:** 2.0  
**Last Updated:** 11 February 2026  
**Status:** ✅ Approved for Development
