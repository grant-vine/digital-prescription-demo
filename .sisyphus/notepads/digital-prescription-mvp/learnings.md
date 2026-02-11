# Learnings - digital-prescription-mvp

## Conventions & Patterns

_AI agents append findings here (never overwrite)_

---

## [2026-02-11] TASK-000: Infrastructure Validation Tests

### Created Files
- `scripts/verify-structure.py` - Python CLI validation script
- `services/backend/app/tests/test_structure.py` - pytest test suite
- `apps/mobile/src/tests/structure.test.ts` - Jest TypeScript test suite

### Validation Checks Implemented

**Python Script (verify-structure.py):**
- Directory existence checks (apps/, services/, infrastructure/, packages/)
- Root-level file existence (docker-compose.yml, README.md, .gitignore)
- Docker Compose YAML syntax validation using yaml.safe_load()
- Backend requirements.txt parsing (validates Python package specs)
- Mobile package.json structure (validates required scripts: start, test, lint, type-check)
- pytest.ini INI format validation
- jest.config.js existence check
- Clear pass/fail output with exit codes (0=success, 1=failure)

**pytest Test Suite (test_structure.py):**
- Backend directory structure validation (app/, models/, services/, api/, tests/)
- requirements.txt parsing and format validation
- pytest.ini validity checks

**Jest Test Suite (structure.test.ts):**
- Mobile src/ directory structure (app/, components/, hooks/, services/, store/, tests/)
- package.json validity and required scripts
- Configuration file existence (jest.config.js, tsconfig.json)
- ESLint configuration detection

### Design Decisions
1. **Separate validation approaches:** Python script for CLI execution, pytest for backend automation, Jest for mobile automation
2. **Graceful error messages:** Clear pass/fail indicators to guide developers
3. **TDD structure:** Tests written BEFORE directories/files created—designed to FAIL until TASK-001
4. **Minimal dependencies:** verify-structure.py requires only yaml (for Docker Compose validation)

### Execution Commands
- `python scripts/verify-structure.py` (requires PyYAML)
- `pytest services/backend/app/tests/test_structure.py` (requires pytest)
- `npm test -- apps/mobile/src/tests/structure.test.ts` (requires Jest)
- Script exits with code 0 when all checks pass, code 1 on failure


## [2026-02-11] TASK-001: Monorepo Structure Initialized

### Directories Created
✓ apps/
✓ apps/mobile/
✓ services/
✓ services/backend/
✓ infrastructure/
✓ infrastructure/acapy/
✓ packages/

### Files Created/Updated
✓ package.json (root workspace config)
✓ .gitignore (updated with .pyo, .expo-shared/, missing Thumbs.db added)

### Validation Status
- Ran: `python3 scripts/verify-structure.py`
- Status: EXPECTED FAILURES (subdirectory configs not created yet)
  - ✓ PASS: Directories exist (1/7)
  - ✗ FAIL: Root Files (docker-compose.yml created in TASK-004)
  - ✗ FAIL: Docker Compose (created in TASK-004)
  - ✗ FAIL: Backend Requirements (created in TASK-002)
  - ✗ FAIL: Mobile Package.json (created in TASK-003)
  - ✗ FAIL: Pytest Config (created in TASK-002)
  - ✗ FAIL: Jest Config (created in TASK-003)

### Root package.json Configuration
```json
{
  "name": "digital-prescription-demo",
  "version": "0.1.0",
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "engines": {"node": ">=18.0.0", "npm": ">=9.0.0"}
}
```
- Workspace monorepo setup enables shared dependencies
- Stub scripts for development workflow
- Version 0.1.0 matches MVP phase

### .gitignore Updates
- Added `.pyo` (Python compiled files)
- Added `.expo-shared/` (Expo build artifacts)
- Added `Thumbs.db` (Windows explorer metadata)
- Cleaned up redundant entries
- Preserved `!.sisyphus/plans/` exception rule

### Dependencies for Future Tasks
- TASK-002 (Backend) needs: `services/backend/requirements.txt`, `services/backend/pytest.ini`, FastAPI setup
- TASK-003 (Mobile) needs: `apps/mobile/package.json`, `apps/mobile/jest.config.js`, Expo setup
- TASK-004 (Infrastructure) needs: `docker-compose.yml`, ACA-Py config in `infrastructure/acapy/`

### Next Steps
1. TASK-002: Backend API scaffolding (FastAPI, PostgreSQL, pytest)
2. TASK-003: Mobile app initialization (React Native, Expo, Jest)
3. TASK-004: Docker infrastructure (docker-compose, ACA-Py)

