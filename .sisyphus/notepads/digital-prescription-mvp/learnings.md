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


## [2026-02-11] TASK-002: FastAPI Project Scaffold

### Directory Structure Created
✓ `services/backend/app/` - Main application package
✓ `services/backend/app/core/` - Configuration, security, database modules (placeholder)
✓ `services/backend/app/models/` - SQLAlchemy model definitions (placeholder)
✓ `services/backend/app/services/` - Business logic services (placeholder)
✓ `services/backend/app/api/` - API routes container
✓ `services/backend/app/api/v1/` - Versioned API v1 endpoints (placeholder)
✓ `services/backend/app/tests/` - Test suite (inherited from TASK-000)

### Files Created
✓ `services/backend/app/__init__.py` - Package initialization with version
✓ `services/backend/app/main.py` - FastAPI app entry point with /health and / endpoints
✓ `services/backend/app/core/__init__.py` - Core module placeholder
✓ `services/backend/app/models/__init__.py` - Models module placeholder
✓ `services/backend/app/services/__init__.py` - Services module placeholder
✓ `services/backend/app/api/__init__.py` - API module placeholder
✓ `services/backend/app/api/v1/__init__.py` - V1 API module placeholder
✓ `services/backend/requirements.txt` - 13 Python packages
✓ `services/backend/pytest.ini` - pytest configuration with coverage
✓ `services/backend/.flake8` - Flake8 linting rules
✓ `services/backend/pyproject.toml` - Black formatter configuration
✓ `services/backend/Dockerfile` - Python 3.12 slim multi-stage build

### FastAPI Application Implementation
- **Entry Point:** `app/main.py` with FastAPI(title="Digital Prescription API", version="0.1.0")
- **CORS Middleware:** Enabled for cross-origin requests
- **Health Endpoint:** `GET /health` returns `{"status": "healthy"}`
- **Root Endpoint:** `GET /` returns API metadata with available endpoints
- **Structure:** Clean layered architecture (core, models, services, api/v1)

### Python Dependencies (requirements.txt)
**Core:**
- fastapi==0.104.1
- uvicorn[standard]==0.24.0

**Database:**
- sqlalchemy==2.0.23
- psycopg2-binary==2.9.9

**Data Validation:**
- pydantic==2.5.0
- pydantic-settings==2.1.0

**Configuration:**
- python-dotenv==1.0.0

**Testing:**
- pytest==7.4.3
- pytest-cov==4.1.0
- pytest-asyncio==0.21.1

**Code Quality:**
- flake8==6.1.0
- black==23.12.0

**Utilities:**
- PyYAML==6.0.1

### Configuration Files

**pytest.ini:**
```ini
[pytest]
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=app --cov-report=term-missing
asyncio_mode = auto
```

**.flake8:**
```ini
[flake8]
max-line-length = 100
exclude = __pycache__,venv,.venv,build,dist,.git
ignore = E203,W503
```

**pyproject.toml:**
```toml
[tool.black]
line-length = 100
target-version = ['py312']
```

**Dockerfile:**
- Base image: python:3.12-slim
- Workdir: /app
- Install system deps: gcc (for psycopg2)
- Copy requirements → pip install
- Copy app code
- Expose: 8000
- CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000

### Validation Results
```
→ Checking Backend Requirements...
✓ services/backend/requirements.txt is valid (13 packages)

→ Checking Pytest Config...
✓ services/backend/pytest.ini is valid
```

- ✓ All Python files compile successfully (py_compile check)
- ✓ All config files valid (INI and TOML parsing)
- ✓ FastAPI app structure ready for import (not installed yet per spec)

### Design Decisions
1. **Minimal FastAPI app:** Only /health and / endpoints implemented (future endpoints in TASK-003+)
2. **Async by default:** pytest asyncio_mode enabled for async endpoint testing
3. **Coverage tracking:** pytest configured with --cov=app for MVP validation
4. **No DB models yet:** Placeholder modules created, actual models in TASK-007
5. **No authentication yet:** Placeholder core module, auth in TASK-010
6. **No dependencies installed:** Per spec, pip install deferred to TASK-003 (Docker build)
7. **Layered architecture:** core/, models/, services/, api/v1/ enable clean separation of concerns

### Dependencies Satisfied
- ✓ TASK-001: Monorepo structure (inherited)
- Prepares for TASK-003: Database models
- Prepares for TASK-007: Prescription models and endpoints
- Prepares for TASK-010: Authentication integration

### Next Steps
1. TASK-003: Mobile app React Native + Expo setup
2. TASK-004: Docker Compose infrastructure
3. TASK-005: Database initialization with PostgreSQL
4. TASK-006: Scaffold tests validation (should PASS now)


## [2026-02-11] TASK-004: Docker Compose Development Stack

### File Created
✓ `docker-compose.yml` at project root

### Services Configured

**PostgreSQL 15-alpine:**
- Port: 5432
- Credentials: postgres/postgres
- Database: prescriptions
- Memory limit: 512MB
- Health check: pg_isready every 10s
- Volume: postgres_data (persistent)

**Redis 7-alpine:**
- Port: 6379
- Memory limit: 256MB
- Health check: redis-cli ping every 10s
- No volume (ephemeral cache)

**ACA-Py 0.10.1:**
- Admin API port: 8001
- Inbound transport port: 8002
- Wallet: askar with insecure_key_for_dev
- Memory limit: 1GB
- Health check: curl to /status endpoint every 15s
- Note: --auto-provision enabled for dev simplicity

**FastAPI Backend:**
- Port: 8000
- Depends on: db, redis (both healthy)
- Memory limit: 512MB
- Reads from Dockerfile at services/backend/Dockerfile
- Environment variables:
  - DATABASE_URL: postgresql://postgres:postgres@db:5432/prescriptions
  - REDIS_URL: redis://redis:6379/0
  - ACAPY_ADMIN_URL: http://acapy:8001

### Configuration Details

**Container Naming:**
- rx_postgres (consistent naming for debugging)
- rx_redis
- rx_acapy
- rx_backend

**Networking:**
- Network name: prescription_network
- Driver: bridge (default, supports inter-service communication)
- All services on same network (db accessible as "db" from backend)

**Health Checks:**
- PostgreSQL: pg_isready check (standard Postgres health)
- Redis: redis-cli ping (simple connection test)
- ACA-Py: HTTP /status endpoint (application-level health)
- Backend: Implicit (depends_on with healthy conditions)

**Memory Limits (M1 8GB optimization):**
- PostgreSQL: 512MB (database workloads are efficient)
- Redis: 256MB (in-memory, but prescriptions are small)
- ACA-Py: 1GB (SSI operations consume resources)
- Backend: 512MB (FastAPI is lightweight)
- **Total reserved:** ~2.2GB (leaves 5.8GB for OS, browser, etc.)

### Validation Results

✓ YAML syntax validated with python3 -c "import yaml; yaml.safe_load()"
✓ Structure verification script passed all checks:
  - ✓ Docker Compose check PASS
  - ✓ 7/7 validation checks passed
  - ✓ All services configured correctly

### Design Decisions

1. **ACA-Py insecure wallet key:** Development-only simplification. Production uses real key management.
2. **Health checks with dependencies:** Backend waits for db+redis healthy before starting (service_healthy condition).
3. **Alpine images:** Smaller base images reduce startup time and memory footprint on M1.
4. **Environment variables in compose:** Database credentials in compose for dev simplicity. Production uses secrets management.
5. **No environment file yet:** .env file creation deferred to future tasks (TASK-005).
6. **Container networking:** All services on bridge network named prescription_network (explicit name aids debugging).

### Testing Approach

**Not yet executed (per spec):**
- docker-compose up (services not ready to run)
- docker build (no dependencies installed)

**Will be tested in TASK-005 (Docker Stack Validation)**

### Dependencies Satisfied

- ✓ TASK-001: Monorepo structure (inherited)
- ✓ TASK-002: Backend Dockerfile exists (services/backend/Dockerfile)
- Prepares for TASK-005: Docker Stack Validation (docker-compose up + health checks)
- Prepares for TASK-006: Environment configuration (.env setup)

### Next Steps

1. TASK-003: Mobile app React Native + Expo setup (parallel task)
2. TASK-005: Docker Stack Validation (bring stack up and verify health)
3. TASK-006: Environment configuration and secrets management


## [2026-02-11] TASK-003: Expo React Native Project Initialized

### Directory Structure Created
✓ `src/app/` - Expo Router file-based routing root
✓ `src/app/(doctor)/` - Doctor role layout group
✓ `src/app/(patient)/` - Patient role layout group
✓ `src/app/(pharmacist)/` - Pharmacist role layout group
✓ `src/components/theme/` - Theme configuration files
✓ `src/components/common/` - Shared component placeholders
✓ `src/hooks/` - Custom React hooks (placeholder)
✓ `src/services/` - API/service layer (placeholder)
✓ `src/store/` - State management (placeholder)

### Files Created
**Config Files:**
✓ `package.json` - Dependencies: Expo 49, React Native 0.72.6, TypeScript 5.1, Jest 29, ESLint 8
✓ `app.json` - Expo app configuration with camera plugin
✓ `tsconfig.json` - TypeScript strict mode, path alias @/* → src/*
✓ `jest.config.js` - Jest Expo preset, collectCoverageFrom src/**/*.{ts,tsx}
✓ `.eslintrc.js` - TypeScript + React + React Hooks ESLint plugins

**App Files:**
✓ `src/app/index.tsx` - Role selector screen with 3 buttons (Doctor/Patient/Pharmacist)
  - Conditional styling by selected role
  - Interactive role selection with color indicators
✓ `src/app/(doctor)/_layout.tsx` - Doctor role Stack Navigator, header color #2563EB
✓ `src/app/(patient)/_layout.tsx` - Patient role Stack Navigator, header color #0891B2
✓ `src/app/(pharmacist)/_layout.tsx` - Pharmacist role Stack Navigator, header color #059669

**Theme Files:**
✓ `src/components/theme/DoctorTheme.ts` - Royal Blue (#2563EB) clinical theme, 8 color vars, spacing, typography
✓ `src/components/theme/PatientTheme.ts` - Cyan (#0891B2) personal health theme
✓ `src/components/theme/PharmacistTheme.ts` - Green (#059669) dispensing theme

### Validation Results
```
Passed: 7/7
  ✓ PASS: Directories
  ✓ PASS: Root Files
  ✓ PASS: Docker Compose
  ✓ PASS: Backend Requirements
  ✓ PASS: Mobile Package.json (start, android, ios, test, lint, type-check)
  ✓ PASS: Pytest Config
  ✓ PASS: Jest Config
```

### Design Decisions
1. **Expo Router v2:** Modern file-based routing with layout groups for role separation
2. **Stack Navigators:** Each role group uses Stack for future nested screens (e.g., doctor/create, doctor/view)
3. **TypeScript strict:** noEmit ensures compilation checks without output, strict: true for type safety
4. **Jest Expo preset:** jest-expo handles React Native JSX and Metro bundler specifics
5. **Theme as TypeScript constants:** Exported types allow theming context to be added in TASK-022
6. **Role selector:** Touchable buttons with dynamic styling preview selected role before navigation

### Path Aliases
- `@/*` → `src/*` configured in tsconfig.json allows clean imports: `import { DoctorTheme } from '@/components/theme'`

### Script Definitions
- `npm start` → `expo start` (default)
- `npm run android` → `expo start --android` (physical/emulator)
- `npm run ios` → `expo start --ios` (physical/simulator)
- `npm test` → `jest` (unit tests)
- `npm run lint` → `eslint . --ext .ts,.tsx` (code quality)
- `npm run type-check` → `tsc --noEmit` (type compilation)

### Dependencies for Future Tasks
- TASK-022: Implement theming context/provider using DoctorTheme/PatientTheme/PharmacistTheme constants
- TASK-024: Add React Navigation with routing from role selector to role-specific dashboards
- TASK-026: Add QR code scanner component in src/components/common/QRScanner.tsx
- TASK-028: Add prescription list component in src/components/common/PrescriptionList.tsx
- TASK-029: Setup testing utilities and mock data for Jest tests

### Next Steps
1. TASK-004: Create Docker infrastructure (docker-compose.yml with PostgreSQL, Redis, ACA-Py)
2. TASK-005: Create services/backend/app/main.py FastAPI scaffold
3. TASK-022: Implement theming context and apply to role-specific screens
