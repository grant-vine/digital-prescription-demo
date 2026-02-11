"""Prescription CRUD endpoints for digital prescription management.

Implements:
- POST /api/v1/prescriptions - Create prescription (doctor only)
- GET /api/v1/prescriptions/{id} - Get prescription by ID (role-filtered)
- PUT /api/v1/prescriptions/{id} - Update draft prescription (doctor only)
- GET /api/v1/prescriptions - List prescriptions (role-filtered)
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.models.prescription import Prescription

router = APIRouter()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class PrescriptionCreate(BaseModel):
    """Schema for creating a new prescription."""

    patient_id: int
    medication_name: str
    medication_code: str
    dosage: str
    quantity: int = Field(gt=0)
    instructions: str
    date_expires: str
    is_repeat: bool = False
    repeat_count: int = 0

    @validator("medication_name")
    def medication_name_not_empty(cls, v):
        """Validate medication name is not empty."""
        if not v or not v.strip():
            raise ValueError("Medication name cannot be empty")
        return v

    @validator("date_expires")
    def date_expires_in_future(cls, v):
        """Validate expiration date is in the future."""
        try:
            expires = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise ValueError("Invalid date format")

        if expires < datetime.utcnow():
            raise ValueError("Expiration date must be in the future")

        return v

    @validator("repeat_count")
    def repeat_count_requires_is_repeat(cls, v, values):
        """Validate repeat_count consistency with is_repeat."""
        if v > 0 and not values.get("is_repeat", False):
            raise ValueError("repeat_count requires is_repeat=True")
        return v


class PrescriptionUpdate(BaseModel):
    """Schema for updating a draft prescription."""

    medication_name: Optional[str] = None
    medication_code: Optional[str] = None
    dosage: Optional[str] = None
    quantity: Optional[int] = None
    instructions: Optional[str] = None
    date_expires: Optional[str] = None
    is_repeat: Optional[bool] = None
    repeat_count: Optional[int] = None


class PrescriptionResponse(BaseModel):
    """Schema for prescription response."""

    id: int
    doctor_id: int
    patient_id: int
    medication_name: str
    medication_code: Optional[str]
    dosage: str
    quantity: int
    instructions: Optional[str]
    date_issued: datetime
    date_expires: datetime
    is_repeat: bool
    repeat_count: int
    digital_signature: Optional[str]
    credential_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrescriptionListResponse(BaseModel):
    """Schema for paginated prescription list response."""

    items: List[PrescriptionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED
)
async def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(require_role(["doctor"])),
    db: Session = Depends(get_db),
):
    """Create a new prescription (doctor only).

    Args:
        data: Prescription creation data
        current_user: Authenticated doctor user
        db: Database session

    Returns:
        Created prescription

    Raises:
        HTTPException 404: Patient not found
        HTTPException 422: Invalid prescription data
        HTTPException 403: User is not a doctor
        HTTPException 401: Not authenticated
    """
    patient = db.query(User).filter(User.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    try:
        expires = datetime.fromisoformat(data.date_expires.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format"
        )

    prescription = Prescription(
        doctor_id=current_user.id,
        patient_id=data.patient_id,
        medication_name=data.medication_name,
        medication_code=data.medication_code,
        dosage=data.dosage,
        quantity=data.quantity,
        instructions=data.instructions,
        date_issued=datetime.utcnow(),
        date_expires=expires,
        is_repeat=data.is_repeat,
        repeat_count=data.repeat_count,
    )

    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return prescription


@router.get("/prescriptions/{id}", response_model=PrescriptionResponse)
async def get_prescription(
    id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get prescription by ID with role-based access control.

    Access rules:
    - Doctor: Can view their own prescriptions
    - Patient: Can view prescriptions for them
    - Pharmacist: Can view any prescription (for verification)

    Args:
        id: Prescription ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Prescription details

    Raises:
        HTTPException 404: Prescription not found
        HTTPException 403: Access denied
        HTTPException 401: Not authenticated
    """
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    user_role = str(current_user.role)

    if user_role == "doctor" and prescription.doctor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif user_role == "patient" and prescription.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return prescription


@router.put("/prescriptions/{id}", response_model=PrescriptionResponse)
async def update_prescription(
    id: int,
    data: PrescriptionUpdate,
    current_user: User = Depends(require_role(["doctor"])),
    db: Session = Depends(get_db),
):
    """Update a draft prescription (doctor only, unsigned prescriptions only).

    Args:
        id: Prescription ID
        data: Updated prescription data
        current_user: Authenticated doctor user
        db: Database session

    Returns:
        Updated prescription

    Raises:
        HTTPException 404: Prescription not found
        HTTPException 403: Access denied or prescription is signed
        HTTPException 401: Not authenticated
    """
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

    if prescription.doctor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if prescription.digital_signature:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify signed prescriptions"
        )

    if data.medication_name is not None:
        prescription.medication_name = data.medication_name
    if data.medication_code is not None:
        prescription.medication_code = data.medication_code
    if data.dosage is not None:
        prescription.dosage = data.dosage
    if data.quantity is not None:
        prescription.quantity = data.quantity
    if data.instructions is not None:
        prescription.instructions = data.instructions
    if data.date_expires is not None:
        try:
            expires = datetime.fromisoformat(data.date_expires.replace("Z", "+00:00"))
            prescription.date_expires = expires
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format"
            )
    if data.is_repeat is not None:
        prescription.is_repeat = data.is_repeat
    if data.repeat_count is not None:
        prescription.repeat_count = data.repeat_count

    prescription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(prescription)

    return prescription


@router.get("/prescriptions", response_model=PrescriptionListResponse)
async def list_prescriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10,
):
    """List prescriptions filtered by user role.

    Filtering rules:
    - Doctor: Sees prescriptions they created
    - Patient: Sees prescriptions for them
    - Pharmacist: Sees all prescriptions (for verification)

    Args:
        current_user: Authenticated user
        db: Database session
        page: Page number (default: 1)
        page_size: Items per page (default: 10)

    Returns:
        Paginated list of prescriptions

    Raises:
        HTTPException 401: Not authenticated
    """
    user_role = str(current_user.role)

    query = db.query(Prescription)

    if user_role == "doctor":
        query = query.filter(Prescription.doctor_id == current_user.id)
    elif user_role == "patient":
        query = query.filter(Prescription.patient_id == current_user.id)

    total = query.count()

    offset = (page - 1) * page_size
    prescriptions = query.offset(offset).limit(page_size).all()

    return PrescriptionListResponse(
        items=prescriptions, total=total, page=page, page_size=page_size
    )
