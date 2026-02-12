"""Audit API endpoints for advanced audit trail and compliance reporting.

Implements US-020 (Advanced Audit Trail & Reporting) with:
- Event listing and retrieval
- Advanced search with filtering
- Prescription, security, and compliance reports
- Dashboard statistics
- Audit log export
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.dependencies.auth import require_role, get_current_user, get_db
from app.models.user import User
from app.services.audit import AuditService

router = APIRouter(prefix="/admin", tags=["audit"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class AdvancedSearchRequest(BaseModel):
    """Request body for advanced audit log search."""
    query_text: Optional[str] = Field(None, description="Text to search across fields")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ExportRequest(BaseModel):
    """Request body for audit log export."""
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply")
    format: str = Field("json", pattern="^(json|csv)$", description="Export format")


class DateRangeFilter(BaseModel):
    """Date range filter for reports."""
    start_date: datetime = Field(..., description="Report period start")
    end_date: datetime = Field(..., description="Report period end")
    actor_id: Optional[int] = Field(None, description="Filter by actor ID")
    resource_id: Optional[int] = Field(None, description="Filter by resource ID")


# ============================================================================
# Audit Event Endpoints
# ============================================================================

@router.get("/audit/events")
async def list_audit_events(
    actor_id: Optional[int] = Query(None, description="Filter by actor ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """List audit events with optional filtering.

    Returns paginated list of audit log entries matching the specified filters.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    filters = {}
    if actor_id:
        filters["actor_id"] = actor_id
    if event_type:
        filters["event_type"] = event_type
    if action:
        filters["action"] = action
    if resource_type:
        filters["resource_type"] = resource_type
    if start_date:
        filters["start_date"] = start_date.isoformat()
    if end_date:
        filters["end_date"] = end_date.isoformat()

    result = service.query_logs(
        filters=filters if filters else None,
        limit=limit,
        offset=offset,
        order_by="timestamp DESC",
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Query failed"))

    return result


@router.get("/audit/events/{event_id}")
async def get_audit_event(
    event_id: int,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get a single audit event by ID.

    Returns detailed information about a specific audit log entry.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)
    result = service.get_event_by_id(event_id)

    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result["error"])
        raise HTTPException(status_code=500, detail=result.get("error", "Query failed"))

    return result


@router.post("/audit/search")
async def advanced_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Advanced search across audit logs.

    Performs full-text-like search across event types, actions, and details
    with additional filtering capabilities.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    result = service.advanced_search(
        query_text=request.query_text,
        filters=request.filters,
        limit=request.limit,
        offset=request.offset,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

    return result


# ============================================================================
# Report Endpoints
# ============================================================================

@router.get("/reports/prescriptions")
async def get_prescription_report(
    start_date: datetime = Query(..., description="Report period start"),
    end_date: datetime = Query(..., description="Report period end"),
    actor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    resource_id: Optional[int] = Query(None, description="Filter by prescription ID"),
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate prescription activity report.

    Returns aggregated statistics about prescription events including
    creation, signing, dispensing, and revocation counts.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    filters = {}
    if actor_id:
        filters["actor_id"] = actor_id
    if resource_id:
        filters["resource_id"] = resource_id

    result = service.generate_prescription_report(
        start_date=start_date,
        end_date=end_date,
        filters=filters if filters else None,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))

    return result


@router.get("/reports/security")
async def get_security_report(
    start_date: datetime = Query(..., description="Report period start"),
    end_date: datetime = Query(..., description="Report period end"),
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate security audit report.

    Returns security metrics including failed login attempts,
    unauthorized access attempts, and failed verifications.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    result = service.generate_security_report(
        start_date=start_date,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))

    return result


@router.get("/reports/compliance")
async def get_compliance_report(
    start_date: datetime = Query(..., description="Report period start"),
    end_date: datetime = Query(..., description="Report period end"),
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate regulatory compliance report.

    Returns POPIA and HPCSA compliance metrics including data access events,
    consent tracking, and prescription revocation records.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    result = service.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))

    return result


# ============================================================================
# Dashboard and Export Endpoints
# ============================================================================

@router.get("/dashboard/compliance")
async def get_compliance_dashboard(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get compliance dashboard statistics.

    Returns summary statistics for the compliance dashboard including
    prescription counts, security metrics, and audit log health.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    result = service.get_dashboard_stats(period_days=period_days)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Stats retrieval failed"))

    return result


@router.post("/reports/export")
async def export_audit_logs(
    request: ExportRequest,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Export audit logs in JSON or CSV format.

    Exports audit logs matching the specified filters in the requested format.
    Requires doctor or admin role.
    """
    service = AuditService(db_session=db)

    result = service.export_logs(
        filters=request.filters,
        format=request.format,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Export failed"))

    return result
