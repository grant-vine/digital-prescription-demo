# Backend Tests

**Parent:** [Backend AGENTS.md](../../../AGENTS.md)

## OVERVIEW

20 pytest files. In-memory SQLite, fixture hierarchy in `conftest.py`. Coverage enforced via `--cov=app`.

## FIXTURE HIERARCHY

```
conftest.py
├── event_loop          (session scope) — async test support
├── test_db_url         → "sqlite:///:memory:"
├── test_engine         → SQLAlchemy engine with StaticPool
├── test_session        → Creates tables, seeds default Tenant, sets global test session
│   ├── doctor_user     → User(role="doctor", HPCSA_12345)
│   ├── patient_user    → User(role="patient")
│   ├── pharmacist_user → User(role="pharmacist", SAPC_67890)
│   ├── doctor_with_did → doctor_user + DID record
│   ├── patient_with_did → patient_user + DID record
│   ├── doctor_with_wallet → doctor_user + Wallet record
│   └── override_get_db → FastAPI dependency override
├── valid_jwt_token     → JWT for doctor_user
├── valid_patient_jwt_token → JWT for patient_user
├── valid_pharmacist_jwt_token → JWT for pharmacist_user
├── mock_acapy_service  → Mocks ACAPyService in dids module
├── mock_acapy_signing_service → Mocks in acapy + vc modules
└── async_client        → httpx.AsyncClient with ASGITransport
```

## TEST PATTERNS

- **DB isolation**: Each test gets fresh `test_session`; tables created/dropped per test
- **Multi-tenancy**: Default tenant auto-created in `test_session` fixture
- **Global session**: `set_test_session()` / `reset_test_session()` for services that read `app.db`
- **ACA-Py mocking**: `monkeypatch.setattr` on service modules, not HTTP interception
- **JWT tokens**: Real tokens via `create_access_token()` — not mocked auth
- **Async tests**: `pytest-asyncio` with `asyncio_mode = auto`

## NAMING

- Files: `test_*.py` matching the module under test
- Functions: `test_<action>_<scenario>` (e.g., `test_create_prescription_success`)
- Classes: `Test<Feature>` (optional grouping)

## ADDING A TEST

1. Create `app/tests/test_feature.py`
2. Import fixtures by name (pytest auto-discovers from `conftest.py`)
3. Use `test_session` for DB, `valid_jwt_token` for auth, `mock_acapy_service` for SSI
4. For async endpoint tests, use `async_client` fixture

```python
def test_example(test_session, doctor_user, valid_jwt_token):
    # test_session has tables + default tenant
    # doctor_user is committed to test_session
    # valid_jwt_token is a real JWT for doctor_user
    pass
```

## ANTI-PATTERNS

- **DO NOT** create DB engines in test files — use `test_session` fixture
- **DO NOT** mock JWT verification — use real tokens from fixtures
- **DO NOT** skip `test_session` for DB tests — it handles tenant seeding
