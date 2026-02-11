# Digital Prescription System - User Stories

## Project Overview

This project implements a digital prescription system using Self-Sovereign Identity (SSI) infrastructure. The system enables doctors to create and digitally sign prescriptions, patients to receive and manage them in a digital wallet, and pharmacists to verify and dispense medications securely.

**Technology Stack:** Python/FastAPI (backend), React Native + Expo (mobile), ACA-Py/DIDx (SSI infrastructure)

## Architecture

The demo uses an **adaptive SSI infrastructure** with the following components:

- **Backend:** Python/FastAPI with SSIProvider adapter pattern
- **Mobile Apps:** React Native with themed role-based interfaces (Doctor/Blue, Patient/Cyan, Pharmacist/Green)
- **SSI Layer:** ACA-Py CloudAPI (local dev weeks 1-4) → DIDx CloudAPI (production week 5+)
- **Ledger:** cheqd testnet for DID registry
- **Standards:** W3C Verifiable Credentials, FHIR R4 (enhanced phase), DIDComm v2 (enhanced phase)

The SSIProvider adapter allows seamless switching between backends:
- **Development:** Local ACA-Py instance
- **Production:** DIDx CloudAPI
- **Testing:** MockProvider for isolated testing

## User Story Index

### MVP Phase (Weeks 1-4) - Core Workflow

| ID | Story | Actor | Priority | Estimation |
|----|-------|-------|----------|------------|
| 001 | Doctor Authentication & DID Setup | Doctor | High | 5 SP |
| 002 | Create Digital Prescription | Doctor | High | 8 SP |
| 003 | Sign Prescription with Digital Signature | Doctor | High | 5 SP |
| 004 | Send Prescription to Patient Wallet (QR) | Doctor | High | 5 SP |
| 005 | Patient Wallet Setup & Authentication | Patient | High | 5 SP |
| 006 | Receive Prescription in Wallet (QR) | Patient | High | 5 SP |
| 007 | View Prescription Details | Patient | High | 3 SP |
| 008 | Share Prescription with Pharmacist (QR) | Patient | High | 5 SP |
| 009 | Pharmacist Authentication & DID Setup | Pharmacist | High | 5 SP |
| 010 | Verify Prescription Authenticity | Pharmacist | High | 8 SP |
| 011 | View Prescription Items for Dispensing | Pharmacist | High | 5 SP |

### Core System (Weeks 3-4) - System Features

| ID | Story | Actor | Priority | Estimation |
|----|-------|-------|----------|------------|
| 012 | Time-Based Prescription Validation | System | High | 5 SP |
| 013 | Handle Prescription Expiration | System | Medium | 3 SP |
| 014 | Support Prescription Repeats/Refills | Doctor/Pharmacist | Medium | 8 SP |
| 015 | Revoke or Cancel Prescription | Doctor | Medium | 5 SP |
| 016 | Audit Trail & Compliance Logging | System | Medium | 5 SP |

### Enhanced Phase (Weeks 7-10) - Production Features

| ID | Story | Actor | Priority | Estimation |
|----|-------|-------|----------|------------|
| 017 | Full FHIR R4 Implementation | System | Medium | 13 SP |
| 018 | DIDComm v2 Messaging | System | Medium | 13 SP |
| 019 | Demo Preparation & Test Data | System | High | 5 SP |
| 020 | Advanced Audit Trail & Reporting | System | Low | 8 SP |
| 021 | Advanced Revocation Workflows | Doctor | Low | 5 SP |
| 022 | Advanced Time-Based Validation | System | Low | 5 SP |
| 023 | Mobile Wallet Deep Integration | Patient | Low | 13 SP |

### Production Phase (Weeks 11-14) - Operations

| ID | Story | Actor | Priority | Estimation |
|----|-------|-------|----------|------------|
| 024 | Kubernetes Deployment | System | Medium | 8 SP |
| 025 | Monitoring & Observability | System | Medium | 8 SP |

**Total Stories:** 25  
**Total Story Points:** 154 SP  
**Estimated Timeline:** 14 weeks (with 2-person team)

**Note:** Story points updated in v1.1 (US-004: 8→5 SP, US-008: 8→5 SP) due to QR code simplification.

## Story Dependencies

```
US-001 (Doctor Auth)
  ↓
US-002 (Create Prescription)
  ↓
US-003 (Sign Prescription)
  ↓
US-004 (Send Prescription)
  ↓
US-006 (Receive Prescription)
  ↓
US-007 (View Details)
  ↓
US-008 (Share with Pharmacist)
  ↓
US-010 (Verify Prescription) ← US-009 (Pharmacist Auth)
  ↓
US-011 (Dispense Items)
```

## INVEST Criteria Applied

All user stories follow INVEST principles:

- **Independent**: Each story delivers standalone value (though some have logical sequencing)
- **Negotiable**: Implementation details are flexible - stories describe *what*, not *how*
- **Valuable**: Each story delivers clear user or business value
- **Estimable**: Scope is well-defined with clear acceptance criteria
- **Small**: Stories are completable within 1-5 days (3-13 story points)
- **Testable**: Clear acceptance criteria with pass/fail conditions

## File Naming Convention

All user story files follow the pattern:
```
user-stories/###-descriptive-slug.md
```

Where:
- `###` = Zero-padded 3-digit number (001, 002, etc.)
- `descriptive-slug` = Lowercase, hyphen-separated description

## Tech Stack

- **Backend:** Python 3.12, FastAPI, PostgreSQL, Redis
- **Mobile:** React Native 0.72+, Expo SDK 49+, TypeScript 5.0+
- **SSI:** ACA-Py CloudAPI, DIDx CloudAPI (production)
- **Ledger:** cheqd testnet (DID registry)
- **Standards:** W3C Verifiable Credentials, FHIR R4, DIDComm v2
- **Auth:** OAuth 2.0 with PKCE
- **Infrastructure:** Docker Compose (dev), Kubernetes (prod)

## Test Environment

**Development (Weeks 1-4):**
- Local ACA-Py instance via Docker Compose
- Mock data and registries
- QR code flows for prescription exchange

**Production (Week 5+):**
- DIDx testnet APIs: `https://cloudapi.test.didxtech.com`
- OAuth 2.0 Client Credentials required
- No real patient data in demo mode

## Story Status Legend

- ✅ **Ready for Development** - Stories 001-016 (MVP)
- 📋 **Planned** - Stories 017-018, 024-025 (Enhanced/Production)
- 💡 **Idea** - Stories 019-023 (Need refinement)

## License

This project is open source under Apache-2.0 license.

---

**Last Updated:** 2026-02-11 (v1.1)  
**Changes in v1.1:**
- Fixed US-004, US-006, US-008 to describe QR code flows (removed DIDComm)
- Updated story points: US-004 (8→5 SP), US-008 (8→5 SP)
- Total story points: 158 → 154 SP
- Clarified US-018 as future DIDComm v2 replacement
