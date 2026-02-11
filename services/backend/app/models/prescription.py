"""Prescription model with FHIR R4 fields."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    medication_name = Column(String(255), nullable=False)
    medication_code = Column(String(50), nullable=True)
    dosage = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)

    date_issued = Column(DateTime, default=datetime.utcnow, nullable=True)
    date_expires = Column(DateTime, nullable=True)

    is_repeat = Column(Boolean, default=False, nullable=False)
    repeat_count = Column(Integer, default=0, nullable=False)

    digital_signature = Column(Text, nullable=True)
    credential_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="prescriptions")
    dispensings = relationship("Dispensing", back_populates="prescription")
