# API v1 Route Modules

**Parent:** [Backend AGENTS.md](../../../AGENTS.md)

## OVERVIEW

12 FastAPI router modules. Each exports `router = APIRouter()`, registered in `app/main.py`.

## MODULES

| Module | Prefix | Purpose |
|--------|--------|---------|
| `auth.py` | `/api/v1/auth` | Login, register, token refresh, JWT flow |
| `prescriptions.py` | `/api/v1/prescriptions` | CRUD prescriptions, list by role |
| `dids.py` | `/api/v1/dids` | DID creation via ACA-Py, wallet setup |
| `signing.py` | `/api/v1/signing` | Sign prescriptions as W3C VCs |
| `qr.py` | `/api/v1/qr` | QR code generation/parsing |
| `verify.py` | `/api/v1/verify` | Credential verification pipeline |
| `admin.py` | `/api/v1/admin` | Demo reset, admin operations |
| `audit.py` | `/api/v1/audit` | Audit trail queries |
| `time_validation.py` | `/api/v1/time-validation` | Expiry/validity checks |
| `fhir.py` | `/api/v1/fhir` | FHIR R4 resource endpoints |
| `revocation.py` | `/api/v1/revocation` | Credential revocation |
| `demo.py` | `/api/v1/demo` | Demo management, seed data |

## CONVENTIONS

- Every module: `router = APIRouter()` at module level
- Route handlers are `async def`
- Auth-protected routes use `Depends(get_current_user)` from `app.dependencies.auth`
- DB access via `Depends(get_db)` — never create sessions directly
- Response models use Pydantic schemas (inline or from separate schemas file)
- Prefix and tags assigned in `app/main.py`, not in the module

## ADDING A NEW ENDPOINT

1. Create `app/api/v1/my_module.py`
2. Define `router = APIRouter()`
3. Add route handlers with type hints
4. Register in `app/main.py`:
   ```python
   from app.api.v1.my_module import router as my_module_router
   app.include_router(my_module_router, prefix="/api/v1", tags=["my-module"])
   ```
5. Add tests in `app/tests/test_my_module.py`

## ANTI-PATTERNS

- **DO NOT** set prefix in the router itself — set it in `main.py`
- **DO NOT** instantiate services at module level — create in handler or use DI
- **DO NOT** access DB without `Depends(get_db)` injection
