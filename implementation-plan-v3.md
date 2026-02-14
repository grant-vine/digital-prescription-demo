# Digital Prescription Demo - Implementation Plan v3.0

## Major Updates in v3.0

✅ **Themed Role-Based UI** - Each role has distinct theme (colors, layout)  
✅ **Mobile-First React Native** - Single codebase for iOS/Android/Web  
✅ **Adaptive Infrastructure** - Swappable between local ACA-Py and DIDx CloudAPI  
✅ **Contract Timeline Accommodation** - Start with local ACA-Py, migrate to DIDx later  
✅ **Hardware-Optimized** - Runs on MacBook Air M1 8GB  
✅ **Future Roadmap Stories** - Full FHIR + DIDComm implementation plan  

---

## 1. UI/UX: Themed Role-Based Design

### Design Philosophy
Each role gets a distinct visual identity to feel like a separate app, while maintaining code reuse.

### Doctor App Theme: "Clinical Professional"
```
Primary Color: #2563EB (Royal Blue - trust, professionalism)
Secondary Color: #1E40AF (Deep Blue)
Accent Color: #10B981 (Emerald - success, go)
Background: #F8FAFC (Cool Gray 50)
Typography: Inter (clean, medical)
Layout: Dashboard-style, left sidebar navigation
Iconography: Rounded, friendly but professional

Key Visual Elements:
- Stethoscope icon in logo
- Medical cross motif
- Clean card-based layout
- Priority on quick prescription creation
- Statistics/overview cards
```

### Patient App Theme: "Personal Health"
```
Primary Color: #0891B2 (Cyan - calm, health, water)
Secondary Color: #0E7490 (Deep Cyan)
Accent Color: #F59E0B (Amber - warmth, attention)
Background: #F0FDFA (Cyan 50, very light)
Typography: Inter (consistent but can use lighter weights)
Layout: Mobile-first, bottom tab navigation
Iconography: Rounded, friendly, approachable

Key Visual Elements:
- Heart/health icon in logo
- Wallet/card metaphor for prescriptions
- Timeline view of medications
- Friendly, reassuring language
- Clear expiration warnings
```

### Pharmacist App Theme: "Clinical Dispensing"
```
Primary Color: #059669 (Green - pharmacy, go, safe)
Secondary Color: #047857 (Deep Green)
Accent Color: #DC2626 (Red - warnings, alerts)
Background: #F0FDF4 (Green 50)
Typography: Inter
Layout: Workstation-optimized, wide tables, keyboard shortcuts
Iconography: Precise, clear, functional

Key Visual Elements:
- Mortar and pestle icon in logo
- Verification badge prominently displayed
- Checklist/checkmark motifs
- Warning indicators for issues
- Focus on accuracy and safety
```

### Shared Components
While themes differ, these remain consistent:
- **Typography scale** (consistent sizing)
- **Spacing system** (4px grid)
- **Form components** (buttons, inputs)
- **QR code scanner UI**
- **Modal/dialog patterns**

### Technical Implementation
```typescript
// Theme configuration
const themes = {
  doctor: {
    colors: {
      primary: '#2563EB',
      secondary: '#1E40AF',
      accent: '#10B981',
      background: '#F8FAFC',
      // ... more colors
    },
    layout: 'dashboard',
    navigation: 'sidebar',
    iconSet: 'medical'
  },
  patient: {
    colors: {
      primary: '#0891B2',
      secondary: '#0E7490',
      accent: '#F59E0B',
      background: '#F0FDFA',
      // ... more colors
    },
    layout: 'mobile',
    navigation: 'bottom-tabs',
    iconSet: 'friendly'
  },
  pharmacist: {
    colors: {
      primary: '#059669',
      secondary: '#047857',
      accent: '#DC2626',
      background: '#F0FDF4',
      // ... more colors
    },
    layout: 'workstation',
    navigation: 'sidebar',
    iconSet: 'clinical'
  }
};

// Usage in components
const ThemeProvider = ({ role, children }) => {
  const theme = themes[role];
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
};
```

---

## 2. Mobile-First Architecture

### Technology: React Native with Expo

**Current Stack** (Updated 2026-02-14):
- Expo SDK 54 (React Native 0.81, React 19.1)
- TypeScript 5.6 with strict mode
- Expo Router v4 for file-based navigation
- Modern CameraView API for QR code scanning

**Why React Native:**
- ✅ Single codebase for iOS, Android, and Web
- ✅ Near-native performance
- ✅ Access to device features (camera for QR scanning)
- ✅ DIDx's Yoma mobile uses React Native (reference)
- ✅ Hot reload for rapid development
- ✅ Expo managed workflow for easier setup

**Why Expo:**
- ✅ Simplified build process
- ✅ OTA (over-the-air) updates
- ✅ QR code-based development
- ✅ Easy device testing
- ✅ Push notifications built-in
- ✅ Camera access for QR scanning
- ✅ App store compliance (iOS 26 SDK, Android API 35)

### Project Structure
```
digital-prescription-demo/
├── apps/
│   ├── mobile/                    # React Native + Expo
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (doctor)/      # Doctor role screens
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── dashboard.tsx
│   │   │   │   │   ├── prescriptions/
│   │   │   │   │   └── profile.tsx
│   │   │   │   ├── (patient)/     # Patient role screens
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── wallet.tsx
│   │   │   │   │   └── scan.tsx
│   │   │   │   ├── (pharmacist)/  # Pharmacist role screens
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── verify.tsx
│   │   │   │   │   └── dispense.tsx
│   │   │   │   └── index.tsx      # Role selector
│   │   │   ├── components/
│   │   │   │   ├── theme/
│   │   │   │   │   ├── DoctorTheme.tsx
│   │   │   │   │   ├── PatientTheme.tsx
│   │   │   │   │   └── PharmacistTheme.tsx
│   │   │   │   ├── qr/
│   │   │   │   │   ├── QRScanner.tsx
│   │   │   │   │   └── QRDisplay.tsx
│   │   │   │   └── common/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   │   ├── api.ts         # Backend API client
│   │   │   │   ├── acapy.ts       # ACA-Py/DIDx client
│   │   │   │   └── qr.ts          # QR code handling
│   │   │   └── store/
│   │   ├── app.json
│   │   └── package.json
│   └── web/                       # (Optional) Web-specific optimizations
├── backend/
│   └── src/
└── infrastructure/
```

### Mobile-Specific Features

**QR Code Scanning:**
```typescript
// Using expo-camera
import { CameraView, useCameraPermissions } from 'expo-camera';

export function QRScanner({ onScan }) {
  const [permission, requestPermission] = useCameraPermissions();
  
  const handleBarCodeScanned = ({ type, data }) => {
    onScan(data);
  };

  return (
    <CameraView
      style={{ flex: 1 }}
      facing="back"
      onBarcodeScanned={handleBarCodeScanned}
      barcodeScannerSettings={{
        barcodeTypes: ['qr'],
      }}
    />
  );
}
```

**Push Notifications:**
```typescript
// Using expo-notifications
import * as Notifications from 'expo-notifications';

// Patient receives prescription
async function notifyPrescriptionReceived(prescriptionId: string) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'New Prescription',
      body: 'Dr. Smith has sent you a prescription',
      data: { prescriptionId },
    },
    trigger: null, // Immediate
  });
}
```

**Offline Support (PWA):**
```typescript
// Using expo-offline and AsyncStorage
import AsyncStorage from '@react-native-async-storage/async-storage';

// Cache prescriptions for offline viewing
const cachePrescriptions = async (prescriptions) => {
  await AsyncStorage.setItem('cached_prescriptions', JSON.stringify(prescriptions));
};

const getCachedPrescriptions = async () => {
  const data = await AsyncStorage.getItem('cached_prescriptions');
  return data ? JSON.parse(data) : [];
};
```

### Responsive Design Strategy

While primarily mobile, layouts adapt:

**Doctor (Tablet/Desktop optimized):**
- Wide dashboard view
- Side-by-side prescription form and preview
- Keyboard-friendly inputs
- Multi-column layouts

**Patient (Mobile-first):**
- Single column
- Large touch targets
- Swipe gestures
- Bottom sheet modals

**Pharmacist (Tablet/Desktop optimized):**
- Workstation layout
- Wide tables for medications
- Split-screen (prescription | verification)
- Barcode scanner integration ready

---

## 3. Adaptive Infrastructure: Swappable Backend

### Architecture Goal
Switch between local ACA-Py and DIDx CloudAPI with minimal code changes (just configuration).

### Adapter Pattern Implementation

```typescript
// Backend adapter interface
interface SSIProvider {
  // Authentication
  authenticate(credentials: AuthCredentials): Promise<AuthToken>;
  refreshToken(token: string): Promise<AuthToken>;
  
  // DIDs
  createDID(): Promise<DID>;
  resolveDID(did: string): Promise<DIDDocument>;
  
  // Credentials
  issueCredential(credential: Credential): Promise<VerifiableCredential>;
  verifyCredential(vc: VerifiableCredential): Promise<VerificationResult>;
  revokeCredential(credentialId: string): Promise<void>;
  
  // Connections (for future DIDComm)
  createConnection(): Promise<Connection>;
  acceptConnection(connectionId: string): Promise<void>;
  sendMessage(connectionId: string, message: Message): Promise<void>;
  
  // Trust Registry
  queryTrustRegistry(did: string): Promise<TrustRegistryEntry>;
}

// ACA-Py Local Implementation
class ACAPyLocalProvider implements SSIProvider {
  private baseUrl: string;
  private apiKey: string;
  
  constructor(config: { baseUrl: string; apiKey: string }) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
  }
  
  async createDID(): Promise<DID> {
    const response = await fetch(`${this.baseUrl}/wallet/did/create`, {
      method: 'POST',
      headers: {
        'X-Api-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ method: 'key' })
    });
    return response.json();
  }
  
  // ... other implementations
}

// DIDx CloudAPI Implementation
class DIDxCloudProvider implements SSIProvider {
  private baseUrl: string;
  private accessToken: string;
  
  constructor(config: { baseUrl: string; accessToken: string }) {
    this.baseUrl = config.baseUrl;
    this.accessToken = config.accessToken;
  }
  
  async createDID(): Promise<DID> {
    const response = await fetch(`${this.baseUrl}/tenant/v1/dids`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }
  
  // ... other implementations
}

// Factory for creating the right provider
class SSIProviderFactory {
  static createProvider(config: AppConfig): SSIProvider {
    switch (config.provider) {
      case 'acapy-local':
        return new ACAPyLocalProvider(config.acapy);
      case 'didx-cloud':
        return new DIDxCloudProvider(config.didx);
      default:
        throw new Error(`Unknown provider: ${config.provider}`);
    }
  }
}

// Configuration
const config = {
  provider: process.env.SSI_PROVIDER || 'acapy-local', // 'acapy-local' or 'didx-cloud'
  
  acapy: {
    baseUrl: process.env.ACAPY_URL || 'http://localhost:8000',
    apiKey: process.env.ACAPY_API_KEY || 'admin-key'
  },
  
  didx: {
    baseUrl: process.env.DIDX_URL || 'https://cloudapi.test.didxtech.com',
    accessToken: process.env.DIDX_TOKEN
  }
};

// Usage
const ssiProvider = SSIProviderFactory.createProvider(config);
const did = await ssiProvider.createDID();
```

### Migration Path: Local ACA-Py → DIDx

**Phase 1: Development (Weeks 1-4)**
```bash
# Use local ACA-Py
SSI_PROVIDER=acapy-local
ACAPY_URL=http://localhost:8000
```

**Phase 2: Contract Signed → Migration (Week 5)**
```bash
# Switch to DIDx
SSI_PROVIDER=didx-cloud
DIDX_URL=https://cloudapi.test.didxtech.com
DIDX_TOKEN=your-oauth-token
```

**Migration Steps:**
1. ✅ Code changes: NONE (just config)
2. ✅ Data migration: Export local DIDs, re-create in DIDx
3. ✅ Testing: Run full test suite against DIDx
4. ✅ Deployment: Update environment variables

**Rollback Plan:**
If DIDx issues arise, switch back instantly:
```bash
SSI_PROVIDER=acapy-local
```

---

## 4. Local ACA-Py Setup (MacBook Air M1 8GB)

### Hardware Assessment: ✅ FEASIBLE

**MacBook Air M1 8GB can handle:**
- ✅ ACA-Py agent (lightweight when configured correctly)
- ✅ PostgreSQL database
- ✅ React Native development
- ⚠️ BUT: Need to run selectively, not all at once during development

**Memory Management Strategy:**
```
Total RAM: 8GB
Reserved for macOS: 2GB
Available for development: 6GB

ACA-Py (tuned): ~1GB
PostgreSQL: ~512MB
React Native Metro bundler: ~1GB
Backend API: ~512MB
VS Code: ~1GB
Browser tabs: ~1GB
Chrome/Safari for testing: ~1GB
-----------------------------------
Total: ~6GB (tight but manageable)
```

### ACA-Py Configuration for Low Memory

**Docker Compose (optimized):**
```yaml
# infrastructure/docker-compose.dev.yml
version: '3.8'

services:
  acapy:
    image: bcgovimages/aries-cloudagent:py36-1.16-1_0.8.0
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - ACAPY_ADMIN_INSECURE_MODE=true
      - ACAPY_ADMIN_API_KEY=admin-key
      - ACAPY_WEBHOOK_URL=http://backend:8000/webhooks
      # Performance optimizations for 8GB RAM
      - ACAPY_LOG_LEVEL=WARNING  # Reduce logging overhead
      - ACAPY_PRESERVE_EXCHANGE_RECORDS=false  # Don't keep history
      - ACAPY_AUTO_RESPOND_CREDENTIAL_OFFER=true
      - ACAPY_AUTO_RESPOND_CREDENTIAL_REQUEST=true
      - ACAPY_AUTO_VERIFY_PRESENTATION=true
    command: >
      start 
      --inbound-transport http 0.0.0.0 8000
      --outbound-transport http
      --admin 0.0.0.0 8001
      --wallet-type indy
      --wallet-name prescription_wallet
      --wallet-key secret_key
      --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/stable/sovrin/pool_transactions_builder_genesis
      --seed 00000000000000000000000000000001
      --storage-type indy
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    volumes:
      - acapy-data:/home/indy/.indy_client

  postgres:
    image: postgres:15-alpine  # Alpine is smaller
    environment:
      POSTGRES_USER: prescription
      POSTGRES_PASSWORD: prescription
      POSTGRES_DB: prescription_db
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  acapy-data:
  postgres-data:
```

**Start Infrastructure Selectively:**
```bash
# Option 1: Just database (for backend development)
docker-compose up postgres redis

# Option 2: Full stack (when testing SSI features)
docker-compose up

# Option 3: ACA-Py only (when developing mobile app against local API)
docker-compose up acapy postgres
```

### Local Development Workflow

**Daily Development (Memory Efficient):**
```bash
# Terminal 1: Database only
docker-compose up postgres redis

# Terminal 2: Backend API
npm run dev  # or python -m uvicorn main:app --reload

# Terminal 3: Mobile app
npx expo start
# Scan QR code with iPhone/Android
```

**Full Integration Testing:**
```bash
# Terminal 1: Full infrastructure
docker-compose up

# Terminal 2: Backend
npm run dev

# Terminal 3: Mobile
npx expo start
```

### Performance Monitoring

**Watch memory usage:**
```bash
# Check Docker stats
docker stats

# Check Mac Activity Monitor
# Keep free memory > 500MB at all times
```

**If memory runs low:**
```bash
# Stop unnecessary services
docker-compose stop acapy  # Keep just database

# Or restart Docker Desktop to clear cache

# Close unused browser tabs

# Quit unused apps
```

### Minimum Viable Infrastructure

For tightest memory constraint (just API development):
```yaml
# docker-compose.minimal.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: prescription
      POSTGRES_PASSWORD: prescription
      POSTGRES_DB: prescription_db
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 384M
    tmpfs:
      - /var/lib/postgresql/data  # In-memory, doesn't persist
```

Run with: `docker-compose -f docker-compose.minimal.yml up`

---

## 5. Revised Timeline (Accommodating Contracts)

### Week 0: Pre-Development (Contract Pending)
**Duration:** 1-3 weeks (until DIDx contract signed)
**Can Start Immediately:** ✅ YES

**Activities:**
1. **Setup Development Environment**
   - Install Docker, Node.js, Python
   - Clone repository
   - Setup local ACA-Py
   - Verify "Hello ACA-Py" works

2. **UI/UX Design**
   - Create wireframes for all 3 roles
   - Define theme specifications
   - Design component library
   - Create design system in Figma/Sketch

3. **Architecture Setup**
   - Implement SSIProvider adapter pattern
   - Setup ACA-Py local provider
   - Create stub DIDx provider (interface only)
   - Setup database schema

4. **Backend Foundation**
   - FastAPI project structure
   - Database models
   - Basic API endpoints (without SSI)
   - Authentication scaffolding

5. **Mobile App Setup**
   - Expo project initialization
   - Navigation setup (3 roles)
   - Theme system implementation
   - Component library setup

**Deliverables:**
- [ ] Development environment running on MacBook Air
- [ ] UI wireframes complete
- [ ] Backend API running locally
- [ ] Mobile app building successfully
- [ ] Local ACA-Py creating DIDs
- [ ] Git repository with initial commits

**Memory Usage This Week:**
- VS Code: 1GB
- Docker (postgres only): 384MB
- React Native: 1GB
- Chrome: 1GB
- **Total: ~3.5GB** ✅ Comfortable

---

### Weeks 1-4: MVP Development
**Timeline:** As previously planned
**Provider:** Local ACA-Py
**Goal:** Complete working demo

**Same as v2.0 plan, but with mobile app instead of web:**
- Week 1: Foundation + Mobile setup
- Week 2: Doctor flow
- Week 3: Patient flow
- Week 4: Pharmacist flow + Demo prep

**Deliverables:**
- [ ] Mobile app on iOS/Android
- [ ] Local ACA-Py integration complete
- [ ] Full demo working end-to-end

**Memory Management:**
- Run full infrastructure only during testing
- Use selective startup during development
- Monitor memory with `docker stats`

---

### Week 5: Contract Signed → DIDx Migration
**Duration:** 1 week
**Provider:** Switch from ACA-Py to DIDx

**Migration Tasks:**
1. **Obtain DIDx Credentials**
   - OAuth 2.0 client ID/secret
   - Test access

2. **Implement DIDx Provider**
   - Fill in stubbed DIDxCloudProvider
   - Implement all interface methods
   - Test each method

3. **Configuration Switch**
   ```bash
   SSI_PROVIDER=didx-cloud
   DIDX_TOKEN=your-token
   ```

4. **Data Migration**
   - Export local DIDs (JSON)
   - Re-create in DIDx
   - Update references
   - Test prescriptions

5. **Testing**
   - Run full test suite
   - Verify all features work
   - Performance testing

6. **Documentation**
   - Migration guide
   - Configuration reference
   - Troubleshooting

**Deliverables:**
- [ ] System running on DIDx CloudAPI
- [ ] Migration documentation
- [ ] Rollback plan tested

**Risk:**
- If DIDx integration issues arise, can roll back to ACA-Py instantly

---

### Week 6: Polish & Demo Prep
**Focus:** Performance, bug fixes, demo optimization
**Provider:** DIDx (or ACA-Py fallback)

**Activities:**
- UI polish
- Performance optimization
- Demo script refinement
- Test data creation
- Video recording

---

## 6. Future Roadmap: Full FHIR + DIDComm

### Phase 2: Enhanced Features (Weeks 7-10)

**Goal:** Add missing features for production readiness

**New User Stories:**

#### US-017: Full FHIR R4 Implementation
```markdown
## Title
Implement Full FHIR R4 MedicationRequest

## Description
Migrate from simplified prescription schema to full FHIR R4 MedicationRequest resource for healthcare interoperability.

## Acceptance Criteria
- [ ] Implement full FHIR R4 MedicationRequest schema (all fields)
- [ ] Support MedicationRequest resource relationships
- [ ] FHIR-compliant JSON serialization
- [ ] Validation against FHIR R4 specification
- [ ] Import/export FHIR bundles
- [ ] Backward compatibility with existing prescriptions

## Technical Notes
- Use fhir.resources library
- Implement FHIR search parameters
- Support _include and _revinclude
- FHIRPath expressions for validation
```

#### US-018: DIDComm v2 Messaging
```markdown
## Title
Implement DIDComm v2 for Prescription Exchange

## Description
Replace QR code flows with full DIDComm v2 peer-to-peer messaging for secure, automated prescription transmission.

## Acceptance Criteria
- [ ] Establish DIDComm connections (doctor→patient, patient→pharmacy)
- [ ] Send prescriptions via DIDComm issue-credential protocol
- [ ] Receive and process prescriptions automatically
- [ ] Send proof requests via DIDComm
- [ ] Receive and verify proof presentations
- [ ] Handle DIDComm mediator for offline messaging
- [ ] Encryption and signing per DIDComm spec

## Technical Notes
- Use didcomm-python library
- Implement DIDComm messaging service
- Handle out-of-band invitations
- Support mediator coordination
```

#### US-019: Prescription Repeats & Refills
```markdown
## Title
Support Prescription Repeats and Refills

## Description
Implement full repeat prescription workflow with interval tracking and dispensing history.

## Acceptance Criteria
- [ ] Track repeats remaining
- [ ] Enforce minimum interval between repeats
- [ ] Calculate next available repeat date
- [ ] Record dispensing history
- [ ] Alert patient when repeats exhausted
- [ ] Support partial fills
- [ ] Handle repeat authorization limits

## Notes
- Dependent on US-018 (DIDComm) for automated flow
- Can work with QR codes initially
```

#### US-020: Advanced Audit Trail
```markdown
## Title
Implement Comprehensive Audit Trail

## Description
Build complete audit logging system for regulatory compliance.

## Acceptance Criteria
- [ ] Log all prescription events (create, sign, send, verify, dispense, revoke)
- [ ] Immutable log storage
- [ ] Blockchain anchoring for critical events
- [ ] Audit log query interface
- [ ] Export to CSV/PDF
- [ ] Tamper-evident verification
- [ ] Retention policy (7 years)
```

#### US-021: Prescription Revocation
```markdown
## Title
Implement Prescription Revocation

## Description
Enable doctors to revoke prescriptions with proper notification and registry updates.

## Acceptance Criteria
- [ ] Doctor can revoke prescription with reason
- [ ] Revocation published to revocation registry
- [ ] Real-time revocation checking
- [ ] Patient notification of revocation
- [ ] Pharmacist sees revocation status
- [ ] Replacement prescription workflow
- [ ] Audit log of all revocations
```

#### US-022: Advanced Time-Based Validation
```markdown
## Title
Advanced Prescription Timing Controls

## Description
Implement sophisticated time-based validation including business hours, timezone handling, and emergency overrides.

## Acceptance Criteria
- [ ] Business hours validation (pharmacy operating hours)
- [ ] Timezone-aware expiration
- [ ] Emergency dispensing override workflow
- [ ] Schedule-based medication reminders
- [ ] Drug-specific timing rules
- [ ] Public holiday handling
```

#### US-023: Mobile Wallet Deep Integration
```markdown
## Title
Native Mobile Wallet Features

## Description
Leverage full mobile capabilities for enhanced user experience.

## Acceptance Criteria
- [ ] Push notifications for prescription events
- [ ] Biometric authentication (Face ID/Touch ID)
- [ ] Apple Wallet / Google Pay integration (optional)
- [ ] Offline mode with sync
- [ medication reminders with local notifications
- [ ] Camera integration for document scanning
- [ ] GPS for pharmacy location (optional)
```

---

### Phase 3: Production Scale (Weeks 11-14)

**Goal:** Production-ready deployment

**Stories:**

#### US-024: Kubernetes Deployment
```markdown
## Title
Kubernetes Production Deployment

## Description
Deploy to Kubernetes cluster with proper scaling, monitoring, and reliability.

## Acceptance Criteria
- [ ] Kubernetes manifests
- [ ] Helm charts
- [ ] Horizontal pod autoscaling
- [ ] Health checks and readiness probes
- [ ] ConfigMaps and Secrets management
- [ ] Ingress configuration
- [ ] SSL/TLS certificates (Let's Encrypt)
```

#### US-025: Monitoring & Alerting
```markdown
## Title
Production Monitoring and Observability

## Description
Implement comprehensive monitoring for production operations.

## Acceptance Criteria
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] Error tracking (Sentry)
- [ ] Log aggregation (ELK stack)
- [ ] Alerting rules (PagerDuty/Opsgenie)
- [ ] Performance monitoring
```

#### US-026: Security Hardening
```markdown
## Title
Security Audit and Hardening

## Description
Production security compliance and penetration testing.

## Acceptance Criteria
- [ ] Security audit by third party
- [ ] Penetration testing
- [ ] OWASP Top 10 compliance
- [ ] Data encryption at rest and in transit
- [ ] Key management (HSM integration)
- [ ] Vulnerability scanning
- [ ] Security documentation
```

#### US-027: Multi-Tenancy
```markdown
## Title
Multi-Tenant Architecture

## Description
Support multiple healthcare organizations on single deployment.

## Acceptance Criteria
- [ ] Tenant isolation
- [ ] Tenant-specific branding
- [ ] Tenant-specific trust registries
- [ ] Resource quotas per tenant
- [ ] Tenant admin interface
- [ ] Cross-tenant prescription sharing
```

---

## 7. Complete Story List

### MVP Stories (Weeks 1-4) - 11 stories
1. US-001: Doctor Authentication & DID Setup
2. US-002: Create Digital Prescription
3. US-003: Sign Prescription
4. US-005: Patient Wallet Setup
5. US-006: Receive Prescription (QR)
6. US-007: View Prescription
7. US-008: Share Prescription (QR)
8. US-009: Pharmacist Authentication
9. US-010: Verify Prescription
10. US-011: View Items for Dispensing
11. US-017: Demo Preparation & Test Data

### Enhanced Stories (Weeks 7-10) - 7 stories
12. US-018: DIDComm v2 Messaging
13. US-019: Prescription Repeats
14. US-020: Advanced Audit Trail
15. US-021: Revocation
16. US-022: Advanced Time Validation
17. US-023: Mobile Wallet Deep Integration
18. US-017-v2: Full FHIR R4 (extends US-017)

### Production Stories (Weeks 11-14) - 5 stories
19. US-024: Kubernetes Deployment
20. US-025: Monitoring & Alerting
21. US-026: Security Hardening
22. US-027: Multi-Tenancy

**Total: 23 stories**

---

## 8. Updated Success Criteria

### MVP (Week 4)
- [ ] Mobile app running on iOS and Android
- [ ] Themed UI (3 distinct visual identities)
- [ ] QR code flows working end-to-end
- [ ] Local ACA-Py integration complete
- [ ] Demo works entirely offline (no DIDx dependency)

### Post-Contract (Week 6)
- [ ] Migrated to DIDx CloudAPI
- [ ] Same features working on DIDx
- [ ] Configuration-only switch validated

### Full Implementation (Week 14)
- [ ] DIDComm messaging (not QR codes)
- [ ] Full FHIR R4 compliance
- [ ] Kubernetes deployment
- [ ] Production monitoring
- [ ] Security audit passed
- [ ] Multi-tenancy support

---

## 9. Risk Mitigation Updated

| Risk | Mitigation |
|------|------------|
| Contract delays | Start with ACA-Py immediately |
| MacBook Air memory | Selective service startup, monitoring |
| DIDx migration issues | Adapter pattern allows instant rollback |
| Mobile complexity | Expo simplifies development |
| UI/UX inconsistency | Shared component library with theme variations |
| Performance on M1 | Optimized Docker images, memory limits |

---

## 10. Immediate Next Steps

### Today:
1. ✅ Approve Plan v3.0
2. 📧 Contact DIDx about timeline (set expectations)
3. 💻 Setup MacBook Air development environment
4. 📱 Install Expo Go app on phone

### This Week (Pre-Contract):
1. Initialize React Native project with Expo
2. Setup Docker with ACA-Py (lightweight config)
3. Implement SSIProvider adapter pattern
4. Create themed UI component library
5. Build "Hello ACA-Py" integration
6. Wireframe all 3 role interfaces

### Next Week:
1. Begin Week 0 tasks (design, architecture)
2. Backend API scaffolding
3. Database setup
4. Mobile navigation structure

---

## 11. Demo Optimization & Productisation Milestone

**Branch:** `milestone/demo-opt-product`  
**Goal:** Implement post-MVP backend features with multi-tenancy baked in from the start, architecturally aligned with DIDx CloudAPI.

### Completed Phases

| Phase | User Story | Commit | Description | Tests Added |
|-------|-----------|--------|-------------|-------------|
| 0 | Multi-Tenancy Foundation | `8d061e7` | TenantMixin on all models, tenant_id in JWT, DIDx CloudAPI alignment | — |
| 1 | US-020: Advanced Audit Trail & Reporting | `85b16d2` | Hash-chain integrity, correlation tracking, compliance reports, dashboard | 27 |
| 2 | US-022: Advanced Time-Based Validation | `d878cc7` | Business hours, timezones, holidays, controlled substance timing, emergency overrides | 48 |
| 3 | US-021: Advanced Revocation Workflows | `ee9a3af` | Bulk revocation, scheduled revocation, rollback, impact analysis, rules engine | 30 |
| 4 | US-017-v2: Full FHIR R4 Implementation | `ea05f18` | MedicationRequest conversion, validation, search, Bundle support, dual-mode | 35 |
| 5 | US-019: Demo Preparation & Test Data | pending commit | Enhanced seed script, demo management API, 6 scenario-based demo datasets | 20 |

### Test Suite Progress

| After Phase | Tests Passed | Pre-existing Failures | Regressions |
|-------------|-------------|----------------------|-------------|
| Baseline (MVP) | 246 | 19 | — |
| + Phase 1 | 273 | 19 | 0 |
| + Phase 2 | 321 | 19 | 0 |
| + Phase 4 | 356 | 19 | 0 |
| + Phase 3 | 386 | 19 | 0 |
| + Phase 5 | 406 | 19 | 0 |

### Architecture Decisions

1. **Multi-tenancy aligned with DIDx CloudAPI** — `tenant_id` maps to DIDx `wallet_id`, `group_id` maps to DIDx group concept
2. **FHIR R4 dual-mode** — existing simplified schema preserved, FHIR conversion in service layer (no model changes)
3. **No new pip dependencies** — all features implemented with stdlib + existing deps
4. **Backward compatible** — all new parameters have defaults, no breaking API changes

### Remaining

- [ ] Final milestone tag: `v1.1.0-demo-opt`

---

**Plan Version:** 3.1  
**Status:** ✅ Ready for Development (Contract Independent)  
**Last Updated:** 12 February 2026  
**Hardware Target:** MacBook Air M1 8GB ✅  
**Changes in v3.1:** Added Section 11 — Demo Optimization & Productisation milestone tracking (Phases 0-5)
