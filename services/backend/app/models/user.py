"""User model for doctors, patients, and pharmacists."""

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import enum

from app.models.base import Base, TenantMixin


class UserRole(enum.Enum):
    doctor = "doctor"
    patient = "patient"
    pharmacist = "pharmacist"


class User(TenantMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('doctor', 'patient', 'pharmacist')", name="check_user_role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=True, default=lambda: None)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=True)
    registration_number = Column(String(100), nullable=True)
    did = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    prescriptions = relationship(
        "Prescription", back_populates="doctor", foreign_keys="Prescription.doctor_id"
    )
    dispensings = relationship(
        "Dispensing", back_populates="pharmacist", foreign_keys="Dispensing.pharmacist_id"
    )

    @validates("role")
    def validate_role(self, key, value):
        if isinstance(value, UserRole):
            return value.value
        return value

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if name == "role" and isinstance(attr, str):

            class RoleProxy:
                def __init__(self, val):
                    self._val = val

                def __eq__(self, other):
                    if isinstance(other, str):
                        return self._val == other
                    return False

                def __str__(self):
                    return self._val

                def __repr__(self):
                    return f"<UserRole.{self._val}: '{self._val}'>"

            return RoleProxy(attr)
        return attr
