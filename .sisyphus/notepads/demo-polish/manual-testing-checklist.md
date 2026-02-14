# Manual Testing Checklist - SDK 54 Migration
**Created**: 2026-02-14
**Status**: Ready for execution
**Estimated Time**: 3.5 hours total

---

## Prerequisites

### Infrastructure Setup
```bash
# Start all services
./scripts/start-demo.sh

# Verify services are running
docker-compose ps  # All should show "healthy"
curl http://localhost:8000/api/v1/health  # Backend health check
curl http://localhost:8081  # Expo dev server
```

### Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Doctor | `sarah.johnson@hospital.co.za` | `Demo@2024` |
| Patient | `john.smith@example.com` | `Demo@2024` |
| Pharmacist | `lisa.chen@pharmacy.co.za` | `Demo@2024` |

---

## Task 87: Manual QR Code Testing (1.5 hours)

### Doctor: QR Generation (30 minutes)

**Setup:**
1. Open mobile app (Expo Go or web browser at http://localhost:8081)
2. Select "Doctor" role from role selector
3. Login with demo credentials

**Test Cases:**
- [ ] **TC-87.1**: Navigate to prescription creation
  - Expected: Prescription form loads
  - Expected: No console errors
  
- [ ] **TC-87.2**: Fill prescription details
  - Select patient: John Smith
  - Add medication: Amoxicillin 500mg
  - Set dosage: 1 tablet, 3 times daily, 7 days
  - Expected: Form validates correctly
  
- [ ] **TC-87.3**: Sign prescription
  - Click "Sign Prescription"
  - Expected: Signing process completes
  - Expected: Success message shown
  
- [ ] **TC-87.4**: View QR code
  - Navigate to QR display screen
  - Expected: QR code displays clearly
  - Expected: QR code is scannable (not blurry)
  - Expected: Prescription details shown below QR
  - **VISUAL CHECK**: QR code is black-and-white, high contrast
  - **VISUAL CHECK**: QR code fills appropriate screen space

**Notes:**
- If QR code doesn't display: Check console for errors
- If QR code is blurry: This is a regression, report immediately
- Take screenshot of QR code for records

---

### Patient: QR Scanning (45 minutes)

**Setup:**
1. Open mobile app in second device/window
2. Select "Patient" role
3. Login with patient demo credentials

**Test Cases:**
- [ ] **TC-87.5**: Navigate to scan screen
  - Click "Scan Prescription" or camera icon
  - Expected: Camera permission prompt (first time)
  - Expected: Camera view loads
  
- [ ] **TC-87.6**: Test camera permissions
  - Grant camera permission
  - Expected: Camera preview shows
  - Expected: No crashes or errors
  
- [ ] **TC-87.7**: Scan QR code (actual camera test)
  - Point camera at doctor's QR code (from TC-87.4)
  - Expected: QR code detected automatically
  - Expected: Scan success message
  - Expected: Prescription details extracted
  - **TIMING**: Should scan within 2-3 seconds
  
- [ ] **TC-87.8**: Test manual entry fallback
  - Click "Manual Entry" button
  - Enter prescription ID manually
  - Expected: Manual entry form works
  - Expected: Prescription retrieved successfully
  
- [ ] **TC-87.9**: View scanned prescription in wallet
  - Navigate to wallet
  - Expected: New prescription appears
  - Expected: All details match doctor's version
  - Expected: Credential status shows "verified"

**Notes:**
- Camera issues? Check `apps/mobile/src/components/qr/QRScanner.tsx` uses `CameraView`
- QR not scanning? Check lighting, try different angles
- Manual entry fallback is critical - must work if camera fails

---

### Pharmacist: QR Verification (15 minutes)

**Setup:**
1. Open mobile app in third device/window
2. Select "Pharmacist" role
3. Login with pharmacist demo credentials

**Test Cases:**
- [ ] **TC-87.10**: Navigate to verify screen
  - Click "Verify Prescription"
  - Expected: Camera view loads
  
- [ ] **TC-87.11**: Scan patient's QR code
  - Patient shows QR from wallet
  - Pharmacist scans with camera
  - Expected: QR detected and decoded
  - Expected: Verification screen shows
  
- [ ] **TC-87.12**: Verify prescription details
  - Expected: Doctor name shown (Dr. Sarah Johnson)
  - Expected: Patient name shown (John Smith)
  - Expected: Medication details shown
  - Expected: Signature status: "Valid"
  - Expected: Expiration status: "Not expired"
  
- [ ] **TC-87.13**: Test malformed QR handling
  - Try scanning a non-prescription QR code
  - Expected: Error message shown
  - Expected: App doesn't crash
  - Expected: Can retry scanning

**Notes:**
- Verification must complete in <5 seconds
- Any "Invalid" signature status is a critical bug
- Error handling must be graceful (no crashes)

---

## Task 88: End-to-End Role Testing (2 hours)

### Doctor Full Flow (40 minutes)

**Complete Workflow:**
- [ ] **TC-88.1**: Authentication
  - Launch app
  - Select doctor role
  - Use demo login button
  - Expected: Dashboard loads
  - Expected: Navigation menu visible
  
- [ ] **TC-88.2**: Dashboard navigation
  - View recent prescriptions
  - Check statistics/counts
  - Expected: All UI elements render
  - Expected: Theme is blue (#2563EB)
  
- [ ] **TC-88.3**: Create prescription (full flow)
  - Click "New Prescription"
  - **Step 1**: Select patient (search + select)
  - **Step 2**: Add medication (drug search + dosage)
  - **Step 3**: Add second medication (test multi-drug)
  - **Step 4**: Review prescription
  - **Step 5**: Sign prescription
  - Expected: All steps complete without errors
  - Expected: Progress indicator shows current step
  
- [ ] **TC-88.4**: View prescription history
  - Navigate to prescriptions list
  - Click on previous prescription
  - Expected: Details screen loads
  - Expected: Can view but not edit
  
- [ ] **TC-88.5**: Test prescription actions
  - Try to revoke a prescription
  - Expected: Revocation confirmation prompt
  - Expected: Revocation completes
  - Expected: Status updates to "Revoked"

**UI/UX Checks:**
- [ ] Theme consistency (all screens use doctor blue)
- [ ] Navigation works (back button, tabs, drawer)
- [ ] Error handling (network errors show messages)
- [ ] Loading states (spinners during API calls)
- [ ] Responsive design (works on tablet view)

---

### Patient Full Flow (40 minutes)

**Complete Workflow:**
- [ ] **TC-88.6**: Authentication
  - Launch app
  - Select patient role
  - Use demo login button
  - Expected: Wallet screen loads
  
- [ ] **TC-88.7**: Wallet overview
  - View all prescriptions
  - Check empty state (if no prescriptions)
  - Expected: Theme is cyan (#0891B2)
  - Expected: Prescriptions sorted by date
  
- [ ] **TC-88.8**: Receive prescription
  - Scan QR code from doctor
  - Expected: Scan completes
  - Expected: Prescription added to wallet
  - Expected: Notification/success message
  
- [ ] **TC-88.9**: View prescription details
  - Click on prescription in wallet
  - Expected: Full details shown:
    - Doctor information
    - Medication list with dosages
    - Issue date, expiry date
    - Signature status
    - QR code for sharing
  
- [ ] **TC-88.10**: Share prescription
  - Click "Share with Pharmacist"
  - Expected: QR code displayed
  - Expected: Can show to pharmacist for scanning
  - Expected: Can toggle between QR and manual code
  
- [ ] **TC-88.11**: Test prescription filters
  - Filter by status (active, expired, dispensed)
  - Expected: Filtering works correctly
  - Expected: Counts update

**UI/UX Checks:**
- [ ] Mobile-first design (optimized for phone)
- [ ] Bottom navigation works
- [ ] Swipe gestures (if implemented)
- [ ] Prescription cards display clearly
- [ ] No text cutoff or overflow

---

### Pharmacist Full Flow (40 minutes)

**Complete Workflow:**
- [ ] **TC-88.12**: Authentication
  - Launch app
  - Select pharmacist role
  - Use demo login button
  - Expected: Verify screen loads
  
- [ ] **TC-88.13**: Scan and verify
  - Scan patient's prescription QR
  - Expected: Verification completes
  - Expected: Prescription details shown
  - Expected: Signature valid, not expired
  - Expected: Theme is green (#059669)
  
- [ ] **TC-88.14**: View dispensing details
  - Review medication list
  - Check quantities to dispense
  - Expected: All items listed clearly
  - Expected: Can view dosage instructions
  
- [ ] **TC-88.15**: Dispense prescription
  - Click "Dispense"
  - Confirm dispensing action
  - Expected: Dispensing records created
  - Expected: Status updates to "Dispensed"
  - Expected: Cannot dispense twice
  
- [ ] **TC-88.16**: View dispensing history
  - Navigate to history
  - Expected: Previously dispensed prescriptions shown
  - Expected: Can search/filter
  
- [ ] **TC-88.17**: Test error scenarios
  - Try to dispense expired prescription
  - Expected: Error message shown
  - Expected: Dispensing blocked
  - Try to dispense revoked prescription
  - Expected: Error message shown
  - Expected: Dispensing blocked

**UI/UX Checks:**
- [ ] Workstation-optimized layout
- [ ] Large touch targets (for gloved hands)
- [ ] Clear success/error states
- [ ] Audit trail visible
- [ ] No ambiguous states

---

## Shared Components Testing (Across All Roles)

### Demo Mode Features
- [ ] **TC-88.18**: Demo login buttons
  - Test on all three role screens
  - Expected: Auto-fills credentials
  - Expected: Logs in successfully
  - Expected: Only visible in DEMO_MODE

- [ ] **TC-88.19**: Error boundary
  - Trigger an error (if possible)
  - Expected: Error boundary catches it
  - Expected: Shows friendly error message
  - Expected: Offers reload option

- [ ] **TC-88.20**: Role card selector
  - Test role selection on index screen
  - Expected: All three cards display
  - Expected: Correct colors (blue, cyan, green)
  - Expected: Descriptions visible
  - Expected: Click navigates to role

- [ ] **TC-88.21**: Workflow diagram
  - View on index or help screen
  - Expected: Diagram renders
  - Expected: Responsive on mobile
  - Expected: Shows full prescription flow

### Responsive Design
- [ ] **TC-88.22**: Phone view (375x667)
  - Test all screens
  - Expected: No horizontal scroll
  - Expected: Text readable
  - Expected: Buttons accessible

- [ ] **TC-88.23**: Tablet view (768x1024)
  - Test all screens
  - Expected: Layout adapts
  - Expected: Utilizes space well
  - Expected: No weird gaps

- [ ] **TC-88.24**: Web browser (1280x720)
  - Test all screens
  - Expected: Desktop-friendly layout
  - Expected: Centered content
  - Expected: Readable at 100% zoom

---

## Performance & Stability

### Performance Checks
- [ ] **TC-88.25**: App startup time
  - Cold start: <3 seconds to role selector
  - Hot start: <1 second
  
- [ ] **TC-88.26**: Navigation speed
  - Screen transitions: <500ms
  - No lag or stuttering
  
- [ ] **TC-88.27**: API response times
  - Login: <2 seconds
  - Prescription creation: <3 seconds
  - QR scan: <2 seconds after detection
  
- [ ] **TC-88.28**: Memory usage
  - No memory leaks over 10 minutes of use
  - App doesn't slow down over time

### Stability Checks
- [ ] **TC-88.29**: No crashes
  - Complete all workflows without crashes
  - Test edge cases (empty states, errors)
  
- [ ] **TC-88.30**: Network resilience
  - Test with poor network (throttle to 3G)
  - Expected: Graceful error messages
  - Expected: Retry mechanisms work
  
- [ ] **TC-88.31**: Offline behavior
  - Disconnect network
  - Expected: Cached prescriptions still viewable
  - Expected: Appropriate offline messages

---

## Success Criteria

### Must Pass (Blocking Issues)
- [ ] All three role flows complete successfully
- [ ] QR code generation and scanning work
- [ ] No crashes or app-breaking errors
- [ ] TypeScript still compiles (0 errors)
- [ ] All automated tests still pass

### Should Pass (Minor Issues)
- [ ] UI polish looks good (no visual bugs)
- [ ] Performance is acceptable (<3s operations)
- [ ] Error messages are clear
- [ ] Responsive design works on 2+ screen sizes

### Nice to Have (Improvements)
- [ ] Animations smooth (60fps)
- [ ] Advanced features work (filters, search)
- [ ] Accessibility features work (screen reader)

---

## Issue Reporting Template

If you find issues, document them using this format:

```
**Issue ID**: MT-[number]
**Severity**: Critical | Major | Minor
**Task**: TC-[number]
**Component**: [screen/component name]
**Description**: [what went wrong]
**Steps to Reproduce**:
1. [step 1]
2. [step 2]
3. [observed behavior]

**Expected**: [what should happen]
**Actual**: [what actually happened]
**Screenshot**: [if applicable]
**Console Errors**: [paste errors]
**Device**: [iOS/Android/Web, version]
```

---

## Completion Checklist

After completing all manual tests:

- [ ] All test cases executed
- [ ] Results documented (pass/fail for each TC)
- [ ] Screenshots captured for key flows
- [ ] Any issues reported with severity
- [ ] Final decision: Ready for production? Yes/No
- [ ] Update `.sisyphus/plans/sdk-54-migration-tasks.md`:
  - Mark Task 87 complete: `- [x]`
  - Mark Task 88 complete: `- [x]`

---

**Time to Complete**: 3.5 hours
**Last Updated**: 2026-02-14
**Next Step**: Execute checklist, report results
