"""Tenant model for multi-tenancy support aligned with DIDx CloudAPI.

Maps to DIDx concepts:
- tenant_id -> DIDx wallet_id (per-tenant identity)
- group_id -> DIDx group_id (organization grouping)
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON
from datetime import datetime

from app.models.base import Base


class Tenant(Base):
    """Multi-tenant organization record.

    Each tenant represents an organization (hospital, pharmacy chain, etc.)
    that operates independently within the system. Aligned with DIDx CloudAPI
    wallet groups for seamless future migration.
    """

    __tablename__ = "tenants"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    group_id = Column(String(50), nullable=True)  # DIDx group_id
    wallet_id = Column(String(255), nullable=True)  # DIDx wallet_id
    settings = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
