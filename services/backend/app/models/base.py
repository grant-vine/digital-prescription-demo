"""Base model and database configuration."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class TenantMixin:
    """Mixin that adds tenant_id FK to any model for multi-tenancy."""

    @declared_attr
    def tenant_id(cls):
        return Column(
            String(50),
            ForeignKey("tenants.id"),
            nullable=False,
            default="default",
            index=True,
        )
