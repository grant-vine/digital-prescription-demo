## Title
Demo Preparation and Test Data

## User Story
As a demo presenter, I want comprehensive test data and a prepared demo environment so that I can showcase the digital prescription system effectively to stakeholders without encountering data or configuration issues.

## Description
This story establishes the infrastructure needed for successful demos, including realistic test data, demo accounts, pre-configured scenarios, and reset functionality. The demo environment must be stable, repeatable, and contain enough variety to demonstrate all key features.

## Acceptance Criteria

### Test Data Creation
- [ ] Create 5-10 test doctor accounts with:
  - Unique DIDs on cheqd testnet
  - Medical license numbers (mock HPCSA format)
  - Practice information and specializations
  - Valid credentials in wallets
- [ ] Create 10-15 test patient accounts with:
  - Unique DIDs
  - Demographic information (names, ages, medical aid numbers)
  - Pre-loaded wallet configurations
- [ ] Create 3-5 test pharmacy accounts with:
  - Pharmacist credentials (mock SAPC format)
  - Pharmacy practice details
  - Dispensing workstation setups
- [ ] Create 20-30 sample prescriptions in various states:
  - Draft prescriptions (5)
  - Active/signed prescriptions (10)
  - Expired prescriptions (3)
  - Revoked prescriptions (2)
  - Partially dispensed prescriptions (5)
  - Fully dispensed prescriptions (5)

### Demo Scenarios
- [ ] **Scenario 1: Happy Path Flow**
  - Doctor creates prescription
  - Patient receives via QR code
  - Pharmacist verifies and dispenses
  - Complete in under 5 minutes
- [ ] **Scenario 2: Multi-Medication Prescription**
  - Prescription with 3+ medications
  - Demonstrates complex dispensing
- [ ] **Scenario 3: Prescription with Repeats**
  - Shows repeat/refill functionality
  - Pharmacist partial dispensing
- [ ] **Scenario 4: Expired Prescription**
  - Shows validation failure
  - Error handling and messaging
- [ ] **Scenario 5: Revoked Prescription**
  - Doctor revokes after patient receives
  - Pharmacist verification fails
- [ ] **Scenario 6: Doctor Verification**
  - Shows trust registry validation
  - Invalid doctor license scenario

### Demo Scripts
- [ ] Write step-by-step demo script with timing
- [ ] Include talking points for each feature
- [ ] Add fallback scenarios for failures
- [ ] Create quick-reference cards for presenter
- [ ] Document keyboard shortcuts and UI navigation

### Environment Management
- [ ] Create demo reset function that:
  - Restores all test data to initial state
  - Resets all prescriptions to starting conditions
  - Clears audit logs (or archives them)
  - Preserves demo accounts but resets state
- [ ] Create "Demo Mode" configuration:
  - Disables real external services (sends to mock)
  - Enables instant operations (no network delays)
  - Pre-fills forms with test data
  - Shows demo watermark/banner
- [ ] Implement demo state snapshots:
  - Save point before each scenario
  - Quick restore to any scenario start
  - Rollback capability if demo goes wrong

### Test Data Documentation
- [ ] Document all test account credentials
- [ ] List all sample prescription details
- [ ] Map test data to demo scenarios
- [ ] Include expected outcomes for each scenario
- [ ] Create data dictionary for complex fields

## Technical Implementation

### Data Seeding
```python
# demo_seed.py
async def seed_demo_data():
    """Create all test data for demo environment"""
    doctors = await create_test_doctors(count=5)
    patients = await create_test_patients(count=15)
    pharmacies = await create_test_pharmacies(count=3)
    prescriptions = await create_sample_prescriptions(
        doctors=doctors,
        patients=patients,
        states=['draft', 'active', 'expired', 'revoked', 'dispensed']
    )
    return DemoData(doctors, patients, pharmacies, prescriptions)

async def reset_demo_environment():
    """Reset all data to initial demo state"""
    await archive_audit_logs()
    await reset_prescription_states()
    await restore_test_accounts()
    await clear_connections()
```

### Demo Configuration
```python
# config.py
DEMO_MODE = True
DEMO_PRESETS = {
    'instant_ops': True,      # No artificial delays
    'mock_external': True,    # Use mock services
    'prefill_forms': True,    # Auto-fill with test data
    'watermark': 'DEMO',      # Show demo indicator
}
DEMO_SNAPSHOTS = {
    'scenario_1': 'path/to/snapshot_1.sql',
    'scenario_2': 'path/to/snapshot_2.sql',
}
```

## API Integration Points

```
POST /api/admin/demo/seed
POST /api/admin/demo/reset
POST /api/admin/demo/snapshot/create
POST /api/admin/demo/snapshot/restore
GET  /api/admin/demo/status
```

## Notes

### Demo Data Requirements
- All data must be **obviously fake** (e.g., "John Demo Doctor", "Test Patient A")
- No real personal information
- Medical conditions should be common and non-sensitive (flu, allergies, etc.)
- Medications should be common OTC or prescription drugs

### Demo Safety
- Demo mode must be visually distinct (banner, watermark)
- All external notifications disabled
- No real data persistence in demo mode
- Clear "Demo Mode" indicator in UI
- Reset button prominently displayed

### Performance
- Demo data should load in under 30 seconds
- Reset operation should complete in under 10 seconds
- Snapshots should restore in under 5 seconds

### Maintenance
- Update test data quarterly
- Refresh expired dates in prescriptions
- Verify all demo scenarios work before presentations
- Keep demo script updated with UI changes

## Estimation
- **Story Points**: 5
- **Time Estimate**: 2-3 days

## Related Stories
- All MVP stories - this provides test data for them
- US-016 (Audit Trail) - demo reset affects audit logs
