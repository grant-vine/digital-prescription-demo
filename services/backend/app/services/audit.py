"""Audit logging service for immutable compliance trail.

Implements US-016 (Audit Trail & Compliance Logging) with:
- Event logging for prescription lifecycle
- Query interface with filtering and pagination
- Immutable storage (cannot update/delete logs after creation)
- SAST timezone (UTC+2) for South African compliance
- Atomic database transactions

All 20 tests from TASK-063 must PASS.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.audit import Audit


class AuditService:
    """Service for audit trail logging with immutable persistence."""

    # SAST timezone (UTC+2)
    SAST = timezone(timedelta(hours=2))

    def __init__(self, db_session: Optional[Session] = None, tenant_id: str = "default"):
        """Initialize with optional database session.

        Args:
            db_session: SQLAlchemy session for database operations.
                       If None, service will use injected session per call.
            tenant_id: Tenant identifier for multi-tenancy scoping.
        """
        self.db = db_session
        self.tenant_id = tenant_id

    def log_event(
        self,
        event_type: str,
        actor_id: int,
        actor_role: str,
        action: str,
        resource_type: str,
        resource_id: int,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log an event to the audit trail.

        Creates an immutable audit log entry in the database with all event details.
        All timestamps are recorded in SAST (UTC+2) timezone for South African compliance.

        Args:
            event_type: Event type (e.g., "prescription.created", "prescription.signed")
            actor_id: User ID who performed action
            actor_role: Role of actor ("doctor", "pharmacist", "patient")
            action: Action taken ("create", "sign", "dispense", "verify", "revoke", etc.)
            resource_type: Type of resource ("prescription", "user", etc.)
            resource_id: ID of resource acted upon
            details: Optional JSON details (medication info, signature details, etc.)
            ip_address: Optional IP address of actor

        Returns:
            {
                "success": True,
                "log_id": <int>,
                "event_type": <str>,
                "action": <str>
            }

        Raises:
            Exception: If database operation fails (wrapped in try/except for graceful handling)
        """
        from app.db import get_db_session

        session = self.db or get_db_session()

        try:
            # Create audit log entry with SAST timestamp
            log = Audit(
                event_type=event_type,
                actor_id=actor_id,
                actor_role=actor_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                timestamp=datetime.now(tz=self.SAST),
                tenant_id=self.tenant_id,
            )

            # Atomic transaction
            session.add(log)
            session.commit()
            session.refresh(log)

            return {
                "success": True,
                "log_id": log.id,
                "event_type": log.event_type,
                "action": log.action,
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}

    def query_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "timestamp DESC",
    ) -> Dict[str, Any]:
        """Query audit logs with filtering and pagination.

        Retrieves audit logs from database with optional filtering by:
        - actor_id: User who performed the action
        - event_type: Type of event (e.g., "prescription.created")
        - action: Action performed (e.g., "create", "sign", "dispense")
        - resource_type: Type of resource affected
        - start_date: Date range start (ISO format string)
        - end_date: Date range end (ISO format string)

        All date filters use SAST timezone. Multiple filters combine with AND logic.

        Args:
            filters: Dictionary of optional filters
            limit: Maximum number of logs to return (default 100)
            offset: Number of logs to skip (for pagination)
            order_by: Ordering clause ("timestamp DESC" for most recent first, etc.)

        Returns:
            {
                "success": True,
                "logs": [
                    {
                        "id": <int>,
                        "event_type": <str>,
                        "actor_id": <int>,
                        "actor_role": <str>,
                        "action": <str>,
                        "resource_type": <str>,
                        "resource_id": <int>,
                        "details": <dict>,
                        "ip_address": <str|null>,
                        "timestamp": <ISO string>
                    },
                    ...
                ],
                "total_count": <int>
            }
        """
        from app.db import get_db_session

        session = self.db or get_db_session()

        try:
            query = session.query(Audit)

            # Apply filters
            if filters:
                if "actor_id" in filters:
                    query = query.filter(Audit.actor_id == filters["actor_id"])
                if "event_type" in filters:
                    query = query.filter(Audit.event_type == filters["event_type"])
                if "action" in filters:
                    query = query.filter(Audit.action == filters["action"])
                if "resource_type" in filters:
                    query = query.filter(Audit.resource_type == filters["resource_type"])
                if "start_date" in filters:
                    # Parse ISO format datetime
                    start_dt = datetime.fromisoformat(filters["start_date"])
                    query = query.filter(Audit.timestamp >= start_dt)
                if "end_date" in filters:
                    end_dt = datetime.fromisoformat(filters["end_date"])
                    query = query.filter(Audit.timestamp <= end_dt)

            # Get total count before pagination
            total_count = query.count()

            # Apply ordering
            if order_by == "timestamp DESC":
                query = query.order_by(Audit.timestamp.desc())
            elif order_by == "timestamp ASC":
                query = query.order_by(Audit.timestamp.asc())

            # Apply pagination
            query = query.limit(limit).offset(offset)

            # Execute query
            logs = query.all()

            # Convert to dict format
            log_dicts = []
            for log in logs:
                log_dicts.append(
                    {
                        "id": log.id,
                        "event_type": log.event_type,
                        "actor_id": log.actor_id,
                        "actor_role": log.actor_role,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "timestamp": (
                            log.timestamp.isoformat()
                            if log.timestamp is not None
                            else None
                        ),
                    }
                )

            return {
                "success": True,
                "logs": log_dicts,
                "total_count": total_count,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "logs": [],
                "total_count": 0,
            }

    def delete_log(self, log_id: int) -> Dict[str, Any]:
        """Attempt to delete an audit log (fails - immutability enforcement).

        Audit logs are immutable and cannot be deleted. This method enforces that
        constraint by always returning a failure response. No actual deletion occurs.

        This is a critical design feature for compliance - audit trails must never
        be tampered with or destroyed, even by privileged users.

        Args:
            log_id: ID of log to delete (will NOT be deleted)

        Returns:
            {
                "success": False,
                "message": "Cannot delete audit logs"
            }
        """
        return {
            "success": False,
            "message": "Cannot delete audit logs",
        }
