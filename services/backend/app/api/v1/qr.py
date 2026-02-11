from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.dependencies.auth import get_current_user, get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.models.did import DID
from app.services.qr import QRService


router = APIRouter()


class QRResponse(BaseModel):
    qr_code: str
    data_type: str
    credential_id: str
    url: Optional[str] = None

    class Config:
        from_attributes = True


@router.post(
    "/api/v1/prescriptions/{id}/qr",
    response_model=QRResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_qr_code(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    if current_user.role not in ["doctor", "patient"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Only doctors and patients can generate QR codes",
        )

    if current_user.role == "doctor":
        if prescription.doctor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Not your prescription",
            )
    elif current_user.role == "patient":
        if prescription.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Not your prescription",
            )

    if not prescription.digital_signature or not prescription.credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prescription is not signed yet",
        )

    doctor_did_record = db.query(DID).filter(DID.user_id == prescription.doctor_id).first()
    if not doctor_did_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doctor DID not found",
        )

    patient_did_record = db.query(DID).filter(DID.user_id == prescription.patient_id).first()
    if not patient_did_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient DID not found",
        )

    qr_service = QRService()
    qr_data = qr_service.generate_prescription_qr(
        prescription=prescription,
        doctor_did=doctor_did_record.did_identifier,
        patient_did=patient_did_record.did_identifier,
        credential_id=prescription.credential_id,
    )

    return QRResponse(**qr_data)
