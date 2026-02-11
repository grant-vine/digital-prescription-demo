"""Dispensing model for tracking pharmacy dispensing events."""

from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Dispensing(Base):
    __tablename__ = "dispensings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    quantity_dispensed = Column(Integer, nullable=False)
    date_dispensed = Column(DateTime, default=datetime.utcnow, nullable=False)

    verified = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    prescription = relationship("Prescription", back_populates="dispensings")
    pharmacist = relationship("User", foreign_keys=[pharmacist_id], back_populates="dispensings")
