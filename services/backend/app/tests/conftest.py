"""Pytest fixtures for database and application testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import asyncio

from app.core.security import hash_password
from app.core.auth import create_access_token, create_refresh_token


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests at session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_url():
    """Use in-memory SQLite for fast tests."""
    return "sqlite:///:memory:"


@pytest.fixture
def test_engine(test_db_url):
    """Create SQLAlchemy engine for tests with in-memory SQLite."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture
def test_session(test_engine) -> Session:
    """Create a new database session for a test.

    Creates all tables before test, drops all after.
    """
    # Import here to avoid circular imports with models
    # Will fail until TASK-007 implements the models
    try:
        from app.models.base import Base

        Base.metadata.create_all(bind=test_engine)
    except ImportError:
        # Models don't exist yet - expected in TDD
        pass

    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    yield session

    session.close()

    # Drop all tables after test
    try:
        from app.models.base import Base

        Base.metadata.drop_all(bind=test_engine)
    except ImportError:
        # Models don't exist yet - expected in TDD
        pass


@pytest.fixture
def doctor_user_data():
    """Sample doctor user data for tests."""
    return {
        "username": "dr_smith",
        "email": "smith@hospital.co.za",
        "password_hash": "hashed_password_123",
        "role": "doctor",
        "full_name": "Dr. John Smith",
        "registration_number": "HPCSA_12345",
    }


@pytest.fixture
def patient_user_data():
    """Sample patient user data for tests."""
    return {
        "username": "john_doe",
        "email": "john@example.com",
        "password_hash": "hashed_password_456",
        "role": "patient",
        "full_name": "John Doe",
        "registration_number": None,
    }


@pytest.fixture
def pharmacist_user_data():
    """Sample pharmacist user data for tests."""
    return {
        "username": "pharmacy_alice",
        "email": "alice@pharmacy.co.za",
        "password_hash": "hashed_password_789",
        "role": "pharmacist",
        "full_name": "Alice Pharmacy",
        "registration_number": "SAPC_67890",
    }


@pytest.fixture
def prescription_data():
    """Sample prescription data for tests."""
    return {
        "patient_id": 1,
        "doctor_id": 1,
        "medication_name": "Amoxicillin",
        "medication_code": "J01CA04",
        "dosage": "500mg",
        "quantity": 21,
        "instructions": "Take one tablet three times daily with food",
        "date_issued": "2026-02-11T10:30:00",
        "date_expires": "2026-05-11T23:59:59",
        "is_repeat": False,
        "repeat_count": 0,
        "digital_signature": "sig_xyz789",
        "credential_id": "cred_abc123",
    }


@pytest.fixture
def dispensing_data():
    """Sample dispensing data for tests."""
    return {
        "prescription_id": 1,
        "pharmacist_id": 1,
        "quantity_dispensed": 21,
        "date_dispensed": "2026-02-11T14:00:00",
        "notes": "Patient counseled on side effects",
        "verified": True,
    }


@pytest.fixture
def audit_event_data():
    """Sample audit event data for tests."""
    return {
        "event_type": "prescription_created",
        "actor_id": 1,
        "actor_role": "doctor",
        "resource_type": "prescription",
        "resource_id": 1,
        "action": "create",
        "details": {"medication": "Amoxicillin", "quantity": 21},
        "ip_address": "127.0.0.1",
    }


@pytest.fixture
def doctor_user(test_session):
    """Create a doctor user in the test database."""
    from app.models.user import User
    
    user = User(
        username="dr_smith",
        email="smith@hospital.co.za",
        password_hash=hash_password("password123"),
        role="doctor",
        full_name="Dr. John Smith",
        registration_number="HPCSA_12345",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def patient_user(test_session):
    """Create a patient user in the test database."""
    from app.models.user import User
    
    user = User(
        username="patient_doe",
        email="patient@example.com",
        password_hash=hash_password("password456"),
        role="patient",
        full_name="John Doe",
        registration_number=None,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def pharmacist_user(test_session):
    """Create a pharmacist user in the test database."""
    from app.models.user import User
    
    user = User(
        username="pharm_jones",
        email="jones@pharmacy.co.za",
        password_hash=hash_password("password789"),
        role="pharmacist",
        full_name="Alice Jones",
        registration_number="SAPC_67890",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def override_get_db(test_session):
    """Override get_db dependency to use test_session."""
    from app.dependencies.auth import get_db
    from app.main import app
    
    def _override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def valid_jwt_token(doctor_user):
    """Generate real JWT token for doctor user."""
    return create_access_token({
        "sub": str(doctor_user.id),
        "username": doctor_user.username,
        "role": str(doctor_user.role)
    })


@pytest.fixture
def valid_patient_jwt_token(patient_user):
    """Generate real JWT token for patient user."""
    return create_access_token({
        "sub": str(patient_user.id),
        "username": patient_user.username,
        "role": str(patient_user.role)
    })


@pytest.fixture
def valid_pharmacist_jwt_token(pharmacist_user):
    """Generate real JWT token for pharmacist user."""
    return create_access_token({
        "sub": str(pharmacist_user.id),
        "username": pharmacist_user.username,
        "role": str(pharmacist_user.role)
    })


@pytest.fixture
def valid_refresh_token(doctor_user):
    """Generate real refresh token for doctor user."""
    return create_refresh_token({
        "sub": str(doctor_user.id),
        "username": doctor_user.username,
        "role": str(doctor_user.role)
    })


@pytest.fixture
def mock_acapy_service(monkeypatch):
    """Mock ACA-Py service for DID/wallet creation tests."""
    import asyncio
    import uuid
    
    class MockACAPyService:
        def __init__(self, admin_url=None):
            self.admin_url = admin_url
        
        async def create_wallet(self):
            unique_id = uuid.uuid4().hex
            return {
                "did": f"did:cheqd:testnet:{unique_id}",
                "verkey": "mock-verification-key",
                "public": True
            }
        
        async def create_did(self, method="cheqd:testnet", public=True):
            unique_id = uuid.uuid4().hex
            return {
                "did": f"did:cheqd:testnet:{unique_id}",
                "verkey": "mock-verification-key",
                "public": public,
                "method": method
            }
        
        async def close(self):
            pass
    
    import app.api.v1.dids as dids_module
    monkeypatch.setattr(dids_module, "ACAPyService", MockACAPyService)
    return MockACAPyService


@pytest.fixture
def doctor_with_wallet(test_session, doctor_user):
    """Create wallet for doctor user (for test_wallet_status_success)."""
    from app.models.wallet import Wallet
    import uuid
    
    wallet = Wallet(
        user_id=doctor_user.id,
        wallet_id=f"wallet-{uuid.uuid4().hex}",
        status="active"
    )
    test_session.add(wallet)
    test_session.commit()
    return doctor_user

