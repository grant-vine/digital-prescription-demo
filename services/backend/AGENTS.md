# Backend Service

**Parent:** [Root AGENTS.md](../../AGENTS.md)

## OVERVIEW

FastAPI REST API (Python 3.12) with SQLAlchemy ORM, ACA-Py SSI integration, JWT auth. Run all commands from `services/backend/` as CWD.

## STRUCTURE

```
services/backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, router registration
│   ├── db.py                 # Session factory (test override via set_test_session)
│   ├── api/v1/               # 12 route modules → see api/v1/AGENTS.md
│   ├── services/             # Business logic layer
│   │   ├── acapy.py          # ACA-Py HTTP client (httpx.AsyncClient)
│   │   ├── vc.py             # W3C Verifiable Credential ops
│   │   ├── qr.py             # QR code generation (qrcode[pil])
│   │   ├── audit.py          # Audit trail logging
│   │   ├── fhir.py           # FHIR R4 resource mapping
│   │   ├── revocation.py     # Credential revocation
│   │   ├── validation.py     # Prescription validation rules
│   │   ├── verification.py   # Credential verification pipeline
│   │   └── dispensing.py     # Dispensing workflow
│   ├── models/               # SQLAlchemy models (Base, User, Prescription, DID, Wallet, Audit, Dispensing, Tenant)
│   ├── core/                 # auth.py (JWT create/decode), security.py (password hashing)
│   ├── dependencies/         # FastAPI dependency injection (auth.py → get_db, get_current_user)
│   └── tests/                # → see tests/AGENTS.md
├── alembic/                  # DB migrations (PostgreSQL target, SQLite for tests)
│   └── versions/             # 3 migration files
├── scripts/seed_demo_data.py # Seeds 3 demo users + sample prescriptions
├── pyproject.toml            # Black config (line-length=100, py312)
├── pytest.ini                # pythonpath=., testpaths=app/tests, --cov=app
├── requirements.txt          # Pinned deps (FastAPI 0.104, SQLAlchemy 2.0, httpx 0.25)
└── Dockerfile                # python:3.12-slim, uvicorn CMD
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new endpoint | `app/api/v1/` | Create module, register in `app/main.py` with `app.include_router()` |
| Add service logic | `app/services/` | Import ACAPyService from `acapy.py` for SSI ops |
| Add/modify model | `app/models/` | Re-export in `models/__init__.py`, run `alembic revision --autogenerate` |
| Add dependency | `app/dependencies/` | FastAPI `Depends()` pattern |
| Add test | `app/tests/test_*.py` | Use fixtures from `conftest.py` |
| Change DB schema | `alembic/versions/` | `alembic revision --autogenerate -m "description"` |

## CONVENTIONS

- **DB sessions**: Production uses `get_db_session()` from `app/db.py`; tests override via `set_test_session()` fixture
- **Model imports**: Always `from app.models import User, Prescription` — never import from individual model files in routes
- **ACAPyService**: Always reads `ACAPY_ADMIN_URL` from env, never hard-coded
- **Router registration**: All routers get `prefix="/api/v1"` and `tags=[...]` in `main.py`
- **Async**: Services use `httpx.AsyncClient`; route handlers are `async def`
- **Multi-tenancy**: All models mix in `TenantMixin`; `tenant_id` scopes queries

## ANTI-PATTERNS

- **DO NOT** create SessionLocal directly in routes — use dependency injection
- **DO NOT** import from `app.models.user` in routes — use `app.models` re-exports
- **DO NOT** hard-code `http://acapy:8001` — read from `ACAPY_ADMIN_URL`
- **DO NOT** use `sync` HTTP clients for ACA-Py calls — `httpx.AsyncClient` only

## COMMANDS

```bash
# From services/backend/
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
pytest                                    # All tests + coverage
pytest app/tests/test_auth.py -v          # Single file
pytest -k "test_create_prescription"      # Pattern match
alembic upgrade head                      # Apply migrations
alembic revision --autogenerate -m "msg"  # New migration
python scripts/seed_demo_data.py          # Seed demo data
```
