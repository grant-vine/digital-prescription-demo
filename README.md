# Digital Prescription Demo - Complete Project Package

## 📦 Package Contents

This package contains everything needed to build and deploy a digital prescription demo using DIDx's verifiable identity infrastructure.

---

## 🎉 Recent Updates

**2026-02-14**: Upgraded to Expo SDK 54
- ✅ Full app store compliance (iOS 26 SDK, Android API 35)
- ✅ Latest security patches and performance improvements
- ✅ Modern CameraView API for QR code scanning
- ✅ React Native 0.81 with React 19.1
- ✅ Zero breaking changes for end users

---

## 📋 Quick Navigation

### Plans (Choose Your Path)
1. **[Implementation Plan v3.0](/implementation-plan-v3.md)** ← **START HERE**
   - ✅ Themed UI (3 distinct roles)
   - ✅ Mobile-first (React Native + Expo)
   - ✅ Adaptive infrastructure (ACA-Py ↔ DIDx)
   - ✅ MacBook Air M1 8GB optimized
   - ✅ Contract-independent development

### User Stories (25 Total)

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
- **Momus Review Report** (incorporated into v3.0 plan)
  - 5 critical issues (all resolved in v3.0)
  - 12 major concerns
  - 13 minor suggestions
  - Full technical assessment

---

## 🚀 Quick Start (Automated)

**Just want to run the demo?** Use the automated startup script to initialize everything in one command:

### macOS / Linux
```bash
chmod +x scripts/start-demo.sh
./scripts/start-demo.sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-demo-windows.ps1
```

The script will:
1. ✅ Check prerequisites (Python 3.12+, Node.js 20+, Docker)
2. ✅ Start Docker infrastructure (PostgreSQL, Redis, ACA-Py)
3. ✅ Setup backend (venv, dependencies, migrations, seed data)
4. ✅ Setup mobile app (npm install)
5. ✅ Start backend API server (http://localhost:8000)
6. ✅ Start mobile app (Expo on port 8081)
7. ✅ Display demo credentials

**Demo Credentials** (automatically seeded):
- **Doctor**: `sarah.johnson@hospital.co.za` / `Demo@2024`
- **Patient**: `john.smith@example.com` / `Demo@2024`
- **Pharmacist**: `lisa.chen@pharmacy.co.za` / `Demo@2024`

> ℹ️ **First run takes 3-5 minutes** as it downloads Docker images and installs dependencies. Subsequent runs are much faster.

---

## 🎬 Investor Demo

Ready to impress investors? Generate a professional 3-panel demo video showing all three roles in action.

### Quick Start
```bash
./scripts/start-demo.sh
```
This single command sets up the entire demo environment with:
- PostgreSQL database with demo data
- Redis cache
- ACA-Py SSI infrastructure
- FastAPI backend (http://localhost:8000)
- React Native mobile app (http://localhost:8081)
- Pre-seeded demo credentials

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Doctor** | `sarah.johnson@hospital.co.za` | `Demo@2024` |
| **Patient** | `john.smith@example.com` | `Demo@2024` |
| **Pharmacist** | `lisa.chen@pharmacy.co.za` | `Demo@2024` |

### Video Demo

Generate a professional side-by-side demo video (3-panel layout):
```bash
cd apps/mobile
npm run demo:video
```

**Output:** `demo-investor-final.mp4` (in project root)
- **Duration:** 17.7 seconds
- **Format:** 3-panel side-by-side (Doctor, Patient, Pharmacist)
- **Resolution:** Professional demo quality
- **Ready to share** with investors

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
- React Native 0.81 + Expo SDK 54
- TypeScript 5.6
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

## 📋 Prerequisites

### Required Software
- **Python 3.12+** - Backend runtime
- **Node.js 20+** - Mobile app development
- **Docker Desktop** - Infrastructure (PostgreSQL, Redis, ACA-Py)
- **Git** - Version control

### Verify Installation
```bash
python --version  # Should show 3.11+
node --version    # Should show 20+
docker --version  # Should show 20+
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/grant-vine/digital-prescription-demo.git
cd digital-prescription-demo
```

### 2. Infrastructure Setup
Start the required databases and SSI infrastructure using Docker Compose:
```bash
docker-compose up -d db redis acapy
```

### 3. Backend Setup
```bash
cd services/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional: create .env file)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/prescriptions"
export REDIS_URL="redis://localhost:6379/0"
export ACAPY_ADMIN_URL="http://localhost:8001"
export SECRET_KEY="dev-secret-key-change-in-production"
```

### 4. Mobile App Setup
```bash
cd apps/mobile

# Install dependencies
npm install
```

---

## 🚀 Running Locally

### Start Backend
```bash
cd services/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Start Mobile App
```bash
cd apps/mobile
npx expo start
```
- Press **i** for iOS simulator (macOS only)
- Press **a** for Android emulator
- Scan QR code with **Expo Go** app on your physical device

### Infrastructure Logs
```bash
docker-compose logs -f acapy  # Follow ACA-Py logs
docker-compose logs -f db     # Follow PostgreSQL logs
```

---

## 🧪 Running Tests

### Backend Tests (pytest)
```bash
cd services/backend
source venv/bin/activate
pytest                              # Run all tests
pytest app/tests/test_audit.py      # Run specific test file
pytest --cov=app                    # Run with coverage report
```

### Mobile Tests (Jest)
```bash
cd apps/mobile
npm test                            # Run all unit and component tests
npm test -- src/components/qr       # Run tests in specific directory
```

### E2E Integration Tests
The mobile app includes E2E tests simulating full user flows:
```bash
cd apps/mobile
npm test -- e2e/doctor.spec.ts     # Test doctor workflow
npm test -- e2e/patient.spec.ts    # Test patient workflow
npm test -- e2e/pharmacist.spec.ts # Test pharmacist workflow
```

---

## 📊 Demo Data

### Seed Demo Data
Populate the system with realistic doctors, patients, and prescriptions:
```bash
cd services/backend
source venv/bin/activate
python scripts/seed_demo_data.py
```

**Default Demo Users:**
- **Doctor**: `sarah.johnson@hospital.co.za` / `Demo@2024`
- **Patient**: `john.smith@example.com` / `Demo@2024`
- **Pharmacist**: `lisa.chen@pharmacy.co.za` / `Demo@2024`

### Reset Demo Environment
Clear all data and optionally reseed via the admin API:
```bash
# Get auth token first (login as doctor)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sarah.johnson@hospital.co.za","password":"Demo@2024"}' \
  | jq -r '.access_token')

# Reset and reseed
curl -X POST "http://localhost:8000/api/v1/admin/reset-demo?confirm=true&reseed=true" \
  -H "Authorization: Bearer $TOKEN"
```

---


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

### Backend Issues

#### "Connection refused" when starting backend
- **Cause**: Database or Redis not running.
- **Solution**: Run `docker-compose up -d db redis`.

#### "ModuleNotFoundError: No module named 'app'"
- **Cause**: Not in backend directory or venv not activated.
- **Solution**:
  ```bash
  cd services/backend
  source venv/bin/activate
  pip install -r requirements.txt
  ```

### Mobile Issues

#### "Metro bundler not starting" or Port 8081 busy
- **Cause**: Port 8081 already in use by another process.
- **Solution**: `npx expo start --clear` or kill the process: `lsof -ti:8081 | xargs kill`.

#### "Expo Go cannot connect to computer"
- **Cause**: Phone and computer on different networks.
- **Solution**: Ensure your phone and computer are on the same Wi-Fi. If using a VPN or restrictive network, try tunnel mode: `npx expo start --tunnel`.

### Infrastructure (SSI/DID)

#### "DID not registered" or SSI errors
- **Cause**: ACA-Py is not healthy or hasn't finished auto-provisioning.
- **Solution**: Check logs: `docker-compose logs -f acapy`. Ensure `ACAPY_ADMIN_URL` is correctly set to `http://localhost:8001`.

### Hardware Optimization
If you experience high memory usage on a MacBook Air 8GB:
```bash
# Stop ACA-Py if not testing SSI features
docker-compose stop acapy

# Clear Docker cache
docker system prune

# Restart Docker Desktop if needed
```

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| `implementation-plan-v3.md` | **Main plan - start here** |
| `docs/plans/implementation-plan-v1.md` | Original plan (archived) |
| `docs/plans/implementation-plan-v2.md` | Previous version (archived) |
| `user-stories/README.md` | Index of all user stories |
| `user-stories/001-*.md` to `027-*.md` | Individual user stories |
| `docs/DEMO-TESTING.md` | Demo testing guide |
| `docs/testing/TEST_FIXES_REPORT.md` | Test fix documentation |
| `docs/testing/VERIFICATION_INVESTIGATION.md` | Verification investigation |
| `docs/reports/DIDX-COMPATIBILITY-REPORT.md` | DIDx compatibility report |
| `docs/archive/CHEQD_INTEGRATION_STATUS.md` | Cheqd integration (archived) |

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
- ✅ **25 comprehensive user stories**
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
**Last Updated:** 12 February 2026  
**Status:** ✅ Ready for Development
