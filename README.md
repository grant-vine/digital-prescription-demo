# Digital Prescription Demo - Complete Project Package

## 📦 Package Contents

This package contains everything needed to build and deploy a digital prescription demo using DIDx's verifiable identity infrastructure.

---

## 📋 Quick Navigation

### Plans (Choose Your Path)
1. **[Implementation Plan v3.0](/implementation-plan-v3.md)** ← **START HERE**
   - ✅ Themed UI (3 distinct roles)
   - ✅ Mobile-first (React Native + Expo)
   - ✅ Adaptive infrastructure (ACA-Py ↔ DIDx)
   - ✅ MacBook Air M1 8GB optimized
   - ✅ Contract-independent development

### User Stories (23 Total)

#### MVP Phase (Weeks 1-4) - 11 Stories
- **US-001:** Doctor Authentication & DID Setup
- **US-002:** Create Digital Prescription
- **US-003:** Sign Prescription with Digital Signature
- **US-005:** Patient Wallet Setup & Authentication
- **US-006:** Receive Prescription in Wallet (QR)
- **US-007:** View Prescription Details
- **US-008:** Share Prescription with Pharmacist (QR)
- **US-009:** Pharmacist Authentication & DID Setup
- **US-010:** Verify Prescription Authenticity
- **US-011:** View Prescription Items for Dispensing
- **US-017:** Demo Preparation & Test Data

#### Enhanced Phase (Weeks 7-10) - 7 Stories
- **US-017-v2:** Full FHIR R4 Implementation ← NEW
- **US-018:** DIDComm v2 Messaging ← NEW
- **US-019:** Support Prescription Repeats/Refills
- **US-020:** Comprehensive Audit Trail ← NEW
- **US-021:** Revoke or Cancel Prescription
- **US-022:** Advanced Time-Based Validation
- **US-023:** Mobile Wallet Deep Integration ← NEW

#### Production Phase (Weeks 11-14) - 5 Stories
- **US-024:** Kubernetes Deployment ← NEW
- **US-025:** Monitoring & Observability ← NEW
- **US-026:** Security Hardening
- **US-027:** Multi-Tenancy ← NEW

### Reviews
- **[Momus Review Report](/momus-review-report.md)**
  - 5 critical issues (all resolved in v3.0)
  - 12 major concerns
  - 13 minor suggestions
  - Full technical assessment

---

## 🎯 Recommended Approach

### Timeline Options

#### Option A: MVP Demo (Recommended) - 4 Weeks + 2 Weeks Migration
**Best for:** Quick demo to stakeholders, proof of concept, limited budget

**Weeks 1-4:** MVP Development
- 11 user stories
- Local ACA-Py (no DIDx dependency)
- QR code flows (simple)
- Themed mobile app (3 roles)
- Runs on MacBook Air M1 8GB

**Weeks 5-6:** Migration to DIDx
- Contract signed
- Switch to DIDx CloudAPI (config only)
- Same features, production infrastructure

**Total: 6 weeks to DIDx demo**

#### Option B: Full Implementation - 14 Weeks
**Best for:** Production-ready system, enterprise deployment

**Weeks 1-4:** MVP (as above)
**Weeks 5-6:** DIDx migration + polish
**Weeks 7-10:** Enhanced features (FHIR, DIDComm, repeats)
**Weeks 11-14:** Production hardening (K8s, monitoring, security)

**Total: 14 weeks to production**

---

## 🏗️ Architecture Highlights

### Adaptive Infrastructure
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

**Switch backends with one config change:**
```bash
# Local development
export SSI_PROVIDER=acapy-local

# Production with DIDx
export SSI_PROVIDER=didx-cloud
```

### Themed UI
Each role has distinct visual identity:

| Role | Primary Color | Theme | Layout |
|------|---------------|-------|--------|
| Doctor | Royal Blue (#2563EB) | Clinical Professional | Dashboard, Sidebar |
| Patient | Cyan (#0891B2) | Personal Health | Mobile-first, Bottom Tabs |
| Pharmacist | Green (#059669) | Clinical Dispensing | Workstation, Sidebar |

### Technology Stack

**Mobile App:**
- React Native + Expo
- TypeScript
- TailwindCSS (via NativeWind)
- Zustand (state management)
- React Navigation

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL
- Redis
- ACA-Py / DIDx CloudAPI

**Infrastructure:**
- Docker Compose (development)
- Kubernetes (production)
- Prometheus + Grafana (monitoring)

---

## 💻 Development Environment

### Hardware Requirements: MacBook Air M1 8GB ✅

**Optimized for your hardware:**
```yaml
# docker-compose.dev.yml (memory-optimized)
services:
  acapy:
    deploy:
      resources:
        limits:
          memory: 1G  # Optimized for 8GB RAM
  
  postgres:
    image: postgres:15-alpine  # Smaller footprint
    deploy:
      resources:
        limits:
          memory: 512M
```

**Memory Management:**
- Selective service startup during development
- Run only what you need
- Monitor with `docker stats`
- Keep 500MB+ free at all times

### Quick Start

```bash
# 1. Clone repository
git clone <your-repo>
cd digital-prescription-demo

# 2. Install dependencies
npm install
cd backend && pip install -r requirements.txt

# 3. Start infrastructure (lightweight)
docker-compose up postgres redis

# 4. Start backend
npm run dev

# 5. Start mobile app
npx expo start
# Scan QR code with Expo Go app
```

---

## 📱 Mobile Features

### Core Capabilities
- **QR Code Scanning:** Built-in camera integration
- **Push Notifications:** Prescription received alerts
- **Offline Mode:** Cached prescriptions for viewing
- **Biometric Auth:** Face ID / Touch ID support
- **Deep Linking:** Navigate directly to prescriptions

### Cross-Platform
- **iOS:** Native app via App Store (TestFlight for demo)
- **Android:** Native app via Play Store (Internal testing)
- **Web:** PWA (Progressive Web App) as fallback

### Screen Sizes
- **Doctor:** Optimized for tablet/desktop
- **Patient:** Mobile-first (smartphone)
- **Pharmacist:** Workstation (tablet/desktop)

---

## 🔧 Adaptive Infrastructure Details

### SSIProvider Interface
```typescript
interface SSIProvider {
  // DIDs
  createDID(): Promise<DID>;
  resolveDID(did: string): Promise<DIDDocument>;
  
  // Credentials
  issueCredential(credential: Credential): Promise<VC>;
  verifyCredential(vc: VC): Promise<VerificationResult>;
  revokeCredential(id: string): Promise<void>;
  
  // Connections (future DIDComm)
  createConnection(): Promise<Connection>;
  sendMessage(connectionId: string, message: Message): Promise<void>;
}
```

### Implementations
1. **ACAPyLocalProvider:** Direct ACA-Py HTTP API
2. **DIDxCloudProvider:** DIDx CloudAPI OAuth 2.0
3. **MockProvider:** Testing and development

### Migration Path
```bash
# Development
export SSI_PROVIDER=acapy-local
export ACAPY_URL=http://localhost:8000

# Production
export SSI_PROVIDER=didx-cloud
export DIDX_URL=https://cloudapi.test.didxtech.com
export DIDX_TOKEN=your-oauth-token
```

**Zero code changes required!**

---

## 📊 Future Roadmap

### Phase 2: Enhanced Features (Weeks 7-10)
- ✅ Full FHIR R4 compliance
- ✅ DIDComm v2 messaging (replace QR codes)
- ✅ Prescription repeats/refills
- ✅ Advanced audit trail
- ✅ Revocation workflows
- ✅ Native mobile features

### Phase 3: Production (Weeks 11-14)
- ✅ Kubernetes deployment
- ✅ Monitoring & alerting
- ✅ Security hardening
- ✅ Multi-tenancy
- ✅ Performance optimization

---

## ⚠️ Critical Prerequisites

### Before Development Starts

1. **✅ Decide Timeline**
   - 4-week MVP + 2-week migration?
   - Or 14-week full implementation?

2. **✅ Confirm Team**
   - 1-2 developers recommended
   - React Native + Python skills needed

3. **📧 Contact DIDx (Set Expectations)**
   ```
   To: hello@didx.co.za
   Subject: Partnership - Digital Prescription Demo
   
   We're building a demo using your infrastructure.
   Timeline: Start development immediately with ACA-Py,
   migrate to DIDx CloudAPI in ~4 weeks when contract signed.
   
   Questions:
   - Typical contract timeline?
   - Testnet availability?
   - Technical support during migration?
   ```

4. **✅ Setup MacBook Air**
   - Install Docker Desktop
   - Install Node.js 20
   - Install Python 3.12
   - Clone repo and run `docker-compose up`

---

## 📈 Success Metrics

### MVP (Week 4)
- [ ] App runs on iOS/Android
- [ ] 3 themed role interfaces
- [ ] QR code flow works end-to-end
- [ ] Local ACA-Py integration
- [ ] Demo ready (5-minute walkthrough)

### Post-Migration (Week 6)
- [ ] All features work on DIDx
- [ ] Configuration-only migration validated
- [ ] Demo on DIDx infrastructure

### Full Production (Week 14)
- [ ] Kubernetes deployment
- [ ] Full FHIR compliance
- [ ] DIDComm messaging
- [ ] Production monitoring
- [ ] Security audit passed

---

## 🆘 Troubleshooting

### MacBook Air Memory Issues
```bash
# If Docker uses too much memory
# 1. Stop unnecessary services
docker-compose stop acapy

# 2. Use minimal database only
docker-compose -f docker-compose.minimal.yml up postgres

# 3. Restart Docker Desktop
docker system prune

# 4. Close browser tabs
# 5. Quit unused apps
```

### DIDx Migration Issues
```bash
# Rollback to ACA-Py instantly
export SSI_PROVIDER=acapy-local
npm run dev
```

### Mobile App Won't Build
```bash
# Clear caches
npx expo start -c

# Or reset completely
rm -rf node_modules
npm install
npx expo start
```

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| `implementation-plan-v3.md` | **Main plan - start here** |
| `implementation-plan-v2.md` | Previous version (for reference) |
| `user-stories/README.md` | Index of all user stories |
| `user-stories/001-*.md` to `027-*.md` | Individual user stories |
| `momus-review-report.md` | Expert review and recommendations |
| `docs/architecture.md` | Detailed architecture (create as needed) |
| `docs/deployment.md` | Deployment guides (create as needed) |

---

## 🎬 Next Steps

### Today:
1. ✅ Read `implementation-plan-v3.md` completely
2. 📧 Email DIDx about timeline
3. 💻 Setup development environment
4. 📱 Install Expo Go on your phone

### This Week:
1. Initialize React Native project
2. Setup Docker with ACA-Py
3. Implement SSIProvider adapter
4. Create themed component library
5. Build "Hello ACA-Py" test

### Next Week:
1. Begin Week 1 tasks (foundation)
2. Backend API scaffolding
3. Mobile navigation structure
4. Database setup

---

## 📞 Support

### During Development
- **DIDx:** hello@didx.co.za (once contracted)
- **ACA-Py:** https://github.com/hyperledger/aries-cloudagent-python
- **React Native:** https://reactnative.dev/docs/getting-started
- **Expo:** https://docs.expo.dev

### Emergency Contacts
- Create GitHub issues for code problems
- Stack Overflow for general questions
- DIDx Discord/Slack (if available)

---

## 📝 License

- **Code:** Apache-2.0 (business-friendly)
- **Documentation:** CC BY 4.0

---

## 🎉 Summary

You now have:
- ✅ **23 comprehensive user stories**
- ✅ **3 detailed implementation plans** (v3.0 is current)
- ✅ **Expert review** (Momus) with all issues resolved
- ✅ **Mobile-first architecture** (React Native + Expo)
- ✅ **Adaptive infrastructure** (ACA-Py ↔ DIDx)
- ✅ **Themed UI** (3 distinct role experiences)
- ✅ **MacBook Air optimization** (8GB RAM)
- ✅ **Contract-independent development** (start immediately)

**Ready to start?** Begin with Week 0 tasks in `implementation-plan-v3.md`!

---

**Package Version:** 3.0  
**Last Updated:** 11 February 2026  
**Status:** ✅ Ready for Development
