# Digital Prescription MVP - Demo Testing Guide

**Status:** ✅ Ready for Testing  
**Date:** 2026-02-12  
**Version:** 1.0  

---

## 🚀 Quick Start

### Automated Demo Setup (Recommended)

Run the automated startup script to initialize everything in one command:

**macOS / Linux:**
```bash
chmod +x scripts/start-demo.sh
./scripts/start-demo.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-demo-windows.ps1
```

**What the script does:**
1. ✅ Validates prerequisites (Python 3.12+, Node.js 20+, Docker)
2. ✅ Starts Docker infrastructure (PostgreSQL, Redis, ACA-Py)
3. ✅ Sets up backend (venv, dependencies, migrations)
4. ✅ Seeds demo data (3 users, sample prescriptions)
5. ✅ Starts backend API (http://localhost:8000)
6. ✅ Starts mobile app (Expo on port 8081)
7. ✅ Displays demo credentials

**First run:** 3-5 minutes (downloads Docker images)  
**Subsequent runs:** 30-60 seconds

---

## 📋 Prerequisites

### Required Software
- **Python 3.11+** (3.12 recommended)
- **Node.js 20+** (22.18+ works)
- **Docker Desktop** (running)
- **Git** (for cloning)

### Verify Installation
```bash
python3 --version  # Should show 3.11+
node --version     # Should show v20+
docker --version   # Should show 20+
docker ps          # Should return running containers (or empty list)
```

### Mobile Testing Options
1. **iOS Simulator** (macOS only) - Requires Xcode
2. **Android Emulator** - Requires Android Studio
3. **Physical Device** - Install Expo Go app, scan QR code

---

## 🎭 Demo Credentials

The automated script seeds the database with three test users:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Doctor** | `sarah.johnson@hospital.co.za` | `Demo@2024` | Can create, sign, and send prescriptions |
| **Patient** | `john.smith@example.com` | `Demo@2024` | Can receive, view, and share prescriptions |
| **Pharmacist** | `lisa.chen@pharmacy.co.za` | `Demo@2024` | Can verify and dispense prescriptions |

---

## 🧪 Testing Scenarios

### Scenario 1: Doctor Creates Prescription (5 minutes)

**Objective:** Demonstrate prescription creation and digital signing.

#### Steps:

1. **Login as Doctor**
   - Open mobile app (Expo on iOS/Android)
   - Select "Doctor" role
   - Email: `sarah.johnson@hospital.co.za`
   - Password: `Demo@2024`
   - Expected: Navigate to doctor dashboard (blue theme)

2. **Create New Prescription**
   - Tap "Create Prescription" button
   - Select Patient: `John Smith` (from dropdown)
   - Add Medication:
     - Name: `Amoxicillin`
     - Dosage: `500mg`
     - Frequency: `Twice daily`
     - Duration: `7 days`
     - Quantity: `14 capsules`
   - Add Instructions: `Take with food`
   - Expected: Form validation passes, preview screen shown

3. **Sign Prescription**
   - Review prescription details
   - Tap "Sign Prescription"
   - Expected: Digital signature created (using doctor's DID)
   - Expected: Signature hash displayed (e.g., `sig-abc123...`)

4. **Generate QR Code**
   - Tap "Generate QR Code"
   - Expected: QR code displayed (300x300px minimum)
   - Expected: Patient instructions shown ("Have patient scan this code")

**Verification Points:**
- ✅ Prescription ID created (e.g., `rx-20260212-001`)
- ✅ Status badge shows "SIGNED" (green)
- ✅ Digital signature hash displayed
- ✅ QR code contains verifiable credential

**API Testing (Optional):**
```bash
# Get doctor's auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sarah.johnson@hospital.co.za","password":"Demo@2024"}' \
  | jq -r '.access_token')

# Create prescription
curl -X POST http://localhost:8000/api/v1/prescriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-001",
    "medications": [
      {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "duration": "7 days",
        "quantity": 14
      }
    ]
  }'

# Expected: JSON response with prescription_id, status: "draft"
```

---

### Scenario 2: Patient Receives Prescription (3 minutes)

**Objective:** Demonstrate QR code scanning and prescription verification.

#### Steps:

1. **Login as Patient**
   - Open mobile app (separate device or logout/login)
   - Select "Patient" role
   - Email: `john.smith@example.com`
   - Password: `Demo@2024`
   - Expected: Navigate to patient wallet (cyan theme)

2. **Scan Doctor's QR Code**
   - Tap "Scan Prescription" button
   - Grant camera permission (if prompted)
   - Point camera at doctor's QR code (from Scenario 1)
   - Expected: Camera preview with scanning overlay

3. **Verify Prescription**
   - Expected: Automatic verification starts after scan
   - Expected: Loading indicator displayed
   - Expected: Prescription details shown after verification
   - Verify details:
     - ✅ Doctor name: `Dr. Sarah Johnson`
     - ✅ Medication: `Amoxicillin 500mg, twice daily`
     - ✅ Signature status: `✓ Verified` (green badge)

4. **Accept Prescription**
   - Review prescription details
   - Tap "Accept Prescription"
   - Expected: Prescription added to wallet
   - Expected: Navigation to prescription detail view

**Verification Points:**
- ✅ Prescription appears in wallet list
- ✅ Status badge shows "ACTIVE" (green)
- ✅ Expiry date displayed (e.g., "Expires: 2026-05-12")
- ✅ Doctor signature verified

**API Testing (Optional):**
```bash
# Verify prescription credential
curl -X POST http://localhost:8000/api/v1/prescriptions/verify \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "presentation": {...}
  }'

# Expected: { "valid": true, "prescription": {...} }
```

---

### Scenario 3: Pharmacist Dispenses Medication (4 minutes)

**Objective:** Demonstrate prescription verification and dispensing workflow.

#### Steps:

1. **Login as Pharmacist**
   - Open mobile app
   - Select "Pharmacist" role
   - Email: `lisa.chen@pharmacy.co.za`
   - Password: `Demo@2024`
   - Expected: Navigate to pharmacist dashboard (green theme)

2. **Scan Patient's Prescription**
   - Tap "Verify Prescription"
   - Patient shows QR code from their wallet (Scenario 2)
   - Scan patient's QR code
   - Expected: Prescription verification starts

3. **Verify Prescription Authenticity**
   - Expected: Verification checks:
     - ✅ Doctor's digital signature valid
     - ✅ Prescription not expired
     - ✅ Prescription not already dispensed
     - ✅ Prescription not revoked
   - Expected: Verification result displayed (✓ Valid or ✗ Invalid)

4. **View Dispensing Details**
   - Review prescription:
     - Patient name: `John Smith`
     - Doctor: `Dr. Sarah Johnson`
     - Medication: `Amoxicillin 500mg`
     - Quantity: `14 capsules`
     - Instructions: `Take with food, twice daily for 7 days`

5. **Dispense Medication**
   - Tap "Mark as Dispensed"
   - Confirm dispensing action
   - Expected: Status updated to "DISPENSED"
   - Expected: Timestamp recorded
   - Expected: Audit log entry created

**Verification Points:**
- ✅ Prescription status changed to "USED" (gray badge)
- ✅ Patient's wallet updates status in real-time
- ✅ Prescription cannot be dispensed again
- ✅ Audit trail records pharmacist action

**API Testing (Optional):**
```bash
# Get pharmacist's auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"lisa.chen@pharmacy.co.za","password":"Demo@2024"}' \
  | jq -r '.access_token')

# Dispense prescription
curl -X POST http://localhost:8000/api/v1/prescriptions/rx-20260212-001/dispense \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pharmacist_id": "pharmacist-001",
    "dispensed_items": [
      { "medication_name": "Amoxicillin", "quantity": 14 }
    ]
  }'

# Expected: { "success": true, "status": "dispensed" }
```

---

### Scenario 4: Error Handling - Expired Prescription (2 minutes)

**Objective:** Demonstrate time-based validation and error handling.

#### Steps:

1. **Create Expired Prescription (Backend)**
   ```bash
   # Manually insert expired prescription via database or API
   curl -X POST http://localhost:8000/api/v1/admin/prescriptions/expired \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

2. **Patient Attempts to Use Expired Prescription**
   - Login as patient
   - Attempt to share expired prescription with pharmacist
   - Expected: Error message displayed
   - Expected: Status badge shows "EXPIRED" (red)

3. **Pharmacist Scans Expired Prescription**
   - Login as pharmacist
   - Scan expired prescription QR code
   - Expected: Verification fails with error:
     - `❌ Prescription expired on 2026-01-15`
   - Expected: "Mark as Dispensed" button disabled
   - Expected: User-friendly error explanation displayed

**Verification Points:**
- ✅ System prevents dispensing expired prescriptions
- ✅ Clear error messages displayed to user
- ✅ Audit trail records verification failure

---

### Scenario 5: Revocation - Doctor Cancels Prescription (3 minutes)

**Objective:** Demonstrate prescription revocation and real-time status updates.

#### Steps:

1. **Doctor Revokes Prescription**
   - Login as doctor
   - Navigate to "My Prescriptions"
   - Select active prescription (from Scenario 1)
   - Tap "Revoke Prescription"
   - Enter reason: `Patient reported allergy to Amoxicillin`
   - Confirm revocation
   - Expected: Status updated to "REVOKED" (red badge)

2. **Patient Sees Revoked Status**
   - Login as patient (or refresh wallet)
   - View prescription in wallet
   - Expected: Status badge shows "REVOKED" (red)
   - Expected: Revocation reason displayed
   - Expected: QR code becomes invalid

3. **Pharmacist Cannot Dispense Revoked Prescription**
   - Login as pharmacist
   - Attempt to scan revoked prescription
   - Expected: Verification fails with error:
     - `❌ Prescription revoked by Dr. Sarah Johnson`
     - `Reason: Patient reported allergy to Amoxicillin`
   - Expected: Dispensing blocked

**Verification Points:**
- ✅ Revocation propagates to all roles in real-time
- ✅ Revoked prescriptions cannot be dispensed
- ✅ Revocation reason visible to all parties
- ✅ Audit trail records revocation event

---

## 🔧 Troubleshooting

### Issue: Docker Services Not Starting

**Symptoms:**
- `docker-compose up` fails
- Services show "Exited" status
- Port conflicts (8000, 8001, 5432, 6379)

**Solutions:**
```bash
# Check service status
docker-compose ps

# View logs for errors
docker-compose logs acapy
docker-compose logs db

# Restart services
docker-compose down
docker-compose up -d db redis acapy

# Check port conflicts
lsof -i :8000  # Backend API
lsof -i :8001  # ACA-Py admin
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

### Issue: Backend API Not Responding

**Symptoms:**
- `curl http://localhost:8000/api/v1/health` fails
- Mobile app shows "Network Error"

**Solutions:**
```bash
# Check backend process
ps aux | grep uvicorn

# Check backend logs
cd services/backend
source venv/bin/activate
uvicorn app.main:app --reload --log-level debug

# Test database connection
docker exec rx_postgres pg_isready -U postgres

# Test Redis connection
docker exec rx_redis redis-cli ping
```

### Issue: Mobile App Cannot Connect

**Symptoms:**
- Expo app shows "Could not connect to development server"
- QR code does not load

**Solutions:**
```bash
# Check if Metro bundler is running
lsof -i :8081

# Restart Expo
cd apps/mobile
npx expo start --clear

# Use tunnel mode if network issues
npx expo start --tunnel

# Check if phone and computer on same WiFi
```

### Issue: QR Code Scanning Not Working

**Symptoms:**
- Camera permission denied
- QR code not recognized
- Verification fails after scan

**Solutions:**
1. **Camera Permission:** Grant camera access in Settings → Your App
2. **QR Code Quality:** Ensure QR code is clear, not pixelated
3. **Lighting:** Improve lighting conditions
4. **Manual Entry:** Use "Enter Code Manually" fallback option

**Manual Code Entry:**
```
1. Doctor displays prescription code (e.g., RX-20260212-001)
2. Patient taps "Enter Code Manually"
3. Patient types code in text input
4. System retrieves prescription by code
```

### Issue: Signature Verification Fails

**Symptoms:**
- `❌ Signature verification failed`
- `❌ Unknown issuer DID`

**Solutions:**
```bash
# Check ACA-Py admin API
curl http://localhost:8001/status

# Verify doctor's DID is registered
curl http://localhost:8000/api/v1/dids/doctor-abc123

# Check trust registry
curl http://localhost:8000/api/v1/admin/trust-registry

# Reseed demo data
cd services/backend
python scripts/seed_demo_data.py --reset
```

---

## 📊 Expected Test Results

### Success Metrics

| Test Scenario | Expected Duration | Pass Criteria |
|---------------|-------------------|---------------|
| Doctor creates prescription | 5 minutes | ✅ Prescription signed, QR generated |
| Patient receives prescription | 3 minutes | ✅ QR scanned, credential verified |
| Pharmacist dispenses medication | 4 minutes | ✅ Verification passed, status updated |
| Expired prescription handling | 2 minutes | ✅ Error displayed, dispensing blocked |
| Revocation workflow | 3 minutes | ✅ Status updates across all roles |

**Total Test Time:** ~20 minutes (full end-to-end demo)

### Coverage

| Feature | Status | Notes |
|---------|--------|-------|
| Authentication (3 roles) | ✅ Working | OAuth 2.0 with PKCE |
| Prescription creation | ✅ Working | FHIR-inspired schema |
| Digital signatures | ✅ Working | W3C Verifiable Credentials |
| QR code generation | ✅ Working | 300x300px minimum |
| QR code scanning | ✅ Working | Expo Camera integration |
| Credential verification | ✅ Working | Signature + time validation |
| Time-based validation | ✅ Working | Expiry checks enforced |
| Revocation handling | ✅ Working | Real-time status updates |
| Audit trail | ✅ Working | All actions logged |
| Error handling | ✅ Working | User-friendly messages |

---

## 🔐 Security Testing (Optional)

### Test: Tampered Prescription Detection

**Objective:** Verify signature validation catches tampering.

```bash
# Get valid prescription credential
CREDENTIAL=$(curl -s http://localhost:8000/api/v1/prescriptions/rx-001 \
  -H "Authorization: Bearer $TOKEN" | jq -r '.credential')

# Modify credential (e.g., change dosage)
TAMPERED=$(echo $CREDENTIAL | sed 's/500mg/1000mg/')

# Attempt verification
curl -X POST http://localhost:8000/api/v1/prescriptions/verify \
  -H "Content-Type: application/json" \
  -d "{\"credential\": \"$TAMPERED\"}"

# Expected: { "valid": false, "error": "Signature verification failed" }
```

### Test: Unauthorized Access Prevention

```bash
# Attempt to access prescription without token
curl http://localhost:8000/api/v1/prescriptions/rx-001

# Expected: 401 Unauthorized

# Attempt to dispense as non-pharmacist
curl -X POST http://localhost:8000/api/v1/prescriptions/rx-001/dispense \
  -H "Authorization: Bearer $PATIENT_TOKEN"

# Expected: 403 Forbidden
```

---

## 📝 Demo Script (For Presentations)

**Duration:** 10 minutes (for stakeholder demo)

### Introduction (1 minute)
> "This is a digital prescription system using Self-Sovereign Identity. We'll demonstrate the full workflow: doctor creates and signs a prescription, patient receives it in their digital wallet, and pharmacist verifies and dispenses it. All using verifiable credentials and digital signatures."

### Act 1: Doctor (3 minutes)
1. Login as doctor → show blue themed dashboard
2. Create prescription for John Smith → Amoxicillin 500mg
3. Sign prescription → show signature hash
4. Generate QR code → "Patient will scan this"

### Act 2: Patient (3 minutes)
1. Login as patient → show cyan themed wallet
2. Scan doctor's QR code → show verification process
3. Accept prescription → show in wallet list
4. Prepare to share with pharmacist → generate patient QR

### Act 3: Pharmacist (3 minutes)
1. Login as pharmacist → show green themed dashboard
2. Scan patient's QR code → show verification checks
3. View dispensing details → confirm medication/dosage
4. Mark as dispensed → show status update across all roles

### Conclusion (30 seconds)
> "Key benefits: cryptographically secure, tamper-proof, verifiable in real-time, works offline with QR codes, full audit trail for compliance. Ready for production deployment with DIDx CloudAPI integration."

---

## 🎯 Next Steps

### After Successful Testing

1. **Production Deployment**
   - Switch from ACA-Py to DIDx CloudAPI (configuration-only change)
   - Deploy to Kubernetes cluster
   - Configure production secrets (not `Demo@2024`)
   - Enable HTTPS/TLS

2. **Enhanced Features (Phase 2)**
   - Replace QR codes with DIDComm v2 messaging
   - Implement full FHIR R4 compliance
   - Add prescription repeats/refills
   - Advanced audit trail with reporting
   - Native mobile features (biometric auth, push notifications)

3. **Regulatory Compliance**
   - HPCSA registration verification
   - SAPC registration verification
   - POPIA compliance audit
   - Medicines Act controlled substance handling

---

## 📞 Support

### If Tests Fail

1. **Check Prerequisites:** Python 3.11+, Node.js 20+, Docker running
2. **Review Logs:** `docker-compose logs`, backend console output
3. **Reset Environment:**
   ```bash
   docker-compose down -v  # Remove volumes
   rm -rf services/backend/venv
   ./scripts/start-demo.sh  # Reinitialize
   ```
4. **Known Issues:** Check GitHub Issues or TROUBLESHOOTING.md

### Contact

- **GitHub Issues:** https://github.com/grant-vine/digital-prescription-demo/issues
- **Developer:** Grant Vine
- **Status:** MVP Complete (2026-02-12)

---

**Version:** 1.0  
**Last Updated:** 2026-02-12  
**Status:** ✅ Ready for Demo Testing
