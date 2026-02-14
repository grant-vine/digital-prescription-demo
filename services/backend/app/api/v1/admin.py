"""Admin API endpoints for demo environment management.

Implements:
- POST /api/v1/admin/reset-demo - Reset demo environment to clean state
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.models.dispensing import Dispensing
from app.models.audit import Audit

router = APIRouter(prefix="/admin", tags=["admin"])


class ResetDemoResponse(BaseModel):
    """Response schema for reset-demo endpoint."""

    success: bool
    deleted: Dict[str, int]
    reseeded: bool = False
    message: str


@router.post("/reset-demo", response_model=ResetDemoResponse)
async def reset_demo_environment(
    confirm: bool = False,
    reseed: bool = False,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
):
    """Reset demo environment to clean state.

    Clears non-test data (prescriptions, dispensings, audit logs) and optionally
    reseeds with fresh demo data. Requires confirmation to prevent accidental resets.

    Users must have 'doctor' or 'admin' role to execute this endpoint.

    Args:
        confirm: Must be True to execute reset (prevents accidental resets)
        reseed: If True, repopulates database with fresh demo data after clearing
        current_user: Authenticated user with doctor or admin role
        db: Database session

    Returns:
        ResetDemoResponse with deletion counts and operation status

    Raises:
        HTTPException 400: If confirm is False or invalid parameters
        HTTPException 403: If user is not doctor or admin
        HTTPException 401: If not authenticated
        HTTPException 500: If database operation fails

    Example:
        # Reset without reseeding (just clear data)
        curl -X POST "http://localhost:8000/api/v1/admin/reset-demo?confirm=true" \\
          -H "Authorization: Bearer $TOKEN"

        # Reset and reseed with fresh demo data
        curl -X POST "http://localhost:8000/api/v1/admin/reset-demo?confirm=true&reseed=true" \\
          -H "Authorization: Bearer $TOKEN"

        # Will fail without confirm=true
        curl -X POST "http://localhost:8000/api/v1/admin/reset-demo" \\
          -H "Authorization: Bearer $TOKEN"
        # Returns: {"detail": "Must pass confirm=true to reset demo environment"}
    """
    # Validate confirmation parameter
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must pass confirm=true to reset demo environment",
        )

    try:
        prescriptions_count = db.query(Prescription).count()
        dispensings_count = db.query(Dispensing).count()
        audit_logs_count = db.query(Audit).count()

        db.query(Prescription).delete()
        db.query(Dispensing).delete()
        db.query(Audit).delete()
        db.commit()

        deleted_counts = {
            "prescriptions": prescriptions_count,
            "dispensings": dispensings_count,
            "audit_logs": audit_logs_count,
        }

        reseeded = False

        if reseed:
            try:
                from scripts.seed_demo_data import (
                    seed_doctors,
                    seed_patients,
                    seed_pharmacists,
                    seed_prescriptions,
                )

                seed_doctors(db)
                seed_patients(db)
                seed_pharmacists(db)
                seed_prescriptions(db)
                reseeded = True
            except (ImportError, Exception):
                pass

        return ResetDemoResponse(
            success=True,
            deleted=deleted_counts,
            reseeded=reseeded,
            message="Demo environment reset successfully",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo environment: {str(e)}",
        )
