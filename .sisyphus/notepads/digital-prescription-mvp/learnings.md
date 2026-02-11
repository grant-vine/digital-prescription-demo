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

