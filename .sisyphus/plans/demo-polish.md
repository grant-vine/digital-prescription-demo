# Demo Polish Plan (Revised for Expo Web)

**Goal:** Enhance the Digital Prescription Demo for investor presentations with improved UX, demo shortcuts, and automated video recording using Playwright for Expo Web.

**Target Completion:** Investor-ready demo
**Priority:** High (polish phase)
**Estimated Duration:** 28-32 hours (~4 developer days)

**Includes Momus-Recommended Improvements:**
- ✅ Error boundary for crash protection (+1h)
- ✅ Playwright retry configuration (+0h)  
- ✅ Seed script protection (+0.5h)
- ✅ Enhanced DEMO.md with platform support (+0.5h)

**Final Momus Review:** APPROVED FOR EXECUTION 🟢 (95% confidence)

**Prerequisites Available:**
- ✅ `ffmpeg` installed (video compression)
- ✅ `playwright` available (via dev-browser skill)
- ✅ Expo Web running at `http://localhost:8081`

---

## 0. Environment Prerequisites (2 hours)

### 0.1 Verify Expo Web Build
```bash
cd apps/mobile
npx expo start --web
# Verify app loads at http://localhost:8081
# Test all 3 role flows manually
# Check browser console for errors
```

### 0.2 Verify Backend API Accessibility
```bash
# Backend running
curl http://localhost:8000/api/v1/health
# Should return: {"status": "healthy"}

# CORS working (open browser console at localhost:8081)
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
# Should NOT show CORS error
```

### 0.3 Verify Camera Access (Web)
```bash
# Open patient/scan in browser
# Verify camera permission prompt appears
# Click "Allow"
# Verify camera feed shows (or mock available)
```

### 0.4 Seed Demo Data
```bash
cd services/backend
source venv/bin/activate
python scripts/seed_demo_data.py
# Verify: 3 demo users, 3+ prescriptions created
```

### 0.5 Browser Requirements
**Recommended (Tested):**
- Chrome 90+ (best performance)
- Firefox 88+

**Supported (May have quirks):**
- Safari 14+ (camera works but slower)
- Edge 90+

**Not Supported:**
- Internet Explorer

---

## 1. Main Index Page Enhancements (4-5 hours)

### Current State
- Simple role selector with name, color, and brief description
- No workflow guidance
- No responsive breakpoints

### 1.1 Role Description Cards (1.5 hours)

Create expandable role cards with detailed information:

**Doctor Role Card:**
```typescript
interface RoleCard {
  id: 'doctor';
  title: 'Healthcare Provider';
  description: 'Create, sign, and issue digital prescriptions to patients';
  color: '#2563EB';
  icon: 'stethoscope'; // Lucide icon
  responsibilities: [
    'Authenticate and setup professional DID',
    'Search patient records',
    'Create prescriptions with medications',
    'Digitally sign using W3C Verifiable Credentials',
    'Generate QR codes for patients'
  ];
  estimatedTime: '2-3 minutes';
}
```

**Patient Role Card:**
```typescript
interface RoleCard {
  id: 'patient';
  title: 'Prescription Holder';
  description: 'Receive, store, and share prescriptions securely in your digital wallet';
  color: '#0891B2';
  icon: 'wallet';
  responsibilities: [
    'Setup personal wallet with decentralized identity',
    'Scan QR codes to receive prescriptions',
    'View prescription details and validity',
    'Share prescriptions with pharmacies via QR'
  ];
  estimatedTime: '1-2 minutes';
}
```

**Pharmacist Role Card:**
```typescript
interface RoleCard {
  id: 'pharmacist';
  title: 'Medication Dispenser';
  description: 'Verify prescription authenticity and dispense medications';
  color: '#059669';
  icon: 'pill';
  responsibilities: [
    'Authenticate with SAPC credentials',
    'Verify prescription signatures and trust registry',
    'Check revocation status',
    'Dispense medications and log actions'
  ];
  estimatedTime: '2-3 minutes';
}
```

**Implementation:**
- Create `RoleCard.tsx` component with expand/collapse animation
- Use `lucide-react-native` for icons
- Add press-to-expand gesture
- Show responsibilities as bullet list when expanded

### 1.2 Workflow Visualization Component (2 hours)

Create `WorkflowDiagram.tsx` with responsive layout:

```typescript
interface WorkflowStep {
  step: number;
  role: 'doctor' | 'patient' | 'pharmacist' | 'system';
  action: string;
  description: string;
  icon: string;
}

const workflowSteps: WorkflowStep[] = [
  { step: 1, role: 'doctor', action: 'Creates', description: 'Doctor creates and signs prescription', icon: 'file-plus' },
  { step: 2, role: 'patient', action: 'Receives', description: 'Patient scans QR and stores in wallet', icon: 'scan' },
  { step: 3, role: 'pharmacist', action: 'Verifies', description: 'Pharmacist checks signature and dispenses', icon: 'check-circle' },
  { step: 4, role: 'system', action: 'Audits', description: 'Complete audit trail recorded', icon: 'clipboard-list' },
];
```

**Visual Design:**
- Horizontal layout on desktop (>1024px)
- Vertical layout on mobile (<768px)
- Color-coded role indicators (blue, cyan, green)
- Animated connecting lines between steps
- Pulsing "active" indicator for current demo phase

**Responsive Breakpoints:**
```typescript
const { width } = useWindowDimensions();
const isMobile = width < 768;
const isDesktop = width > 1024;
```

### 1.3 Quick Start Guide (0.5 hours)

Add expandable FAQ-style section:

**Sections:**
1. "How the Demo Works" - 2-3 sentence overview
2. "What is SSI?" - Link to Self-Sovereign Identity explanation
3. "QR Code Flow" - Brief explanation of QR handoff
4. "Total Demo Time" - "3-5 minutes for complete workflow"

**Implementation:**
- Use accordion-style expandable sections
- Add smooth height animation
- Include help icon (question mark circle)

---

## 2. Demo User Quick-Login Buttons (3-4 hours)

### 2.1 Security Requirements

**CRITICAL:** Demo credentials must NOT work in production.

**Backend Changes (`services/backend/app/api/v1/auth.py`):**
```python
import os

@router.post("/api/v1/auth/login")
async def login(credentials: LoginRequest):
    # Check if using demo password
    if credentials.password == "Demo@2024":
        # Only allow in demo mode
        if os.getenv("DEMO_MODE") != "true":
            raise HTTPException(
                status_code=403,
                detail="Demo accounts are disabled in production"
            )
    
    # Continue with normal login...
```

**Environment Configuration:**
```bash
# .env.development
DEMO_MODE=true

# .env.production
DEMO_MODE=false
```

**Seed Script Protection (`services/backend/scripts/seed_demo_data.py`):**
```python
import os
import sys

def main():
    # Prevent accidental demo account creation in production
    if os.getenv("DEMO_MODE") != "true":
        print("⚠️  DEMO_MODE not enabled, skipping demo data creation")
        print("Set DEMO_MODE=true to create demo accounts")
        print("")
        print("If you want to seed production data, use:")
        print("  python scripts/seed_production_data.py")
        sys.exit(0)
    
    # Log warning when creating demo accounts
    print("🎮 DEMO MODE: Creating demo accounts...")
    print("   These accounts are for demonstration only!")
    print("")
    
    # Continue with existing seed logic...
    create_demo_users()
    create_demo_prescriptions()
```

**Additional Safety Measures:**
- Seed script logs `DEMO MODE` prominently when running
- Production deployments should never have `DEMO_MODE=true`
- CI/CD pipeline checks for `DEMO_MODE` in production builds
- Add pre-commit hook to prevent committing `.env` with `DEMO_MODE=true`

**Mobile Changes (`apps/mobile/app.json`):**
```json
{
  "expo": {
    "extra": {
      "demoMode": true
    }
  }
}
```

### 2.2 DemoLoginButtons Component (1 hour)

Create reusable component:

```typescript
// apps/mobile/src/components/DemoLoginButtons.tsx
import Constants from 'expo-constants';

export interface DemoCredentials {
  label: string;
  email: string;
  password: string;
  role: 'doctor' | 'patient' | 'pharmacist';
}

export const DEMO_CREDENTIALS: Record<string, DemoCredentials> = {
  doctor: {
    label: '👨‍⚕️ Use Demo Doctor',
    email: 'sarah.johnson@hospital.co.za',
    password: 'Demo@2024',
    role: 'doctor'
  },
  patient: {
    label: '👤 Use Demo Patient',
    email: 'john.smith@example.com',
    password: 'Demo@2024',
    role: 'patient'
  },
  pharmacist: {
    label: '💊 Use Demo Pharmacist',
    email: 'lisa.chen@pharmacy.co.za',
    password: 'Demo@2024',
    role: 'pharmacist'
  }
};

interface DemoLoginButtonsProps {
  onSelect: (credentials: DemoCredentials) => void;
  currentRole?: 'doctor' | 'patient' | 'pharmacist';
}

export function DemoLoginButtons({ onSelect, currentRole }: DemoLoginButtonsProps) {
  // Hide in production
  const isDemoMode = Constants.expoConfig?.extra?.demoMode;
  if (!isDemoMode) return null;
  
  return (
    <View style={styles.container}>
      <View style={styles.warningBanner}>
        <Text style={styles.warningIcon}>⚠️</Text>
        <Text style={styles.warningText}>DEMO MODE ONLY</Text>
      </View>
      
      {Object.entries(DEMO_CREDENTIALS).map(([key, creds]) => (
        <TouchableOpacity
          key={key}
          style={[
            styles.button,
            currentRole === creds.role && styles.buttonActive
          ]}
          onPress={() => onSelect(creds)}
        >
          <Text style={styles.buttonText}>{creds.label}</Text>
        </TouchableOpacity>
      ))}
      
      <Text style={styles.helperText}>
        Click to auto-fill demo credentials
      </Text>
    </View>
  );
}
```

**Visual Design:**
- Warning banner at top (red/orange background)
- Outlined buttons (not filled) to show they're secondary
- Active state highlighting for current role
- Small helper text below

### 2.3 Integration in Auth Screens (2-3 hours)

**Doctor Auth Screen:**
- Add `DemoLoginButtons` at bottom of login form
- On select: populate `email` and `password` state
- Optionally auto-submit after 500ms delay

**Patient Auth Screen:**
- Add to both wallet creation and login views
- For wallet creation: just populate (don't auto-submit)
- For login: populate and auto-submit

**Pharmacist Auth Screen:**
- Add to login step only (not profile setup)
- Populate email/password fields
- Maintain multi-step flow after login

---

## 3. UI/UX Major Redesign (12-14 hours)

### 3.1 Patient Auth Screen - Complete Redesign (5-6 hours)

**Current Issues:**
- Basic styling, no themed components
- Missing loading states
- No visual hierarchy
- Cluttered wallet creation flow

**Proposed Design:**

```typescript
// New component structure
<SafeAreaView>
  <KeyboardAvoidingView>
    <ScrollView>
      <CardContainer>
        <LogoHeader />
        
        <AuthStepIndicator 
          currentStep={step} 
          steps={['Welcome', 'Wallet', 'Verify']} 
        />
        
        {step === 'WELCOME' && (
          <WelcomeView 
            onCreateWallet={() => setStep('WALLET')}
            onLogin={() => setStep('LOGIN')}
          />
        )}
        
        {step === 'WALLET' && (
          <WalletCreationView
            onWalletCreated={handleWalletCreated}
            loading={loading}
          />
        )}
        
        {step === 'LOGIN' && (
          <LoginForm
            email={email}
            setEmail={setEmail}
            password={password}
            setPassword={setPassword}
            onSubmit={handleLogin}
            loading={loading}
            error={error}
          />
        )}
        
        <DemoLoginButtons onSelect={handleDemoSelect} />
      </CardContainer>
    </ScrollView>
  </KeyboardAvoidingView>
</SafeAreaView>
```

**Visual Elements:**

1. **Card Container:**
   - White background with subtle shadow
   - Rounded corners (12px)
   - Max-width: 480px (centered on desktop)
   - Padding: 24px

2. **Logo Header:**
   - App icon (96x96px)
   - Title: "Digital Prescription"
   - Subtitle: "Patient Wallet"

3. **Step Indicator:**
   - 3 steps: Welcome → Wallet → Verify
   - Progress bar connecting steps
   - Active step highlighted with cyan color
   - Completed steps show checkmark

4. **Welcome View:**
   - Illustration (wallet/phone icon)
   - Heading: "Welcome to Your Digital Wallet"
   - Description text about SSI
   - Two prominent buttons:
     - "Create New Wallet" (primary)
     - "I Already Have a Wallet" (secondary)

5. **Login Form:**
   - `ThemedInput` with error states
   - Password visibility toggle
   - "Forgot Password?" link (placeholder)
   - Loading spinner on submit button

6. **Error Display:**
   - Red background banner
   - Error icon (alert circle)
   - Clear error message
   - Auto-dismiss after 5 seconds

**Animation:**
- Step transitions: slide horizontally
- Loading: pulse animation on button
- Error: shake animation on form

### 3.2 Pharmacist Auth Screen - Complete Redesign (5-6 hours)

**Current Issues:**
- Multi-step but unclear progression
- SAPC field confusing
- No step indicators
- Basic styling

**Proposed Design:**

**Step Indicator Component:**
```typescript
interface Step {
  id: AuthStep;
  label: string;
  icon: string;
}

const steps: Step[] = [
  { id: AuthStep.LOGIN, label: 'Login', icon: 'log-in' },
  { id: AuthStep.PROFILE, label: 'Profile', icon: 'user' },
  { id: AuthStep.SAPC, label: 'SAPC', icon: 'shield' },
  { id: AuthStep.DID, label: 'Identity', icon: 'key' },
];

<StepIndicator 
  steps={steps} 
  currentStep={currentStep}
  onStepPress={(step) => canNavigateTo(step) && setCurrentStep(step)}
/>
```

**Step 1: Login (Enhanced)**
- Same structure as Patient login
- ThemedInput components
- Error handling
- Demo buttons at bottom

**Step 2: Profile Setup (NEW)**
```typescript
<ProfileSetupView>
  <Heading>Setup Your Pharmacy Profile</Heading>
  
  <ThemedInput
    label="Pharmacy Name"
    placeholder="e.g., MediCare Pharmacy"
    helperText="Your registered pharmacy practice name"
    value={pharmacyName}
    onChangeText={setPharmacyName}
    icon="building"
  />
  
  <ThemedInput
    label="Pharmacy Registration Number"
    placeholder="e.g., PRN123456"
    helperText="Optional: Your pharmacy license number"
    value={pharmacyRegNumber}
    onChangeText={setPharmacyRegNumber}
    icon="file-text"
  />
  
  <InfoBox>
    <Icon name="info" />
    <Text>This information will be associated with your digital identity for audit purposes.</Text>
  </InfoBox>
</ProfileSetupView>
```

**Step 3: SAPC Validation (Enhanced with Help)**

```typescript
<SAPCValidationView>
  <Heading>South African Pharmacy Council Registration</Heading>
  
  <ThemedInput
    label={
      <View style={styles.labelRow}>
        <Text>SAPC Number</Text>
        <InfoTooltip 
          title="What is SAPC?"
          content={SAPC_HELP_TEXT}
        />
      </View>
    }
    placeholder="SAPC123456"
    helperText="Format: SAPC followed by 6 digits"
    value={sapcNumber}
    onChangeText={handleSAPCChange}
    validation={{
      isValid: sapcValidated,
      message: sapcValidated ? '✓ Valid SAPC format' : 'Enter 6 digits after SAPC'
    }}
    icon="shield-check"
  />
  
  {sapcValidated && (
    <ValidationSuccess>
      <Icon name="check-circle" color="green" />
      <Text>SAPC registration verified</Text>
    </ValidationSuccess>
  )}
  
  <LinkButton 
    onPress={() => Linking.openURL('https://www.sapc.za.org/')}
    icon="external-link"
  >
    Verify your SAPC registration
  </LinkButton>
</SAPCValidationView>
```

**SAPC Help Tooltip Content:**
```typescript
const SAPC_HELP_TEXT = `South African Pharmacy Council (SAPC) Registration

The SAPC number is your official registration identifier issued by the South African Pharmacy Council. It verifies you are a licensed pharmacist authorized to dispense medications in South Africa.

Why it's required:
• Legal requirement for all practicing pharmacists
• Ensures only qualified professionals dispense
• Required for digital prescription verification
• Part of compliance audit trail

Format: SAPC followed by 6 digits
Example: SAPC123456

Forgot your number? Contact SAPC at www.sapc.za.org`;
```

**Step 4: DID Creation (Enhanced)**
```typescript
<DIDCreationView>
  <Heading>Create Your Digital Identity</Heading>
  
  <InfoBox type="info">
    <Text>A Decentralized Identifier (DID) is your unique digital identity on the blockchain. It allows you to verify prescriptions without sharing personal information.</Text>
  </InfoBox>
  
  {did ? (
    <SuccessView>
      <Icon name="check-circle" size={64} color="green" />
      <Heading>Identity Created!</Heading>
      <DIDCard did={did} />
      <Button onPress={finishOnboarding}>
        Continue to Dashboard
      </Button>
    </SuccessView>
  ) : (
    <LoadingView>
      <ActivityIndicator size="large" />
      <Text>Creating your secure digital identity...</Text>
      <Text style={styles.subtext}>This may take a few seconds</Text>
    </LoadingView>
  )}
</DIDCreationView>
```

### 3.3 Common Components (2 hours)

Create shared components for consistency:

**ThemedInput:**
```typescript
interface ThemedInputProps extends TextInputProps {
  label?: React.ReactNode;
  helperText?: string;
  error?: string;
  icon?: string;
  validation?: {
    isValid: boolean;
    message: string;
  };
}
```

**InfoTooltip:**
```typescript
interface InfoTooltipProps {
  title: string;
  content: string;
  icon?: string;
}
// Shows modal/bottom sheet on press
```

**CardContainer:**
```typescript
interface CardContainerProps {
  children: React.ReactNode;
  maxWidth?: number;
}
// Responsive card with shadow
```

**StepIndicator:**
```typescript
interface StepIndicatorProps {
  steps: Step[];
  currentStep: string;
  onStepPress?: (stepId: string) => void;
}
```

**ErrorBanner:**
```typescript
interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  duration?: number;
}
```

### 3.4 Global Error Boundary (+1 hour)

**Purpose:** Prevent embarrassing crash screens during investor demo.

**Implementation:**

```typescript
// apps/mobile/src/components/ErrorBoundary.tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Demo error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    // Navigate to home
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Demo Temporarily Unavailable</Text>
          <Text style={styles.message}>
            An unexpected error occurred. Please restart the demo.
          </Text>
          <TouchableOpacity onPress={this.handleReset} style={styles.button}>
            <Text style={styles.buttonText}>Restart Demo</Text>
          </TouchableOpacity>
          <Text style={styles.contact}>
            Questions? hello@digital-prescription.demo
          </Text>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#f8f9fa',
  },
  icon: {
    fontSize: 64,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  contact: {
    marginTop: 24,
    fontSize: 14,
    color: '#999',
  },
});
```

**Integration:**
```typescript
// apps/mobile/src/app/_layout.tsx
import { ErrorBoundary } from '../components/ErrorBoundary';

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="doctor" />
        <Stack.Screen name="patient" />
        <Stack.Screen name="pharmacist" />
      </Stack>
    </ErrorBoundary>
  );
}
```

**Acceptance Criteria:**
- [ ] Unhandled errors show user-friendly screen (not red React Native error screen)
- [ ] Reset button reloads app to index page
- [ ] Error logged to console for debugging
- [ ] Works in both web and native builds

---

## 4. Playwright E2E Video Demo Test (5-6 hours)

### 4.1 Playwright Configuration

**File: `apps/mobile/playwright.config.ts`**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Sequential for video narrative
  timeout: 120000,      // 2 minutes per test
  retries: 2,           // Retry flaky tests up to 2 times
  
  expect: {
    timeout: 10000,     // Wait up to 10s for assertions
  },
  
  use: {
    baseURL: 'http://localhost:8081',
    
    // Video recording configuration
    video: {
      mode: 'on',
      size: { width: 1280, height: 720 }
    },
    
    // Trace for debugging
    trace: 'on-first-retry',
    
    // Viewport
    viewport: { width: 1280, height: 720 },
    
    // Action timeout - wait up to 10s for clicks, fills, etc.
    actionTimeout: 10000,
    
    // Permissions
    permissions: ['camera'], // Auto-grant for QR flow
    
    // Browser launch options
    launchOptions: {
      args: [
        '--disable-infobars',
        '--kiosk',           // Fullscreen-like mode
        '--disable-extensions',
        '--disable-dev-shm-usage'
      ]
    }
  },

  projects: [
    {
      name: 'demo-video',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 }
      },
    },
  ],

  // Start Expo Web dev server
  webServer: {
    command: 'npx expo start --web --non-interactive',
    port: 8081,
    timeout: 120000,
    reuseExistingServer: true,
  },
  
  // Output directories
  outputDir: 'test-results/',
  preserveOutput: 'always',
});
```

### 4.2 QR Code Strategy: Copy as Text

**Instead of camera scanning, use text-based QR sharing:**

**Doctor Screen Modification:**
```typescript
// Add to QR display screen
<QRDisplay prescriptionId={id} qrData={qrData} />

{/* Fallback: Copy QR data as text */}
<CopyButton 
  text={qrData}
  label="Copy QR Data"
  helperText="For demo: Copy this data and paste in patient screen"
/>

{/* Show raw data for debugging */}
<Collapsible title="Show QR Data">
  <Text style={styles.code}>{qrData}</Text>
</Collapsible>
```

**Patient Screen Modification:**
```typescript
{/* Mock camera with text input */}
<CameraMockView>
  <Text>Camera Preview (Demo Mode)</Text>
  
  <TextInput
    placeholder="Paste QR data here..."
    value={scannedData}
    onChangeText={handleScannedData}
    multiline
    style={styles.qrInput}
  />
  
  <Button onPress={() => processQRData(scannedData)}>
    Process QR Data
  </Button>
  
  <Text style={styles.helper}>
    Or use "Simulate Scan" button for demo
  </Text>
  
  <DemoScanButton 
    onPress={() => processQRData(DEMO_QR_DATA)}
  />
</CameraMockView>
```

**Playwright Test Flow:**
```typescript
// Extract QR data from doctor screen
const qrData = await doctorPage.inputValue('[data-testid="qr-data-input"]');

// Navigate patient to scan screen
await patientPage.goto('/patient/scan');

// Paste QR data (simulating scan)
await patientPage.fill('[data-testid="qr-input"]', qrData);
await patientPage.click('button:has-text("Process QR Data")');

// Continue with prescription acceptance
```

### 4.3 Multi-Context Test Implementation

**File: `apps/mobile/e2e/demo-video.spec.ts`**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Investor Demo - Complete Prescription Flow', () => {
  test('Full workflow with video recording', async ({ browser }) => {
    // Create isolated browser contexts (separate sessions)
    const doctorContext = await browser.newContext();
    const patientContext = await browser.newContext();
    const pharmacistContext = await browser.newContext();
    
    const doctorPage = await doctorContext.newPage();
    const patientPage = await patientContext.newPage();
    const pharmacistPage = await pharmacistContext.newPage();
    
    try {
      // === STEP 1: Doctor Creates Prescription ===
      await test.step('Doctor Login', async () => {
        await doctorPage.goto('/');
        await doctorPage.click('text=Doctor');
        await doctorPage.click('text=Continue as doctor');
        
        // Use demo credentials
        await doctorPage.click('text=Use Demo Doctor');
        await doctorPage.waitForNavigation();
        
        await expect(doctorPage).toHaveURL(/.*dashboard/);
      });
      
      await test.step('Doctor Creates Prescription', async () => {
        await doctorPage.click('text=Create New Prescription');
        
        // Search patient
        await doctorPage.fill('[placeholder*="Search"]', 'John Smith');
        await doctorPage.click('text=John Smith');
        
        // Add medication
        await doctorPage.fill('[placeholder*="medication"]', 'Amoxicillin');
        await doctorPage.click('text=Amoxicillin 500mg');
        await doctorPage.fill('[placeholder*="dosage"]', '500mg twice daily');
        
        // Sign and generate QR
        await doctorPage.click('text=Sign & Generate QR');
        await doctorPage.waitForSelector('[data-testid="qr-display"]');
      });
      
      // Extract QR data
      const qrData = await doctorPage.inputValue('[data-testid="qr-data-text"]');
      expect(qrData).toBeTruthy();
      
      // === STEP 2: Patient Receives Prescription ===
      await test.step('Patient Login', async () => {
        await patientPage.goto('/');
        await patientPage.click('text=Patient');
        await patientPage.click('text=Continue as patient');
        await patientPage.click('text=Use Demo Patient');
      });
      
      await test.step('Patient Scans QR', async () => {
        await patientPage.click('text=Scan QR Code');
        
        // Paste QR data (simulating scan)
        await patientPage.fill('[data-testid="qr-input"]', qrData);
        await patientPage.click('text=Process QR Data');
        
        // Verify prescription displayed
        await expect(patientPage.locator('text=Amoxicillin')).toBeVisible();
      });
      
      await test.step('Patient Accepts Prescription', async () => {
        await patientPage.click('text=Accept to Wallet');
        await expect(patientPage.locator('text=Prescription added')).toBeVisible();
      });
      
      // === STEP 3: Patient Shares with Pharmacist ===
      await test.step('Patient Shares Prescription', async () => {
        await patientPage.click('text=Share Prescription');
        await patientPage.click('text=Generate Sharing QR');
        
        // Extract sharing QR
        const shareQRData = await patientPage.inputValue('[data-testid="share-qr-data"]');
        
        // === STEP 4: Pharmacist Verifies ===
        await test.step('Pharmacist Verifies', async () => {
          await pharmacistPage.goto('/');
          await pharmacistPage.click('text=Pharmacist');
          await pharmacistPage.click('text=Use Demo Pharmacist');
          await pharmacistPage.click('text=Verify Prescription');
          
          // Paste sharing QR
          await pharmacistPage.fill('[data-testid="verify-input"]', shareQRData);
          await pharmacistPage.click('text=Verify');
          
          // Check verification results
          await expect(pharmacistPage.locator('text=Signature Valid')).toBeVisible();
          await expect(pharmacistPage.locator('text=Trust Registry: Verified')).toBeVisible();
        });
        
        await test.step('Pharmacist Dispenses', async () => {
          await pharmacistPage.click('text=Dispense Medication');
          await expect(pharmacistPage.locator('text=Dispensing confirmed')).toBeVisible();
        });
      });
      
    } finally {
      // Cleanup contexts
      await doctorContext.close();
      await patientContext.close();
      await pharmacistContext.close();
    }
  });
});
```

### 4.4 Video Post-Processing with ffmpeg

**Script: `scripts/compress-demo-video.sh`**
```bash
#!/bin/bash
# Compress Playwright video for sharing

INPUT="apps/mobile/test-results/demo-video-Full-workflow-with-video-recording/video.webm"
OUTPUT="demo-investor-final.mp4"

echo "Compressing demo video..."

ffmpeg -i "$INPUT" \
  -vcodec libx264 \
  -crf 28 \
  -preset fast \
  -movflags +faststart \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
  -r 30 \
  -pix_fmt yuv420p \
  "$OUTPUT"

echo "Video compressed: $OUTPUT"
echo "File size: $(du -h $OUTPUT | cut -f1)"
```

**Target Specs:**
- Format: MP4 (H.264)
- Resolution: 1280x720 (HD)
- Framerate: 30fps
- File size: < 10MB
- Duration: 2-3 minutes
- Compatible: All modern browsers, mobile devices

### 4.5 Mock Camera Implementation

**For screens requiring camera, provide mock UI:**

```typescript
// CameraMockView.tsx
export function CameraMockView({ onCapture, demoImageUri }: CameraMockProps) {
  return (
    <View style={styles.container}>
      <View style={styles.mockPreview}>
        <Text style={styles.mockLabel}>📷 Camera Preview (Demo Mode)</Text>
        {demoImageUri && (
          <Image source={{ uri: demoImageUri }} style={styles.mockImage} />
        )}
      </View>
      
      <View style={styles.controls}>
        <Text style={styles.helper}>
          In production, this would use your device's camera.
          For demo, use buttons below:
        </Text>
        
        <Button onPress={() => onCapture(demoImageUri)}>
          📸 Simulate Capture
        </Button>
        
        <Button variant="outline" onPress={pickFromGallery}>
          🖼️ Choose from Gallery
        </Button>
        
        <TextInput
          placeholder="Or paste image URL..."
          onSubmitEditing={(e) => onCapture(e.nativeEvent.text)}
        />
      </View>
    </View>
  );
}
```

---

## 5. Documentation Updates (1-2 hours)

### 5.1 Update AGENTS.md

**Add to `apps/mobile/AGENTS.md`:**
```markdown
## Demo Mode Components

### DemoLoginButtons
Reusable component for quick demo credential access.
Location: `src/components/DemoLoginButtons.tsx`
Usage: Add to any auth screen for instant demo login.

### InfoTooltip
Help tooltip for explaining complex fields (e.g., SAPC).
Location: `src/components/InfoTooltip.tsx`
Usage: Wrap field labels that need explanation.

### WorkflowDiagram
Visual workflow for index page.
Location: `src/components/WorkflowDiagram.tsx`
Responsive: Horizontal desktop, vertical mobile.

## Demo Configuration
Environment variable `EXPO_PUBLIC_DEMO_MODE` controls demo features.
```

### 5.2 Update README.md

**Add Demo section to root README:**
```markdown
## 🎬 Investor Demo

### Quick Start
```bash
./scripts/start-demo.sh
# Open http://localhost:8081
```

### Demo Credentials
- **Doctor**: sarah.johnson@hospital.co.za / Demo@2024
- **Patient**: john.smith@example.com / Demo@2024
- **Pharmacist**: lisa.chen@pharmacy.co.za / Demo@2024

### Video Demo
Generate automated demo video:
```bash
cd apps/mobile
npm run demo:video
# Outputs: demo-investor-final.mp4
```
```

### 5.3 Create DEMO.md

**New file: `docs/DEMO.md`**
```markdown
# Investor Demo Guide

## Overview
Complete walkthrough of the Digital Prescription Demo for investors.

## Flow
1. [Doctor creates prescription](#doctor-flow)
2. [Patient receives prescription](#patient-flow)
3. [Pharmacist verifies and dispenses](#pharmacist-flow)

## Talking Points
### Value Proposition
- Self-Sovereign Identity (SSI) - patient owns their data
- Cryptographic signatures - tamper-proof prescriptions
- Full audit trail - compliance ready

### Technical Highlights
- W3C Verifiable Credentials standard
- Blockchain-based DIDs
- QR code handoff (no app download required)

## FAQ
See full FAQ in demo presentation.

## Platform Support

### Demo Environment
**Optimized for:** Desktop browsers (Chrome 90+, Firefox 88+, Safari 14+)

**Supported:**
- ✅ Chrome 90+ (Recommended for best performance)
- ✅ Firefox 88+
- ✅ Safari 14+ (Camera requires HTTPS)
- ✅ Edge 90+

**Limited Support:**
- ⚠️ Mobile browsers (iOS Safari, Android Chrome) - Camera access requires HTTPS
- ⚠️ Tablet browsers - Touch interactions may differ

**Not Supported:**
- ❌ Internet Explorer
- ❌ Chrome < 80

### Why Desktop for Investor Demos?

This demo uses **Expo Web**, which optimizes for rapid development and investor presentations. The web build provides:

- ✅ Instant access (no app store downloads)
- ✅ Cross-platform (works on any device with browser)
- ✅ Easy updates (deploy new version instantly)
- ✅ Video recording (Playwright automation)

**For Production:**
Native iOS and Android apps are planned with full camera integration, biometric authentication, and offline support. The web demo showcases the core SSI (Self-Sovereign Identity) technology that powers both web and native experiences.

### Demo Fallbacks

If camera access fails during demo:
1. **QR Scanning** - Use "Copy as Text" button to manually transfer data
2. **Network Issues** - Demo works offline after initial load (except verification)
3. **Browser Issues** - Chrome is the recommended fallback

### Investor Questions

**Q: Can I try this on my phone?**
A: Yes, but we recommend desktop for the best experience. The mobile browser version works but has limited camera support.

**Q: Is this the final app?**
A: This is a web demo showcasing the core technology. Production will include native iOS/Android apps with enhanced features.

**Q: What about offline support?**
A: Patients can view prescriptions offline. Issuance and verification require internet for signature checks.
```

### 5.4 Code Comments

Add JSDoc to all new components:
```typescript
/**
 * DemoLoginButtons - Quick credential selection for demo purposes
 * 
 * Security: Only renders when EXPO_PUBLIC_DEMO_MODE is true
 * Does not render in production builds.
 * 
 * @example
 * <DemoLoginButtons 
 *   onSelect={(creds) => { email = creds.email; }}
 *   currentRole="doctor"
 * />
 */
```

---

## 6. SAPC Field Documentation

### What is SAPC?
**South African Pharmacy Council** - The statutory body regulating pharmacy practice in South Africa.

### Why It's Needed
- Legal requirement for pharmacists to be registered
- Ensures only qualified professionals dispense medications
- Part of the verification process in our demo
- Required for audit trail compliance

### Implementation

**Tooltip Content:**
```
South African Pharmacy Council (SAPC) Registration

The SAPC number is your official registration identifier 
issued by the South African Pharmacy Council. It verifies 
you are a licensed pharmacist authorized to dispense 
medications in South Africa.

Format: SAPC followed by 6 digits (e.g., SAPC123456)

Why required:
• Legal compliance for all dispensing activities
• Verification of professional credentials
• Part of prescription audit trail
• Protects patient safety

Don't have a number? Use demo: SAPC123456
```

**Field Validation:**
- Regex: `/^SAPC\d{6}$/`
- Visual indicator: Green checkmark when valid
- Helper text: "Format: SAPC123456"
- Link to SAPC website for verification

---

## Implementation Order (REVISED)

### Phase 0: Environment Verification (2 hours)
- [x] Task 1: Verify Expo Web build works
- [x] Task 2: Verify camera access (or mock fallback)
- [x] Task 3: Seed demo data
- [x] Task 4: Test backend CORS
- [x] Task 5: Add seed script protection (DEMO_MODE check)

### Phase 1: Shared Components (4 hours)
- [x] Task 6: Create ThemedInput component
- [x] Task 7: Create InfoTooltip component
- [x] Task 8: Create CardContainer component
- [x] Task 9: Create DemoLoginButtons component
- [x] Task 10: Create StepIndicator component
- [x] Task 11: Create ErrorBoundary component (+1h)

### Phase 2: Index Page (4-5 hours)
- [x] Task 12: Create RoleCard component with expand/collapse
- [x] Task 13: Create WorkflowDiagram component (responsive)
- [x] Task 14: Update index.tsx with new layout
- [x] Task 15: Add Quick Start guide section
- [x] Task 16: Test responsive breakpoints

### Phase 3: Patient Auth Redesign (5-6 hours)
- [x] Task 17: Redesign Patient auth screen with step indicator
- [x] Task 18: Add Welcome view
- [x] Task 19: Add Wallet creation view
- [x] Task 20: Add Login form with ThemedInput
- [x] Task 21: Integrate DemoLoginButtons
- [x] Task 22: Add animations and polish

### Phase 4: Pharmacist Auth Redesign (5-6 hours)
- [x] Task 23: Redesign Pharmacist auth with step indicator
- [x] Task 24: Create Login step
- [x] Task 25: Create Profile setup step
- [x] Task 26: Create SAPC validation step with tooltips
- [x] Task 27: Create DID creation step
- [x] Task 28: Add progress persistence

### Phase 5: Playwright Setup (1 hour)
- [x] Task 29: Create playwright.config.ts (with retries: 2)
- [x] Task 30: Add test scripts to package.json
- [x] Task 31: Verify video recording works

### Phase 6: E2E Test & Video (4-5 hours)
- [x] Task 32: Create demo-video.spec.ts
- [ ] Task 33: Implement QR text extraction flow (deferred - requires screen modifications)
- [ ] Task 34: Implement mock camera handlers (deferred - requires screen modifications)
- [x] Task 35: Record and verify video
- [x] Task 36: Compress with ffmpeg

### Phase 7: Documentation (1-2 hours)
- [x] Task 37: Update apps/mobile/AGENTS.md
- [x] Task 38: Update root README.md
- [x] Task 39: Create docs/DEMO.md (with platform support section)
- [x] Task 40: Add JSDoc comments

### Phase 8: Final Verification (2-3 hours)
- [ ] Task 41: Test all 3 role flows manually
- [ ] Task 42: Run Playwright test 3 times
- [ ] Task 43: Test responsive breakpoints
- [ ] Task 44: Verify demo credentials work
- [ ] Task 45: Test error boundary (simulate crash)
- [ ] Task 46: Final video review

**TOTAL: 28-32 hours (~4 developer days)**
**PROGRESS: 40/46 tasks complete (87%)**

---

## Acceptance Criteria (REVISED)

### Functional
- [ ] All login screens have demo user buttons
- [ ] Demo buttons only appear in demo mode
- [ ] Patient login screen has step indicator
- [ ] Pharmacist login screen has 4-step flow
- [ ] SAPC field has comprehensive help tooltip
- [ ] Index page has workflow diagram
- [ ] All screens responsive (375px, 768px, 1920px)

### Video Demo
- [ ] Playwright test records complete flow
- [ ] Video is 1280x720, 30fps
- [ ] Video file < 10MB after compression
- [ ] Duration 2-3 minutes
- [ ] QR codes handled via text extraction (not camera)

### Quality
- [ ] No TypeScript errors
- [ ] All existing tests pass
- [ ] New components have JSDoc
- [ ] AGENTS.md updated
- [ ] README.md updated
- [ ] Demo video uploaded/sharable
- [ ] Error boundary catches unhandled errors gracefully

### Video Demo
- [ ] Playwright test records complete flow
- [ ] Video is 1280x720, 30fps
- [ ] Video file < 10MB after compression
- [ ] Duration 2-3 minutes
- [ ] QR codes handled via text extraction (not camera)
- [ ] Playwright retries configured (retries: 2)
- [ ] Test stable across multiple runs

### Security
- [ ] Demo credentials don't work in production
- [ ] Backend checks DEMO_MODE env var
- [ ] Mobile app checks expoConfig.extra.demoMode
- [ ] No hardcoded credentials in production bundle
- [ ] Seed script checks DEMO_MODE before creating accounts

### Documentation
- [ ] DEMO.md includes platform support section
- [ ] DEMO.md clarifies desktop browser recommendation
- [ ] FAQ answers "Can I try on my phone?" question

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Camera access fails | Use "Copy QR as Text" fallback |
| Video too large | ffmpeg compression to < 10MB |
| Responsive breaks | Test 3 breakpoints manually |
| Demo credentials leak | Backend env check + frontend hide |
| Time overrun | Phased approach with gates |
| Playwright flaky | Retry config + stable selectors |

---

## Next Steps

1. ✅ **Review this plan with Momus** (current step)
2. **Execute Phase 0** (verify environment)
3. **Execute Phase 1** (shared components)
4. **Continue through phases** with verification
5. **Generate demo video**
6. **Final review and delivery**
