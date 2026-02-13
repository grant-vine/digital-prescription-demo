# Plan: demo-mode

## Overview

**Goal:** Implement `USE_DEMO=true` environment variable that makes the entire digital prescription demo work end-to-end without ACA-Py or any external SSI infrastructure. Mock services produce technically accurate W3C Verifiable Credentials with HMAC-SHA256 signatures that the verification pipeline accepts.

**Context:** The current demo fails at verification (500 error) because:
1. Signing stores wrong data (`proofValue` string instead of full W3C VC JSON)
2. Seed script generates invalid signatures (`sig_{uuid}`)
3. Seed script doesn't create DID model records
4. No mock SSI provider exists despite `SSI_PROVIDER=mock` being referenced
5. ACA-Py is always required — no way to skip it

**Architecture Decision:** HMAC-SHA256 deterministic signing with hardcoded demo secret. Not cryptographically meaningful for production, but enables sign→verify round-trips and tamper detection.

**Estimated Time:** ~3 hours
**Total Tasks:** 23

---

## Phase 0 — Configuration & Environment Wiring

### TASK-D001: Add USE_DEMO to backend configuration
- **File:** `services/backend/app/main.py`
- **Size:** S
- **Action:** Read `USE_DEMO` env var (default `false`), log demo mode status at startup, expose via `app.state.use_demo`
- **Acceptance:**
  - `USE_DEMO=true` logs "🎭 DEMO MODE ENABLED" at startup
  - `USE_DEMO=false` (or unset) logs nothing special
  - `app.state.use_demo` is a boolean accessible from request handlers

### TASK-D002: Add USE_DEMO to docker-compose.yml
- **File:** `docker-compose.yml`
- **Size:** S
- **Action:** Add `USE_DEMO=${USE_DEMO:-false}` to backend service environment
- **Acceptance:**
  - `USE_DEMO=true docker-compose up` passes the var to the backend container

### TASK-D003: Update start-demo.sh to conditionally skip ACA-Py
- **File:** `scripts/start-demo.sh`
- **Size:** M
- **Action:** When `USE_DEMO=true`:
  - Skip ACA-Py health check / startup
  - Skip ACA-Py-dependent setup steps
  - Log that demo mode is active, ACA-Py not required
  - Pass `USE_DEMO=true` to backend startup
- **Acceptance:**
  - `USE_DEMO=true ./scripts/start-demo.sh` starts without Docker/ACA-Py
  - Normal startup (no `USE_DEMO`) behaves unchanged

---

## Phase 1 — Create Mock Service

### TASK-D004: Create DemoACAPyService
- **File:** `services/backend/app/services/demo_acapy.py` (NEW)
- **Size:** M (critical path)
- **Action:** Create a `DemoACAPyService` class that mirrors the `ACAPyService` interface but uses HMAC-SHA256 for all signing/verification operations. Key design:
  ```python
  DEMO_HMAC_SECRET = b"rxdistribute-demo-mode-secret-key-2026"
  
  # create_did() → returns did:cheqd:testnet:demo-{uuid}, stores key material
  # sign_credential(credential) → adds W3C proof with HMAC-SHA256 proofValue (z-prefixed)
  # verify_credential(credential) → recomputes HMAC, compares to proofValue
  # create_schema(), create_credential_definition() → return mock IDs
  # All other ACAPyService methods → return reasonable mock responses
  ```
- **Acceptance:**
  - Class has same public interface as `ACAPyService`
  - `sign_credential()` → `verify_credential()` round-trip succeeds
  - Modifying any credential field after signing causes verification to fail
  - DIDs use `did:cheqd:testnet:` prefix (passes trust registry check in verification.py)
  - No HTTP calls, no external dependencies

---

## Phase 2 — Service Factory

### TASK-D005: Create service factory
- **File:** `services/backend/app/services/factory.py` (NEW)
- **Size:** S
- **Action:** Create `get_acapy_service()` function that returns `DemoACAPyService` when `USE_DEMO=true`, else `ACAPyService`
- **Acceptance:**
  - `USE_DEMO=true` → returns `DemoACAPyService` instance
  - `USE_DEMO=false` → returns `ACAPyService` instance
  - Singleton pattern (same instance per request lifecycle)

### TASK-D006: Update vc.py to use factory
- **File:** `services/backend/app/services/vc.py`
- **Size:** S
- **Action:** Replace direct `ACAPyService` imports/instantiation with `get_acapy_service()` from factory
- **Acceptance:** All existing vc.py behavior unchanged when `USE_DEMO=false`

### TASK-D007: Update signing.py to use factory
- **File:** `services/backend/app/api/v1/signing.py`
- **Size:** S
- **Action:** Replace direct `ACAPyService` imports with factory
- **Acceptance:** All existing signing behavior unchanged when `USE_DEMO=false`

### TASK-D008: Update dids.py to use factory
- **File:** `services/backend/app/api/v1/dids.py`
- **Size:** S
- **Action:** Replace direct `ACAPyService` imports with factory
- **Acceptance:** All existing DID behavior unchanged when `USE_DEMO=false`

### TASK-D009: Update any other files importing ACAPyService directly
- **File:** Various (grep for imports)
- **Size:** S
- **Action:** Find and update all remaining direct imports of `ACAPyService`
- **Acceptance:** No file imports `ACAPyService` directly except `factory.py` and `demo_acapy.py`

---

## Phase 3 — Fix Signing Bug (Critical)

### TASK-D010: Fix signing.py to store full W3C VC JSON
- **File:** `services/backend/app/api/v1/signing.py`
- **Size:** M (critical fix)
- **Action:** At ~line 147, change `prescription.digital_signature = signature` to `prescription.digital_signature = json.dumps(signed_result["credential"])` (or the full VC dict). This fixes the mismatch where `verification.py` does `json.loads(prescription.digital_signature)` expecting full W3C VC JSON.
- **Acceptance:**
  - After signing, `prescription.digital_signature` contains valid JSON that parses to a W3C VC dict with `proof` field
  - `json.loads(prescription.digital_signature)` succeeds and returns a dict with `credentialSubject`, `proof`, etc.

### TASK-D011: Verify verification.py works with fixed data
- **File:** `services/backend/app/services/verification.py`
- **Size:** S
- **Action:** Review verification.py to ensure it correctly handles the now-valid W3C VC JSON from `digital_signature`. Check all 3 verification steps (signature, trust registry, credential status).
- **Acceptance:** No changes needed if signing fix is correct; verification pipeline accepts properly signed demo credentials

### TASK-D012: Update qr.py for full VC JSON handling
- **File:** `services/backend/app/services/qr.py`
- **Size:** S
- **Action:** Check if `qr.py` reads `digital_signature` and ensure it handles full VC JSON (not just a string signature)
- **Acceptance:** QR generation works with the new `digital_signature` format

---

## Phase 4 — Fix Seed Script

### TASK-D013: Create DID model records for seeded users
- **File:** `services/backend/scripts/seed_demo_data.py`
- **Size:** M
- **Action:** After creating users with `user.did = "did:cheqd:testnet:..."`, also create corresponding `DID` model records in the database. The signing endpoint queries `db.query(DID).filter(DID.user_id == ...)` and fails if no DID record exists.
- **Acceptance:**
  - Each seeded doctor user has a corresponding `DID` model record
  - `db.query(DID).filter(DID.user_id == user.id).first()` returns a valid DID for seeded doctors

### TASK-D014: Generate valid W3C VC JSON signatures in seed script
- **File:** `services/backend/scripts/seed_demo_data.py`
- **Size:** L
- **Action:** Replace `generate_digital_signature()` (returns `sig_{uuid}`) with proper W3C VC JSON generation using the same HMAC-SHA256 signing as `DemoACAPyService`. Import and reuse the signing logic.
- **Acceptance:**
  - Seeded prescriptions have `digital_signature` containing valid JSON
  - `json.loads(prescription.digital_signature)` returns a proper W3C VC dict
  - Verification endpoint accepts seeded prescriptions without errors

---

## Phase 5 — VCService Fallback Fix

### TASK-D015: Update _generate_mock_signature fallback in vc.py
- **File:** `services/backend/app/services/vc.py`
- **Size:** S
- **Action:** The existing `_generate_mock_signature` fallback should use the demo signer when `USE_DEMO=true` to ensure consistency
- **Acceptance:** Any fallback signature generation path also produces valid HMAC signatures in demo mode

---

## Phase 6 — Tests

### TASK-D016: Unit tests for DemoACAPyService
- **File:** `services/backend/app/tests/test_demo_acapy.py` (NEW)
- **Size:** M
- **Action:** Test all DemoACAPyService methods:
  - `create_did()` returns valid did:cheqd:testnet: DID
  - `sign_credential()` → `verify_credential()` round-trip
  - Tampered credential fails verification
  - All mock methods return expected structures
- **Acceptance:** All tests pass, ≥90% coverage of demo_acapy.py

### TASK-D017: Integration test for demo-mode sign→verify
- **File:** `services/backend/app/tests/test_demo_signing_integration.py` (NEW)
- **Size:** M
- **Action:** End-to-end test: create prescription → sign (demo mode) → verify → dispense. Uses test client with `USE_DEMO=true`.
- **Acceptance:** Full flow completes without errors, verification returns `verified: true`

### TASK-D018: Remove xfail markers from verification tests
- **File:** `services/backend/app/tests/test_signing.py`
- **Size:** S
- **Action:** Find and remove `@pytest.mark.xfail` markers on verification tests that were xfailed due to the signing bug
- **Acceptance:** Previously xfailed tests now pass

---

## Phase 7 — Test Fixture Compatibility

### TASK-D019: Update conftest.py for factory pattern
- **File:** `services/backend/app/tests/conftest.py`
- **Size:** S
- **Action:** Update monkeypatching to work with the new factory pattern. Tests should use `DemoACAPyService` by default (set `USE_DEMO=true` in test env).
- **Acceptance:** All existing tests still pass, new tests use factory pattern

---

## Phase 8 — E2E Verification

### TASK-D020: Create test-demo-mode.sh E2E script
- **File:** `scripts/test-demo-mode.sh` (NEW)
- **Size:** M
- **Action:** Bash script that:
  1. Sets `USE_DEMO=true`
  2. Starts backend (no Docker needed)
  3. Seeds demo data
  4. Runs sign→verify→dispense flow via curl
  5. Reports pass/fail
- **Acceptance:** Script runs successfully on a machine with only Python 3.12 and no Docker

### TASK-D021: Run full test suite, fix regressions
- **File:** Various
- **Size:** M
- **Action:** Run `pytest` from `services/backend/`, fix any regressions introduced by the factory pattern or signing fix
- **Acceptance:** `pytest` exits 0 with no new failures

---

## Phase 9 — Documentation

### TASK-D022: Update developer-notes.md
- **File:** `developer-notes.md`
- **Size:** S
- **Action:** Add entry (newest-first) documenting all changes: date, tasks, files changed, notes, next steps
- **Acceptance:** Entry follows existing format

### TASK-D023: Add inline documentation to new files
- **File:** `services/backend/app/services/demo_acapy.py`, `factory.py`
- **Size:** S
- **Action:** Add module docstrings, class docstrings, and inline comments explaining HMAC approach and demo-only nature
- **Acceptance:** New files have clear documentation explaining purpose and limitations

---

## Task Dependencies (Critical Path)

```
D001 → D004 → D005 → D006,D007,D008,D009 → D010 → D011,D012 → D013,D014 → D015 → D016,D017,D018,D019 → D020,D021 → D022,D023
       ↑                                     ↑
   (critical)                             (critical)
```

**Phases can partially overlap:**
- Phase 0 (config) is independent, do first
- Phase 1 (mock service) blocks everything else
- Phase 2 (factory) blocks Phase 3+
- Phase 3 (signing fix) blocks Phase 4+
- Phase 4 (seed fix) blocks Phase 6+ tests
- Phase 6-7 (tests) block Phase 8 (E2E)
- Phase 9 (docs) runs last

---

## Files Summary

### New Files (6)
| File | Purpose |
|------|---------|
| `services/backend/app/services/demo_acapy.py` | Mock ACAPyService with HMAC signing |
| `services/backend/app/services/factory.py` | Service factory (swap real/demo) |
| `services/backend/app/tests/test_demo_acapy.py` | Unit tests for mock service |
| `services/backend/app/tests/test_demo_signing_integration.py` | Integration tests |
| `scripts/test-demo-mode.sh` | E2E verification script |

### Modified Files (11)
| File | Key Changes |
|------|-------------|
| `services/backend/app/main.py` | Add `USE_DEMO` config, startup log |
| `services/backend/app/api/v1/signing.py` | **BUG FIX**: store full VC JSON; use factory |
| `services/backend/app/api/v1/dids.py` | Factory imports |
| `services/backend/app/services/vc.py` | Factory imports, fix fallback |
| `services/backend/app/services/qr.py` | Handle full VC JSON in digital_signature |
| `services/backend/scripts/seed_demo_data.py` | Create DID records, valid W3C VC JSON |
| `services/backend/app/tests/conftest.py` | Factory-compatible monkeypatching |
| `services/backend/app/tests/test_signing.py` | Remove xfail markers |
| `docker-compose.yml` | Add USE_DEMO env var |
| `scripts/start-demo.sh` | Conditional ACA-Py startup |
| `developer-notes.md` | Document changes |
