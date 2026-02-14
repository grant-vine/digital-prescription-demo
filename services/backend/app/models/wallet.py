"""Wallet model for storing user wallet information."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, TenantMixin


class Wallet(TenantMixin, Base):
    """ACA-Py wallet record for users.

    Stores wallet_id returned by ACA-Py /wallet/did/create endpoint.
    One wallet per user (enforced via unique constraint on user_id).
    """

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    wallet_id = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to User model
    user = relationship("User", foreign_keys=[user_id])
