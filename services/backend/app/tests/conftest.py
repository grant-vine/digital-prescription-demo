"""Pytest fixtures for database and application testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import asyncio


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
