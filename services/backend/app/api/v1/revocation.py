"""Revocation API endpoints for advanced prescription revocation workflows.

Implements US-021 (Advanced Revocation Workflows):
- POST /prescriptions/{id}/revoke          → single revocation
- POST /prescriptions/bulk-revoke          → bulk revocation with preview mode
- POST /prescriptions/schedule-revoke      → schedule future revocation
- PUT  /prescriptions/scheduled/{id}       → modify scheduled revocation
- DELETE /prescriptions/scheduled/{id}     → cancel scheduled revocation
- GET  /prescriptions/revocations          → list revocations with filters
- GET  /prescriptions/revocations/{id}     → single revocation details
- POST /prescriptions/revoke-rollback/{id} → rollback bulk operation
- GET  /admin/revocations/dashboard        → dashboard stats
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.models.audit import Audit
from app.services.revocation import RevocationService

router = APIRouter()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class RevokeRequest(BaseModel):
    """Schema for single prescription revocation."""
    reason: str = Field(..., description="Revocation reason")
    notes: Optional[str] = Field(None, description="Optional notes")


class BulkRevokeRequest(BaseModel):
    """Schema for bulk revocation request."""
    filter_criteria: Dict[str, Any] = Field(..., description="Filter criteria for prescriptions")
    reason: str = Field(..., description="Revocation reason")
    preview_only: bool = Field(False, description="If true, only preview without executing")


class ScheduleRevokeRequest(BaseModel):
    """Schema for scheduling a future revocation."""
    prescription_id: int = Field(..., description="ID of prescription to revoke")
    scheduled_at: str = Field(..., description="ISO datetime when to revoke")
    reason: str = Field(..., description="Revocation reason")


class RevocationRuleRequest(BaseModel):
    """Schema for creating a conditional revocation rule."""
    trigger_type: str = Field(..., description="Type of trigger (expiry, repeat_exhausted, time_based)")
    conditions: Dict[str, Any] = Field(..., description="Conditions for the rule")
    reason: str = Field(..., description="Default reason when rule triggers")


class RevocationResponse(BaseModel):
    """Schema for revocation response."""
    success: bool
    prescription_id: int
    revocation_id: Optional[int] = None
    timestamp: str
    reason: str


class BulkRevokeResponse(BaseModel):
    """Schema for bulk revocation response."""
    bulk_operation_id: str
    preview: bool
    affected_count: int
    prescription_ids: List[int]
    timestamp: str


class ScheduledRevocationResponse(BaseModel):
    """Schema for scheduled revocation response."""
    schedule_id: str
    prescription_id: int
    scheduled_at: str
    reason: str
    status: str


class RollbackResponse(BaseModel):
    """Schema for rollback response."""
    success: bool
    restored_count: int
    prescription_ids: List[int]
    timestamp: str


class ImpactAnalysisResponse(BaseModel):
    """Schema for impact analysis response."""
    prescription_id: int
    can_revoke: bool
    impact_level: str
    affected_entities: Dict[str, bool]
    warnings: List[str]
    recommendations: List[str]


class DashboardResponse(BaseModel):
    """Schema for dashboard response."""
    period: Dict[str, Any]
    summary: Dict[str, int]
    by_reason: Dict[str, int]
    by_actor: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# ============================================================================
# SINGLE REVOCATION
# ============================================================================


@router.post(
    "/prescriptions/{prescription_id}/revoke",
    response_model=RevocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a single prescription"
)
def revoke_prescription(
    prescription_id: int,
    request: RevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Revoke a single prescription.
    
    - **prescription_id**: ID of the prescription to revoke
    - **reason**: Reason for revocation (prescribing_error, patient_request, etc.)
    - **notes**: Optional additional context
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        result = service.revoke_prescription(
            prescription_id=prescription_id,
            revoked_by_user_id=current_user.id,
            reason=request.reason,
            notes=request.notes
        )
        return RevocationResponse(
            success=result["success"],
            prescription_id=result["prescription_id"],
            revocation_id=result.get("revocation_id"),
            timestamp=result["timestamp"],
            reason=result["reason"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# BULK REVOCATION
# ============================================================================


@router.post(
    "/prescriptions/bulk-revoke",
    response_model=BulkRevokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk revoke prescriptions matching filter criteria"
)
def bulk_revoke(
    request: BulkRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Bulk revoke prescriptions matching filter criteria.
    
    Maximum 100 prescriptions per operation. Use preview_only=True to see what would be revoked.
    
    - **filter_criteria**: Dict with optional keys:
      - patient_id: Filter by patient
      - status: Filter by status (default: ACTIVE)
      - medication_name: Filter by medication name (partial match)
      - date_range: Dict with start/end ISO datetimes
    - **reason**: Reason for revocation
    - **preview_only**: If true, only returns count without revoking
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        result = service.revoke_bulk(
            filter_criteria=request.filter_criteria,
            reason=request.reason,
            actor_id=current_user.id,
            preview_only=request.preview_only
        )
        return BulkRevokeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/prescriptions/revoke-rollback/{bulk_operation_id}",
    response_model=RollbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Rollback a bulk revocation (within 24 hours)"
)
def rollback_bulk_revocation(
    bulk_operation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Rollback a bulk revocation operation within 24 hours.
    
    - **bulk_operation_id**: UUID of the bulk operation to rollback
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        result = service.rollback_bulk(
            bulk_operation_id=bulk_operation_id,
            actor_id=current_user.id
        )
        return RollbackResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# SCHEDULED REVOCATION
# ============================================================================


@router.post(
    "/prescriptions/schedule-revoke",
    response_model=ScheduledRevocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a future revocation"
)
def schedule_revocation(
    request: ScheduleRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Schedule a prescription revocation for future execution.
    
    - **prescription_id**: ID of prescription to revoke
    - **scheduled_at**: ISO datetime when revocation should occur
    - **reason**: Reason for revocation
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        # Parse the scheduled_at datetime
        scheduled_at = datetime.fromisoformat(request.scheduled_at.replace("Z", "+00:00"))
        
        result = service.schedule_revocation(
            prescription_id=request.prescription_id,
            scheduled_at=scheduled_at,
            reason=request.reason,
            actor_id=current_user.id
        )
        return ScheduledRevocationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid datetime format: {str(e)}")


@router.delete(
    "/prescriptions/scheduled/{schedule_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Cancel a scheduled revocation"
)
def cancel_scheduled_revocation(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Cancel a scheduled revocation.
    
    - **schedule_id**: UUID of the scheduled revocation to cancel
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        result = service.cancel_scheduled_revocation(
            schedule_id=schedule_id,
            actor_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/prescriptions/revocations/scheduled",
    response_model=List[Dict[str, Any]],
    summary="List scheduled revocations"
)
def list_scheduled_revocations(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Get list of scheduled revocations with optional filters."""
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    filters = {}
    if patient_id:
        filters["patient_id"] = patient_id
    if status:
        filters["status"] = status
    
    result = service.get_scheduled_revocations(filters=filters)
    return result


# ============================================================================
# LIST AND DETAIL ENDPOINTS
# ============================================================================


@router.get(
    "/prescriptions/revocations",
    response_model=List[Dict[str, Any]],
    summary="List revocation audit entries"
)
def list_revocations(
    prescription_id: Optional[int] = Query(None, description="Filter by prescription ID"),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Get list of revocation events with optional filters.
    
    Returns audit log entries for revocation events.
    """
    from app.db import get_db_session
    from app.models.audit import Audit
    from datetime import datetime, timedelta, timezone
    
    session = db or get_db_session()
    
    SAST = timezone(timedelta(hours=2))
    start_date = datetime.now(SAST) - timedelta(days=days)
    
    query = session.query(Audit).filter(
        Audit.timestamp >= start_date,
        Audit.event_type.in_([
            "prescription_revocation",
            "bulk_revocation_executed",
            "bulk_revocation_preview",
            "revocation_scheduled",
            "revocation_schedule_cancelled",
            "revocation_executed",
            "bulk_revocation_rollback"
        ])
    )
    
    if prescription_id:
        query = query.filter(Audit.resource_id == prescription_id)
    
    audits = query.order_by(Audit.timestamp.desc()).all()
    
    result = []
    for audit in audits:
        details = audit.details or {}
        entry = {
            "id": audit.id,
            "event_type": audit.event_type,
            "actor_id": audit.actor_id,
            "actor_role": audit.actor_role,
            "resource_id": audit.resource_id,
            "resource_type": audit.resource_type,
            "timestamp": audit.timestamp.isoformat(),
            "details": details,
            "correlation_id": audit.correlation_id
        }
        result.append(entry)
    
    return result


@router.get(
    "/prescriptions/revocations/{revocation_id}",
    response_model=Dict[str, Any],
    summary="Get single revocation details"
)
def get_revocation_details(
    revocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Get details of a single revocation audit entry."""
    from app.db import get_db_session
    from app.models.audit import Audit
    
    session = db or get_db_session()
    
    audit = session.query(Audit).filter_by(id=revocation_id).first()
    
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revocation not found")
    
    # Verify it's a revocation event
    if audit.event_type not in [
        "prescription_revocation",
        "bulk_revocation_executed",
        "revocation_scheduled",
        "revocation_executed"
    ]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a revocation event")
    
    details = audit.details or {}
    
    return {
        "id": audit.id,
        "event_type": audit.event_type,
        "actor_id": audit.actor_id,
        "actor_role": audit.actor_role,
        "resource_id": audit.resource_id,
        "resource_type": audit.resource_type,
        "timestamp": audit.timestamp.isoformat(),
        "details": details,
        "correlation_id": audit.correlation_id
    }


# ============================================================================
# CONDITIONAL RULES
# ============================================================================


@router.post(
    "/prescriptions/revocation-rules",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a conditional revocation rule"
)
def create_revocation_rule(
    request: RevocationRuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Create a conditional revocation rule.
    
    - **trigger_type**: Type of trigger (expiry, repeat_exhausted, time_based)
    - **conditions**: Dict with conditions for the rule
    - **reason**: Default reason when rule triggers
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    try:
        result = service.create_revocation_rule(
            trigger_type=request.trigger_type,
            conditions=request.conditions,
            reason=request.reason,
            actor_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/prescriptions/{prescription_id}/evaluate-rules",
    response_model=List[Dict[str, Any]],
    summary="Evaluate revocation rules for a prescription"
)
def evaluate_revocation_rules(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Evaluate all revocation rules against a prescription.
    
    Returns list of rules that would trigger for this prescription.
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    result = service.evaluate_revocation_rules(prescription_id=prescription_id)
    return result


# ============================================================================
# IMPACT ANALYSIS
# ============================================================================


@router.get(
    "/prescriptions/{prescription_id}/revoke-impact",
    response_model=ImpactAnalysisResponse,
    summary="Analyze revocation impact for a prescription"
)
def analyze_revocation_impact(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Analyze the impact of revoking a prescription.
    
    Returns impact assessment including warnings and recommendations.
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    result = service.analyze_revocation_impact(prescription_id=prescription_id)
    return ImpactAnalysisResponse(**result)


@router.post(
    "/prescriptions/bulk-revoke-impact",
    response_model=Dict[str, Any],
    summary="Analyze bulk revocation impact"
)
def analyze_bulk_impact(
    filter_criteria: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    """Analyze the impact of a bulk revocation operation.
    
    - **filter_criteria**: Same format as bulk-revoke endpoint
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    result = service.analyze_bulk_impact(filter_criteria=filter_criteria)
    return result


# ============================================================================
# DASHBOARD
# ============================================================================


@router.get(
    "/admin/revocations/dashboard",
    response_model=DashboardResponse,
    summary="Get revocation dashboard statistics"
)
def get_revocation_dashboard(
    days: int = Query(30, description="Number of days to include", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get revocation dashboard statistics.
    
    Aggregates data from audit logs to provide comprehensive statistics.
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    result = service.get_revocation_dashboard(days=days)
    return DashboardResponse(**result)


# ============================================================================
# BACKGROUND JOB ENDPOINT
# ============================================================================


@router.post(
    "/admin/revocations/process-due",
    response_model=Dict[str, Any],
    summary="Process due scheduled revocations (admin only)"
)
def process_due_revocations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Process scheduled revocations that are due.
    
    This endpoint is typically called by a background job/cron.
    """
    service = RevocationService(db_session=db, tenant_id=getattr(current_user, "tenant_id", "default"))
    
    result = service.process_due_revocations()
    return result
