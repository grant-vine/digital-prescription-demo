"""Database session management.

Provides a singleton session factory and context-aware session access.
Tests can override via pytest fixtures.
"""

from typing import Optional
from sqlalchemy.orm import Session

_test_session: Optional[Session] = None


def set_test_session(session: Session) -> None:
    """Set the test session (for pytest fixtures to use)."""
    global _test_session
    _test_session = session


def get_db_session() -> Session:
    """Get database session.
    
    Returns test session if set (for tests), otherwise creates production session.
    For now, returns test session or raises error if none available.
    """
    global _test_session
    if _test_session is not None:
        return _test_session
    
    raise RuntimeError(
        "No database session available. "
        "In tests, configure via set_test_session(). "
        "In production, implement SessionLocal factory."
    )


def reset_test_session() -> None:
    """Reset test session (for cleanup)."""
    global _test_session
    _test_session = None
