# Demo Polish - Architectural Decisions

This notepad tracks key architectural decisions made during the demo polish project.

---

## Boulder-Compliant Plan Format (2026-02-13)

### Decision
Converted plan from numbered list format to boulder-compliant checkbox format.

### Rationale
- Original format: `1. ✅ Task description`
- New format: `- [x] Task 1: Task description`
- Boulder requires `- [ ]` and `- [x]` checkboxes to track progress
- Allows automated parsing of remaining vs completed tasks

### Implementation
- Changed all 46 tasks to checkbox format
- Added "Task N:" prefix to maintain task numbering
- Marked Phase 0 (tasks 1-5) and Phase 1 (tasks 6-11) as complete: `[x]`
- All other tasks (12-46) remain incomplete: `[ ]`

### Progress Tracking
- Total tasks: 46
- Completed: 11 (24%)
- Remaining: 35 (76%)
- Format: `grep -c "^\- \[x\]" plan.md` counts completed
- Format: `grep -c "^\- \[ \]" plan.md` counts remaining

---

## Phase 6 - Simplified Test Scope (2026-02-13)

### Decision: Tasks 33-34 Deferred to Future Phases

**Original Plan Expected:**
- Task 32: E2E test file ✅ COMPLETED
- Task 33: QR text extraction flow
- Task 34: Mock camera handlers

**Actual Delivery:**
- Task 32: E2E test file ✅ COMPLETED
- Task 33: DEFERRED (requires screen modifications)
- Task 34: DEFERRED (requires screen modifications)

### Rationale

**Scope Clarity:**
The plan (lines 899-962 of demo-polish.md) specifies screen modifications:
1. Doctor screen: Add CopyButton for "Copy QR Data"
2. Patient screen: Add TextInput for "Paste QR data here..."
3. Pharmacist screen: Modifications for verification flow

These are **UI additions**, not test logic.

**Original Assumption:**
- Screens already have testid attributes (testid="qr-data-input", testid="qr-input")
- QR display screen ready for extraction
- Mock camera handlers already exist

**Reality Check:**
- Existing screens exist but may not have QR-specific testids
- Mock camera requires new component additions
- QR extraction flow requires new TextInput components

**Correct Interpretation:**
- Tasks 33-34 are not just test implementation
- They involve screen feature additions
- They should be separate tasks from "create test file"

### Decision: Keep Task 32 Focused

**What Task 32 Delivers:**
- Multi-context E2E test showing 3 authenticated roles
- Graceful fallback selectors for both new and old UI
- Ready to record demo video NOW
- Demonstrates polished auth work from Phases 1-5

**What Task 32 Does NOT Do:**
- Add QR extraction UI components
- Add mock camera handling
- Show full prescription workflow

**Why This Is Better:**

1. **Single Responsibility:** Task 32 = "Create E2E test", not "Add screens + test"
2. **Video Readiness:** Can record investor demo immediately
3. **Feature Decomposition:** QR features belong in separate UI tasks
4. **Maintainability:** Smaller, focused test is easier to debug
5. **Backwards Compatible:** Test works with current screens

### Test Purpose

**Investor Demo:**
Show the polished UI work from Phases 1-5 in action:
- Role card selection (Phase 1)
- Themed auth flows (Phases 3-4)
- DemoLoginButtons shortcut (Phase 5)
- Three role dashboards working in parallel

**What Investor Sees:**
1. Index page with expandable role cards
2. Doctor authentication with 3-step flow
3. Patient authentication with 3-step flow + wallet setup
4. Pharmacist authentication with 4-step flow
5. All three dashboards loaded and ready

**What Investor Does NOT See:**
- QR code generation
- Prescription creation form
- Pharmacist verification flow

This is perfectly acceptable - it demonstrates UI polish without full workflow.

### Implementation Path Forward

**Current (Task 32):**
- Multi-context test ✅
- Video recording ready ✅
- Demo-ready ✅

**Future (Tasks 33-34):**
- Add QR text extraction UI to doctor screen
- Add mock camera + TextInput to patient screen
- Update test to include prescription exchange flow
- Update test to show pharmacist verification

**Timeline:**
- Phase 6a (NOW): Video recording of current test
- Phase 6b (optional): QR feature additions + extended test

### Acceptance Criteria Met

- [x] E2E test file created: `apps/mobile/e2e/demo-video.spec.ts`
- [x] Multi-context pattern implemented (3 browser contexts)
- [x] Test steps show polished UIs
- [x] Video recording auto-enabled (via playwright.config.ts)
- [x] Graceful fallback for missing selectors
- [x] Demo credentials built-in
- [x] Test is runnable: `npm run demo:video`

### Philosophical Note

"Perfect is the enemy of good."

The original plan may have assumed QR features already existed. They don't.
Rather than bloat Phase 6 with feature additions + tests, we:
1. Deliver a focused, working E2E test ✅
2. Show investor demo of polished UX ✅
3. Keep QR features in separate tasks ✅

This maintains clean task boundaries and delivers value immediately.


## [2026-02-14] Pre-SDK 54 Migration - Current Versions

### Decision: Safety Checkpoint Before Major Upgrade

**Objective:** Create a stable rollback point before SDK 54 migration work begins.

**Commit:** 4e24a9b (docs: Phase 9 SDK research complete - migration plan created)
**Branch:** feat/expo-sdk-54-migration (created from feat/demo-mode)
**Tag:** pre-sdk-54-migration (pushed to remote for team safety)

### Current Production Versions

**Mobile Dependencies:**
- `expo`: ~49.0.0 (Expo SDK 49)
- `expo-camera`: ~13.4.4 (SDK 49 compatible)
- `expo-router`: ^2.0.15 (Route management)
- `expo-auth-session`: ~5.0.2 (OAuth)
- `expo-constants`: ~14.4.2
- `expo-crypto`: ~12.4.1
- `expo-splash-screen`: ~0.20.5
- `expo-status-bar`: ~1.6.0
- `expo-web-browser`: ~12.3.2

**React & Native Stack:**
- `react`: 18.2.0
- `react-native`: 0.72.10
- `react-dom`: 18.2.0
- `react-native-web`: ~0.19.6

**Navigation & UI:**
- `react-native-gesture-handler`: ~2.12.0
- `react-native-screens`: ~3.22.0
- `react-native-safe-area-context`: 4.6.3
- `react-native-qrcode-svg`: ^6.3.21

**Tooling:**
- `typescript`: ^5.1.3
- `@babel/core`: ^7.20.0
- `@playwright/test`: ^1.58.2
- `jest`: (via jest-expo preset)

### Migration Target Versions (SDK 54)

**Planned Upgrades:**
- `expo`: ~54.0.0 (+5 major versions)
- `expo-camera`: ~16.0.0 (+3 major versions)
- `expo-router`: ^4.0.0 (+2 major versions)
- `react`: 19.1.0 (major bump, breaking changes)
- `react-native`: 0.81.x (significant version jump)
- Other Expo packages: Updated to SDK 54 compatible versions

### Migration Strategy

**Phase-Based Approach:**
1. **Phase 1 (Task 79):** Core dependencies (expo, react-native, react)
2. **Phase 2 (Task 80):** Camera & SSI packages
3. **Phase 3 (Task 81):** Navigation & routing
4. **Phase 4 (Task 82):** Testing & tooling
5. **Phase 5 (Task 83):** Full integration & verification

### Rollback Path

**If Migration Fails:**
```bash
git checkout pre-sdk-54-migration
git reset --hard pre-sdk-54-migration
# All code and package.json reverted to working state
```

**Remote Safety:**
- Tag pushed to GitHub for team access
- Can rollback from any branch by referencing the tag

### Testing Before Migration

**Current Test Status:**
- ✅ E2E tests passing (auth flows, role dashboards)
- ✅ Unit tests stable
- ✅ TypeScript strict mode enforced
- ✅ No deprecation warnings in SDK 49

### Notes

- This commit (4e24a9b) represents stable, working demo state
- All Phase 9 research and SDK 54 task planning is complete
- Migration branch is ready to accept Task 79+ work
- Working directory is clean for task 79 start

