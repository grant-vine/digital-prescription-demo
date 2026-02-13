# Digital Prescription Demo

**Generated:** 2026-02-12  
**Commit:** 4f84277  
**Branch:** before-cheqd (detached) | master, milestone/mvp-complete

## OVERVIEW

Tech demo: digital prescription system using SSI (Self-Sovereign Identity). Doctors sign prescriptions as W3C Verifiable Credentials, patients store in mobile wallets, pharmacists verify and dispense. Python/FastAPI backend + React Native/Expo mobile + ACA-Py SSI agent.

## STRUCTURE

```
rxdistribute/
├── services/backend/         # FastAPI API + SQLAlchemy + ACA-Py integration
│   ├── app/api/v1/           # 12 route modules (auth, prescriptions, dids, signing, qr, verify...)
│   ├── app/services/         # Business logic (acapy, vc, qr, audit, fhir, revocation, validation)
│   ├── app/models/           # SQLAlchemy models (User, Prescription, Dispensing, Audit, DID, Wallet)
│   ├── app/tests/            # 20 pytest test files, conftest with fixture hierarchy
│   ├── alembic/              # DB migrations (PostgreSQL)
│   └── scripts/              # seed_demo_data.py
├── apps/mobile/              # React Native + Expo Router (TypeScript)
│   ├── src/app/(doctor)/     # Doctor screens: auth, dashboard, prescriptions/*
│   ├── src/app/(patient)/    # Patient screens: auth, wallet, scan, prescriptions/*
│   ├── src/app/(pharmacist)/ # Pharmacist screens: auth, verify, prescriptions/[id]/dispense
│   ├── src/components/       # Shared: qr/ (QRDisplay, QRScanner), theme/ (per-role themes)
│   ├── src/services/         # API client (axios)
│   └── e2e/                  # E2E specs per role
├── user-stories/             # 25 markdown stories (001-025), README index
├── scripts/                  # start-demo.sh, verify-structure.py
├── .sisyphus/                # Execution plan + notepads (73 tasks, boulder.json)
├── docker-compose.yml        # PostgreSQL, Redis, ACA-Py (OWF 1.4.0), backend
└── implementation-plan-v3.md # Current plan (v1, v2 are archived)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `services/backend/app/api/v1/` | Register in `app/main.py` |
| Add business logic | `services/backend/app/services/` | SSI ops in `acapy.py`, credential ops in `vc.py` |
| Add/modify DB model | `services/backend/app/models/` | Re-export in `__init__.py`, create alembic migration |
| Backend tests | `services/backend/app/tests/` | Fixtures in `conftest.py`, in-memory SQLite |
| Mobile screen | `apps/mobile/src/app/(role)/` | Expo Router file-based routing, `_layout.tsx` per group |
| Mobile shared component | `apps/mobile/src/components/` | `qr/` and `theme/` subdirs |
| Mobile API calls | `apps/mobile/src/services/api.ts` | Single axios client module |
| User stories | `user-stories/###-slug.md` | Format template in `user-stories/AGENTS.md` |
| Run demo | `./scripts/start-demo.sh` | Checks prereqs, starts Docker, seeds data, launches everything |
| Execution plan | `.sisyphus/plans/digital-prescription-mvp.md` | 73 tasks, boulder tracking |

## CONVENTIONS

- **Monorepo** with npm workspaces: `apps/*`, `packages/*`
- **Backend** runs from `services/backend/` as CWD (not project root)
- **Python**: Black formatter (line-length=100, py312), pytest with `--cov=app`
- **Mobile**: TypeScript strict mode, `@/*` path alias to `src/*`, jest-expo preset
- **Commit format**: Conventional Commits (`feat(scope):`, `fix(scope):`, `docs:`)
- **SSI provider**: Swappable via `SSI_PROVIDER` env var (acapy-local | didx-cloud | mock)
- **Role theming**: Doctor=#2563EB, Patient=#0891B2, Pharmacist=#059669
- **Tests colocated** with source (mobile: `*.test.tsx` next to `*.tsx`), backend in `app/tests/`

## ANTI-PATTERNS

- **DO NOT** use `as any` or `@ts-ignore` in mobile code — strict TS is enforced
- **DO NOT** commit `.env`, `test.db`, or `venv/` (gitignored)
- **DO NOT** hard-code ACA-Py URLs — always use `ACAPY_ADMIN_URL` env var
- **DO NOT** import models directly in API routes — use `app.models` re-exports
- **DO NOT** skip developer-notes.md entry when completing work
- **CORS** is `allow_origins=["*"]` — change for production

## COMMANDS

```bash
# Infrastructure
docker-compose up -d db redis acapy     # Start SSI stack
docker-compose logs -f acapy            # Debug ACA-Py

# Backend (from services/backend/)
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
pytest                                   # All tests + coverage
pytest app/tests/test_auth.py           # Single test file

# Mobile (from apps/mobile/)
npx expo start --clear                  # Dev server
npm test                                # Jest tests
npm test -- e2e/doctor.spec.ts          # E2E per role

# Full demo (from project root)
./scripts/start-demo.sh                 # One-command startup
```

## MILESTONES

| Branch/Tag | Status |
|-----------|--------|
| `milestone/ready-to-dev` | Planning complete |
| `milestone/mvp-complete` | MVP done (94/94 tasks) |
| `milestone/demo-opt-product` | Demo optimization |
| `v1.0.0-mvp` | Tag: all 16 core stories |

Agents must update `developer-notes.md` (newest-first log) with: date, tasks, duration, files changed, notes, next steps.

## CHILD AGENTS.md

- `services/backend/AGENTS.md` — Backend API, models, services, DB
- `services/backend/app/api/v1/AGENTS.md` — Route module conventions
- `services/backend/app/tests/AGENTS.md` — Test fixture hierarchy, patterns
- `apps/mobile/AGENTS.md` — Mobile app structure, theming, testing
- `user-stories/AGENTS.md` — Story format, naming, cross-references
