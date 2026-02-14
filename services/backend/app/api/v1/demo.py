"""Demo Management API endpoints.

US-019: Demo Preparation & Test Data
Provides endpoints for managing demo data in the system.

Endpoints:
- POST /api/v1/admin/demo/seed    — Run the seed process
- POST /api/v1/admin/demo/reset   — Reset demo data (delete all, reseed)
- GET  /api/v1/admin/demo/status  — Show demo data statistics
- GET  /api/v1/admin/demo/scenarios — List available demo scenarios
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.models.prescription import Prescription
from app.models.dispensing import Dispensing
from app.models.audit import Audit
from app.db import get_db_session

router = APIRouter(prefix="/admin/demo", tags=["demo"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class DemoStatsResponse(BaseModel):
    """Response schema for demo statistics."""
    users: Dict[str, int] = Field(..., description="User counts by role")
    prescriptions: Dict[str, int] = Field(..., description="Prescription counts by status")
    dispensings: int = Field(..., description="Total dispensing records")
    audit_logs: int = Field(..., description="Total audit log entries")


class DemoScenario(BaseModel):
    """Demo scenario description."""
    id: int = Field(..., description="Scenario ID")
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Detailed scenario description")
    prescriptions: List[str] = Field(..., description="Related prescription identifiers")


class DemoScenariosResponse(BaseModel):
    """Response schema for demo scenarios list."""
    scenarios: List[DemoScenario] = Field(..., description="Available demo scenarios")
    total: int = Field(..., description="Total number of scenarios")


class SeedDemoResponse(BaseModel):
    """Response schema for seed endpoint."""
    success: bool = Field(..., description="Whether seeding was successful")
    users_created: Dict[str, int] = Field(..., description="Number of users created by role")
    prescriptions_created: int = Field(..., description="Number of prescriptions created")
    message: str = Field(..., description="Status message")


class ResetDemoResponse(BaseModel):
    """Response schema for reset endpoint."""
    success: bool = Field(..., description="Whether reset was successful")
    deleted: Dict[str, int] = Field(..., description="Counts of deleted records")
    reseeded: bool = Field(..., description="Whether data was reseeded after reset")
    message: str = Field(..., description="Status message")


# =============================================================================
# Demo Scenarios Data
# =============================================================================

DEMO_SCENARIOS = [
    DemoScenario(
        id=1,
        name="Happy Path",
        description="Complete workflow: Doctor creates prescription → digitally signs → patient receives → shares with pharmacist → verification → dispensing",
        prescriptions=["happy_path_rx"],
    ),
    DemoScenario(
        id=2,
        name="Multi-Medication",
        description="Patient with 3+ concurrent medications prescribed together for complex condition management",
        prescriptions=["multi_med_1", "multi_med_2", "multi_med_3"],
    ),
    DemoScenario(
        id=3,
        name="Repeat Prescription",
        description="Chronic medication with repeat authorization, partially dispensed over multiple pharmacy visits",
        prescriptions=["repeat_partial_rx"],
    ),
    DemoScenario(
        id=4,
        name="Expired Prescription",
        description="Prescription that has passed its expiration date, demonstrating time-based validation",
        prescriptions=["expired_rx_1", "expired_rx_2", "expired_rx_3"],
    ),
    DemoScenario(
        id=5,
        name="Revoked Prescription",
        description="Prescription revoked by doctor due to prescribing error, with audit trail documentation",
        prescriptions=["revoked_rx_1", "revoked_rx_2"],
    ),
    DemoScenario(
        id=6,
        name="Doctor Verification",
        description="Demonstrates valid vs invalid HPCSA registration verification scenarios",
        prescriptions=["verification_rx"],
    ),
]


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/seed", response_model=SeedDemoResponse)
async def seed_demo_data(
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> SeedDemoResponse:
    """Seed demo data into the database.
    
    Creates demo users (doctors, patients, pharmacists), prescriptions in various states,
    audit trail entries, and dispensing records. Requires doctor or admin role.
    
    Args:
        current_user: Authenticated user with doctor or admin role
        db: Database session
        
    Returns:
        SeedDemoResponse with counts of created records
        
    Raises:
        HTTPException 403: If user is not doctor or admin
        HTTPException 500: If seeding fails
    """
    tenant_id = getattr(current_user, '_jwt_tenant_id', 'default')
    
    try:
        # Import seed functions
        from scripts.seed_demo_data import (
            seed_doctors,
            seed_patients,
            seed_pharmacists,
            seed_prescriptions_with_states,
            ensure_default_tenant,
        )
        
        # Ensure tenant exists
        ensure_default_tenant(db)
        
        # Get current counts before seeding
        doctors_before = db.query(User).filter_by(role="doctor", tenant_id=tenant_id).count()
        patients_before = db.query(User).filter_by(role="patient", tenant_id=tenant_id).count()
        pharmacists_before = db.query(User).filter_by(role="pharmacist", tenant_id=tenant_id).count()
        rx_before = db.query(Prescription).filter_by(tenant_id=tenant_id).count()
        
        # Seed users
        doctors = seed_doctors(db, count=5, tenant_id=tenant_id)
        patients = seed_patients(db, count=10, tenant_id=tenant_id)
        pharmacists = seed_pharmacists(db, count=3, tenant_id=tenant_id)
        
        # Seed prescriptions if we have users
        prescriptions_created = 0
        if doctors and patients and pharmacists:
            prescriptions_by_state = seed_prescriptions_with_states(
                db, doctors, patients, pharmacists, tenant_id
            )
            prescriptions_created = sum(len(rx_list) for rx_list in prescriptions_by_state.values())
        
        db.commit()
        
        # Calculate created counts
        doctors_after = db.query(User).filter_by(role="doctor", tenant_id=tenant_id).count()
        patients_after = db.query(User).filter_by(role="patient", tenant_id=tenant_id).count()
        pharmacists_after = db.query(User).filter_by(role="pharmacist", tenant_id=tenant_id).count()
        rx_after = db.query(Prescription).filter_by(tenant_id=tenant_id).count()
        
        return SeedDemoResponse(
            success=True,
            users_created={
                "doctors": doctors_after - doctors_before,
                "patients": patients_after - patients_before,
                "pharmacists": pharmacists_after - pharmacists_before,
            },
            prescriptions_created=rx_after - rx_before,
            message="Demo data seeded successfully",
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed demo data: {str(e)}",
        )


@router.post("/reset", response_model=ResetDemoResponse)
async def reset_demo_data(
    confirm: bool = False,
    reseed: bool = False,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> ResetDemoResponse:
    """Reset demo data to clean state.
    
    Clears all demo data (prescriptions, dispensings, audit logs, users) and optionally
    reseeds with fresh data. Requires confirmation to prevent accidental resets.
    
    Args:
        confirm: Must be True to execute reset
        reseed: If True, repopulates database after clearing
        current_user: Authenticated user with doctor or admin role
        db: Database session
        
    Returns:
        ResetDemoResponse with deletion counts and reseed status
        
    Raises:
        HTTPException 400: If confirm is False
        HTTPException 403: If user is not doctor or admin
        HTTPException 500: If reset fails
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must pass confirm=true to reset demo data",
        )
    
    tenant_id = getattr(current_user, '_jwt_tenant_id', 'default')
    
    try:
        # Count records before deletion (excluding current user)
        prescriptions_count = db.query(Prescription).filter_by(tenant_id=tenant_id).count()
        dispensings_count = db.query(Dispensing).filter_by(tenant_id=tenant_id).count()
        audit_logs_count = db.query(Audit).filter_by(tenant_id=tenant_id).count()
        # Don't count the current user - they will not be deleted
        users_count = db.query(User).filter_by(tenant_id=tenant_id).filter(User.id != current_user.id).count()
        
        # Delete in order to respect foreign keys
        db.query(Dispensing).filter_by(tenant_id=tenant_id).delete()
        db.query(Audit).filter_by(tenant_id=tenant_id).delete()
        db.query(Prescription).filter_by(tenant_id=tenant_id).delete()
        # Delete all users except the current authenticated user
        db.query(User).filter_by(tenant_id=tenant_id).filter(User.id != current_user.id).delete()
        db.commit()
        
        deleted_counts = {
            "prescriptions": prescriptions_count,
            "dispensings": dispensings_count,
            "audit_logs": audit_logs_count,
            "users": users_count,
        }
        
        reseeded = False
        if reseed:
            # Call seed endpoint logic
            try:
                from scripts.seed_demo_data import (
                    seed_doctors,
                    seed_patients,
                    seed_pharmacists,
                    seed_prescriptions_with_states,
                    ensure_default_tenant,
                )
                
                ensure_default_tenant(db)
                
                doctors = seed_doctors(db, count=5, tenant_id=tenant_id)
                patients = seed_patients(db, count=10, tenant_id=tenant_id)
                pharmacists = seed_pharmacists(db, count=3, tenant_id=tenant_id)
                
                if doctors and patients and pharmacists:
                    seed_prescriptions_with_states(db, doctors, patients, pharmacists, tenant_id)
                
                db.commit()
                reseeded = True
            except Exception:
                db.rollback()
                reseeded = False
        
        return ResetDemoResponse(
            success=True,
            deleted=deleted_counts,
            reseeded=reseeded,
            message="Demo data reset successfully" + (" and reseeded" if reseeded else ""),
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo data: {str(e)}",
        )


@router.get("/status", response_model=DemoStatsResponse)
async def get_demo_status(
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> DemoStatsResponse:
    """Get demo data statistics.
    
    Returns counts of users, prescriptions by status, dispensings, and audit logs.
    
    Args:
        current_user: Authenticated user with doctor or admin role
        db: Database session
        
    Returns:
        DemoStatsResponse with current demo data statistics
        
    Raises:
        HTTPException 403: If user is not doctor or admin
    """
    tenant_id = getattr(current_user, '_jwt_tenant_id', 'default')
    
    users = {
        "doctors": db.query(User).filter_by(role="doctor", tenant_id=tenant_id).count(),
        "patients": db.query(User).filter_by(role="patient", tenant_id=tenant_id).count(),
        "pharmacists": db.query(User).filter_by(role="pharmacist", tenant_id=tenant_id).count(),
        "total": db.query(User).filter_by(tenant_id=tenant_id).count(),
    }
    prescriptions = {
        "total": db.query(Prescription).filter_by(tenant_id=tenant_id).count(),
        "draft": db.query(Prescription).filter_by(status="DRAFT", tenant_id=tenant_id).count(),
        "active": db.query(Prescription).filter_by(status="ACTIVE", tenant_id=tenant_id).count(),
        "expired": db.query(Prescription).filter_by(status="EXPIRED", tenant_id=tenant_id).count(),
        "revoked": db.query(Prescription).filter_by(status="REVOKED", tenant_id=tenant_id).count(),
        "dispensed": db.query(Prescription).filter_by(status="DISPENSED", tenant_id=tenant_id).count(),
    }
    dispensings = db.query(Dispensing).filter_by(tenant_id=tenant_id).count()
    audit_logs = db.query(Audit).filter_by(tenant_id=tenant_id).count()
    
    return DemoStatsResponse(
        users=users,
        prescriptions=prescriptions,
        dispensings=dispensings,
        audit_logs=audit_logs,
    )


@router.get("/scenarios", response_model=DemoScenariosResponse)
async def get_demo_scenarios(
    current_user: User = Depends(require_role(["doctor", "admin"])),
) -> DemoScenariosResponse:
    """List available demo scenarios.
    
    Returns descriptions of all 6 demo scenarios available in the system.
    
    Args:
        current_user: Authenticated user with doctor or admin role
        
    Returns:
        DemoScenariosResponse with list of scenarios
        
    Raises:
        HTTPException 403: If user is not doctor or admin
    """
    return DemoScenariosResponse(
        scenarios=DEMO_SCENARIOS,
        total=len(DEMO_SCENARIOS),
    )
