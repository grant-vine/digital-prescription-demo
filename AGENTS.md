# Digital Prescription Demo - AGENTS.md

## Project Overview

**🎯 Technology Demo:** This is a technology demonstration project showcasing the rapid implementation of digital wallet solutions using an **agentic framework**. The goal is to demonstrate how AI agents can collaboratively build complex Self-Sovereign Identity (SSI) infrastructure through systematic planning and execution.

**Demo Focus:** Digital prescription system using Self-Sovereign Identity (SSI) infrastructure. Enables doctors to create and digitally sign prescriptions, patients to receive and manage them in digital wallets, and pharmacists to verify and dispense medications securely.

**Status:** Planning Phase - Ready for Development  
**Architecture:** Python/FastAPI backend + React Native mobile apps  
**SSI Infrastructure:** ACA-Py (local dev) → DIDx CloudAPI (production)  
**Standards:** W3C Verifiable Credentials, FHIR R4 (enhanced phase)  
**Repository:** https://github.com/grant-vine/digital-prescription-demo  
**Execution Plan:** `.sisyphus/plans/digital-prescription-mvp.md` (73 tasks, 4-week MVP)  

---

## Directory Structure

```
/Users/grantv/Code/rxdistribute/
├── README.md                          # Project overview and quick start
├── implementation-plan-v3.md          # Main implementation plan (CURRENT)
├── implementation-plan-v2.md          # Previous version (reference only)
├── implementation-plan.md             # Original version (reference only)
├── AGENTS.md                          # This file - AI agent reference
└── user-stories/                      # User stories directory
    ├── README.md                      # Index of all user stories
    ├── 001-doctor-authentication-did-setup.md
    ├── 002-create-digital-prescription.md
    ├── 003-sign-prescription-digital-signature.md
    ├── 004-send-prescription-patient-wallet.md
    ├── 005-patient-wallet-setup-authentication.md
    ├── 006-receive-prescription-wallet.md
    ├── 007-view-prescription-details.md
    ├── 008-share-prescription-pharmacist.md
    ├── 009-pharmacist-authentication-did-setup.md
    ├── 010-verify-prescription-authenticity.md
    ├── 011-view-prescription-items-dispensing.md
    ├── 012-time-based-prescription-validation.md
    ├── 013-handle-prescription-expiration.md
    ├── 014-support-prescription-repeats-refills.md
    ├── 015-revoke-cancel-prescription.md
    ├── 016-audit-trail-compliance-logging.md
    ├── 017-full-fhir-r4-implementation.md
    ├── 018-didcomm-v2-messaging.md
    ├── 019-demo-preparation-test-data.md
    ├── 020-advanced-audit-trail-reporting.md
    ├── 021-advanced-revocation-workflows.md
    ├── 022-advanced-time-based-validation.md
    ├── 023-mobile-wallet-deep-integration.md
    ├── 024-kubernetes-deployment.md
    └── 025-monitoring-observability.md
    └── developer-notes.md              # Agent work log and timing
```

---

## Milestone Strategy

This project uses **Git Branches and Tags** as milestone checkpoints that third-party developers can use as implementation starting points.

### Current Milestones

| Milestone | Branch/Tag | Description | Status |
|-----------|-----------|-------------|--------|
| **Ready to Dev** | `milestone/ready-to-dev` | Complete planning phase, all stories documented, execution plan approved | ✅ Current |
| Foundation | `milestone/foundation` | Monorepo initialized, Docker stack running | 🔄 Pending |
| Backend Core | `milestone/backend-core` | Auth and prescription API complete | 🔄 Pending |
| SSI Integration | `milestone/ssi-integration` | ACA-Py integrated, DID/VC/QR services ready | 🔄 Pending |
| Mobile Core | `milestone/mobile-core` | Theming, navigation, QR components done | 🔄 Pending |
| Doctor Flow | `milestone/doctor-flow` | Doctor create/sign/send prescription complete | 🔄 Pending |
| Patient Flow | `milestone/patient-flow` | Patient receive/view/share complete | 🔄 Pending |
| Pharmacist Flow | `milestone/pharmacist-flow` | Verification and dispensing complete | 🔄 Pending |
| System Features | `milestone/system-features` | Validation, repeats, revocation, audit done | 🔄 Pending |
| **MVP Complete** | `v1.0.0-mvp` | All 16 stories implemented, E2E tests passing | 🔄 Pending |

### Using Milestones

Third-party developers can start from any milestone:

```bash
# Clone and checkout a specific milestone
git clone https://github.com/grant-vine/digital-prescription-demo.git
cd digital-prescription-demo
git checkout milestone/ready-to-dev  # Or any other milestone

# View all available milestones
git branch -a | grep milestone/
git tag -l
```

### Creating Milestones

When completing a milestone:

```bash
# Create milestone branch from current state
git checkout -b milestone/milestone-name

# Tag significant releases
git tag -a v1.0.0-mvp -m "MVP Complete - All 16 stories implemented"

# Push milestone and tags
git push origin milestone/milestone-name
git push origin --tags
```

### Developer Notes

**IMPORTANT:** All agents must update `developer-notes.md` when completing work:

```markdown
#### [DATE] - [AGENT NAME]

**Tasks Completed:**
- [TASK-ID]: [Brief description]

**Time Taken:**
- Start: [HH:MM]
- End: [HH:MM]
- Duration: [X hours Y minutes]

**Files Modified:**
- `path/to/file` - [what changed]

**Notes:**
[Any important context]

**Next Steps:**
[What should happen next]
```

**Use actual dates from CLI commands for timing.**

---

## User Story Standards

### File Naming Convention
```
user-stories/###-descriptive-slug.md
```
- `###` = Zero-padded 3-digit number (001-025)
- `descriptive-slug` = Lowercase, hyphen-separated
- All files use `.md` extension

### Story Format Template
Every user story MUST include:

```markdown
## Title
[Clear, concise title]

## User Story
As a [type of user], I want [goal], so that [benefit].

## Description
[2-3 sentences explaining the feature and value proposition]

## Context
[Background information, technical constraints, business rules]

## Acceptance Criteria
[Bullet list of testable criteria with checkboxes - [ ]]

## API Integration Points
```
[API endpoints if applicable]
```

## Technical Implementation
[Code examples, schemas, implementation notes]

## Notes
[Constraints, considerations, edge cases, demo simplifications]

## Estimation
- **Story Points**: [Fibonacci number]
- **Time Estimate**: [X-Y days]
- **Dependencies**: [US-### dependencies]

## Related Stories
- [US-###: Story name]
```

---

## Story Categories

### MVP Phase (Weeks 1-4) - Core Workflow
| ID | Story | Actor | Points |
|----|-------|-------|--------|
| 001 | Doctor Authentication & DID Setup | Doctor | 5 |
| 002 | Create Digital Prescription | Doctor | 8 |
| 003 | Sign Prescription with Digital Signature | Doctor | 5 |
| 004 | Send Prescription to Patient Wallet (QR) | Doctor | 5 |
| 005 | Patient Wallet Setup & Authentication | Patient | 5 |
| 006 | Receive Prescription in Wallet (QR) | Patient | 5 |
| 007 | View Prescription Details | Patient | 3 |
| 008 | Share Prescription with Pharmacist (QR) | Patient | 5 |
| 009 | Pharmacist Authentication & DID Setup | Pharmacist | 5 |
| 010 | Verify Prescription Authenticity | Pharmacist | 8 |
| 011 | View Prescription Items for Dispensing | Pharmacist | 5 |

### Core System (Weeks 3-4) - System Features
| ID | Story | Actor | Points |
|----|-------|-------|--------|
| 012 | Time-Based Prescription Validation | System | 5 |
| 013 | Handle Prescription Expiration | System | 3 |
| 014 | Support Prescription Repeats/Refills | Doctor/Pharmacist | 8 |
| 015 | Revoke or Cancel Prescription | Doctor | 5 |
| 016 | Audit Trail & Compliance Logging | System | 5 |

### Enhanced Phase (Weeks 7-10) - Production Features
| ID | Story | Actor | Points |
|----|-------|-------|--------|
| 017 | Full FHIR R4 Implementation | System | 13 |
| 018 | DIDComm v2 Messaging | System | 13 |
| 019 | Demo Preparation & Test Data | System | 5 |
| 020 | Advanced Audit Trail & Reporting | System | 8 |
| 021 | Advanced Revocation Workflows | Doctor | 5 |
| 022 | Advanced Time-Based Validation | System | 5 |
| 023 | Mobile Wallet Deep Integration | Patient | 13 |

### Production Phase (Weeks 11-14) - Operations
| ID | Story | Actor | Points |
|----|-------|-------|--------|
| 024 | Kubernetes Deployment | System | 8 |
| 025 | Monitoring & Observability | System | 8 |

**Total Stories:** 25  
**Total Story Points:** 158  
**Timeline:** 14 weeks (2-person team)

---

## Critical Dependencies

### Story Dependency Chain
```
US-001 (Doctor Auth)
  ↓
US-002 (Create Prescription)
  ↓
US-003 (Sign Prescription)
  ↓
US-004 (Send Prescription - QR)
  ↓
US-006 (Receive Prescription - QR)
  ↓
US-007 (View Details)
  ↓
US-008 (Share with Pharmacist - QR)
  ↓
US-010 (Verify Prescription) ← US-009 (Pharmacist Auth)
  ↓
US-011 (Dispense Items)
```

### Technical Dependencies
- US-003 requires revocation registry setup (infrastructure)
- US-010 requires trust registry implementation
- US-012/013/014 require dispensing data store
- US-017 extends US-002 (prescription schema)
- US-018 replaces/extends US-004, US-006, US-008 (QR flows)
- US-020 extends US-016 (audit trail)
- US-021 extends US-015 (revocation)
- US-022 extends US-012 (time validation)
- US-023 depends on US-005, US-006
- US-024 required by US-025 (monitoring needs K8s)

---

## Architecture Overview

### Adaptive SSI Infrastructure
```
┌─────────────────────────────────────────────────────┐
│              REACT NATIVE MOBILE APP                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   Doctor     │ │   Patient    │  │ Pharmacist  │ │
│  │  (Blue Theme)│ │ (Cyan Theme) │  │(Green Theme)│ │
│  └──────────────┘ └──────────────┘ └──────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
           ┌───────────▼───────────┐
           │   SSIProvider Adapter  │
           │  (Swappable Backend)   │
           └───────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌──────────────┐ ┌──────────┐ ┌──────────┐
  │ ACA-Py Local │ │   DIDx   │ │  Mock    │
  │  (Weeks 1-4) │ │(Week 5+) │ │(Testing) │
  └──────────────┘ └──────────┘ └──────────┘
```

### Technology Stack
- **Backend:** Python 3.12, FastAPI, PostgreSQL, Redis
- **Mobile:** React Native 0.72+, Expo SDK 49+, TypeScript 5.0+
- **SSI:** ACA-Py CloudAPI, DIDx CloudAPI (production)
- **Ledger:** cheqd testnet
- **Standards:** W3C Verifiable Credentials, FHIR R4, DIDComm v2
- **Auth:** OAuth 2.0 with PKCE
- **Infrastructure:** Docker Compose (dev), Kubernetes (prod)

---

## Implementation Plan Reference

### Week-by-Week Breakdown (from implementation-plan-v3.md)

**Week 0: Foundation Setup**
- Development environment setup
- Docker Compose infrastructure
- ACA-Py local deployment
- Project scaffolding

**Week 1: Backend API & SSI Adapter**
- FastAPI project structure
- Database models
- SSIProvider interface
- ACA-Py integration

**Week 2: Mobile App Core**
- React Native + Expo setup
- Themed component library
- Navigation structure
- API client

**Week 3: Core Features Implementation**
- US-001 through US-011 implementation
- QR code flows
- Wallet integration

**Week 4: MVP Completion & Polish**
- US-012 through US-016
- Integration testing
- Bug fixes
- Demo preparation

**Weeks 5-6: DIDx Migration**
- Contract finalization
- SSIProvider switch to DIDx
- Production configuration
- End-to-end testing

**Weeks 7-10: Enhanced Features**
- US-017 (FHIR R4)
- US-018 (DIDComm v2)
- US-019 through US-023

**Weeks 11-14: Production Hardening**
- US-024 (Kubernetes)
- US-025 (Monitoring)
- Security audit
- Performance optimization

---

## Key Design Decisions

### 1. QR Code vs DIDComm
**MVP (Weeks 1-4):** QR code flows (US-004, US-006, US-008)  
**Production (Week 7+):** DIDComm v2 messaging (US-018)  
**Rationale:** QR codes are simpler for MVP demo, DIDComm provides true peer-to-peer security with push notifications and offline delivery

**Important:** US-004, US-006, and US-008 describe simple QR code exchange (no DIDComm connections, no push notifications). US-018 describes the future DIDComm v2 replacement with full messaging infrastructure.

### 2. ACA-Py vs DIDx
**Development:** Local ACA-Py instance  
**Production:** DIDx CloudAPI  
**Migration:** Configuration-only switch via SSIProvider adapter  
**Rationale:** Start development immediately, migrate to production infrastructure later

### 3. Simplified vs Full FHIR
**MVP:** FHIR-inspired schema (10 fields)  
**Enhanced:** Full FHIR R4 MedicationRequest  
**Rationale:** Simpler for MVP, full compliance for production

### 4. Themed Mobile UI
**Doctor:** Royal Blue (#2563EB), clinical professional layout  
**Patient:** Cyan (#0891B2), mobile-first personal health  
**Pharmacist:** Green (#059669), workstation dispensing layout  
**Rationale:** Visual distinction helps users identify their role quickly

---

## Constraints & Simplifications

### For MVP Demo
- Mock medical registry (HPCSA/SAPC)
- Pre-populated test data
- QR codes instead of DIDComm
- Simplified FHIR schema
- Local ACA-Py instead of DIDx
- In-memory audit logs
- No real drug interaction checking

### For Production
- Real DIDx testnet/production APIs
- Full FHIR R4 compliance
- DIDComm v2 messaging
- Persistent audit trails
- Trust registry integration
- Revocation registry setup
- Performance optimization

---

## Regulatory Context

### South Africa Requirements
- **HPCSA:** Health Professions Council registration
- **SAPC:** South African Pharmacy Council registration
- **POPIA:** Data privacy compliance
- **Medicines Act:** Controlled substance regulations
- **ECTA:** Electronic signature validity

### Standards
- **W3C VC:** Verifiable Credentials Data Model 2.0
- **FHIR R4:** Fast Healthcare Interoperability Resources
- **DIDComm v2:** DID Communications Messaging
- **DID Core:** Decentralized Identifiers

---

## Agent Instructions

### When Adding New Stories
1. Use next available 3-digit number (currently 026+)
2. Follow the exact format template above
3. Include explicit "User Story" section with As/I want/so that format
4. Add to user-stories/README.md index table
5. Update AGENTS.md if new dependencies introduced
6. Run consistency check

### When Modifying Stories
1. Preserve existing numbering
2. Update related stories sections if cross-references change
3. Keep acceptance criteria testable and specific
4. Maintain estimation consistency
5. Update README index if titles change

### When Reviewing
1. Check all stories follow INVEST principles
2. Verify acceptance criteria are testable
3. Confirm API endpoints are plausible
4. Validate dependencies are accurate
5. Ensure no duplicates or gaps in numbering

---

## Last Updated
- **Date:** 2026-02-11
- **Version:** 1.1
- **Status:** Complete - 25 user stories, all standardized, QR vs DIDComm clarified
- **Next Review:** Before development kickoff
- **Changes in v1.1:**
  - Fixed US-004, US-006, US-008 to properly describe QR code flows
  - Removed DIDComm references from MVP stories
  - Clarified US-018 as future replacement for QR flows
  - Updated story points: US-004 (8→5), US-008 (8→5)

---

## Questions?

For technical questions, refer to:
- `implementation-plan-v3.md` for detailed timeline
- `user-stories/README.md` for story index
- Individual story files for specific requirements
