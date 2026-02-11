"""DID model for storing user DIDs."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class DID(Base):
    """Decentralized Identifier record for users.

    Stores DID created on cheqd testnet via ACA-Py.
    One DID per user (enforced via unique constraint on user_id).
    """

    __tablename__ = "dids"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    did_identifier = Column(String(255), nullable=False, unique=True)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to User model
    user = relationship("User", foreign_keys=[user_id])
