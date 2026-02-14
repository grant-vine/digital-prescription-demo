"""Audit model for immutable compliance logging."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, event
from datetime import datetime

from app.models.base import Base, TenantMixin


class Audit(TenantMixin, Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    event_type = Column(String(100), nullable=False)
    actor_id = Column(Integer, nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)

    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer, nullable=False)

    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

    timestamp = Column(DateTime, default=datetime.now, nullable=False)

    # US-020: Advanced audit fields (nullable for backward compatibility)
    correlation_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    result = Column(String(50), nullable=True, default="success")
    previous_hash = Column(String(256), nullable=True)

    _immutable = False

    def __setattr__(self, key, value):
        if hasattr(self, "_immutable") and self._immutable and key != "_immutable":
            return
        super().__setattr__(key, value)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._immutable = True


@event.listens_for(Audit, "load")
def receive_load(target, context):
    """Set immutable flag when object is loaded from database."""
    target._immutable = True
