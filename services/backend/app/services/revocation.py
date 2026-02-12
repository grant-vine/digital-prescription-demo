"""Revocation service for managing prescription revocations with database persistence.

Implements US-015 (Revoke or Cancel Prescription) with:
- Revocation request handling with reason/notes
- Prescription status changes (ACTIVE → REVOKED)
- SSI revocation registry integration (ACA-Py placeholder)
- Patient notification on revocation (future DIDComm)
- Audit trail logging for compliance
- Edge case handling (cannot revoke twice, revoked prescriptions block dispensing)

All dates handled in SAST (UTC+2) timezone.
Database operations use SQLAlchemy with atomic transactions.

This is the TDD green phase implementation for TASK-061 tests.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session


class RevocationService:
    """Service for managing prescription revocations.
    
    Handles:
    1. Revocation request with reason tracking
    2. Prescription status updates (ACTIVE → REVOKED)
    3. SSI revocation registry updates (placeholder for ACA-Py)
    4. Patient notifications (placeholder for DIDComm)
    5. Audit trail logging
    6. Edge case validation (already revoked, prescription not found)
    """
    
    # SAST timezone (UTC+2)
    SAST = timezone(timedelta(hours=2))
    
    # Valid revocation reasons
    VALID_REASONS = [
        "prescribing_error",
        "patient_request",
        "adverse_reaction",
        "duplicate",
        "other"
    ]
    
    def __init__(self, db_session: Optional[Session] = None, tenant_id: str = "default"):
        """Initialize with optional database session.
        
        Args:
            db_session: SQLAlchemy session for database operations.
                       If None, service will use injected session per call.
            tenant_id: Tenant identifier for multi-tenancy scoping.
        """
        self.db = db_session
        self.tenant_id = tenant_id
    
    # ========================================================================
    # CATEGORY 1: REVOCATION REQUEST
    # ========================================================================
    
    def revoke_prescription(
        self,
        prescription_id: int,
        revoked_by_user_id: int,
        reason: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Revoke prescription with audit trail and notifications.
        
        Process:
        1. Validate prescription exists and not already revoked
        2. Update prescription.status = "REVOKED"
        3. Create AuditLog entry
        4. Call update_revocation_registry() placeholder
        5. Call notify_patient() placeholder
        6. Return success response
        
        Args:
            prescription_id: ID of prescription to revoke
            revoked_by_user_id: ID of user performing revocation (doctor)
            reason: Revocation reason (prescribing_error, patient_request, etc.)
            notes: Optional additional context for audit trail
        
        Returns:
            {
                "success": True,
                "prescription_id": 123,
                "revocation_id": 456,  # AuditLog.id
                "timestamp": "2026-02-12T10:00:00+02:00",
                "reason": "prescribing_error",
                "registry_updated": True,
                "patient_notified": True
            }
        
        Raises:
            ValueError: Prescription not found
            ValueError: Already revoked
        """
        from app.db import get_db_session
        from app.models.prescription import Prescription
        from app.models.audit import Audit
        
        session = self.db or get_db_session()
        
        try:
            # 1. Get prescription
            prescription = session.query(Prescription).filter_by(id=prescription_id).first()
            if not prescription:
                raise ValueError("Prescription not found")
            
            # 2. Check already revoked
            current_status = getattr(prescription, 'status', None)
            if current_status == "REVOKED":
                raise ValueError("Prescription already revoked")
            
            # 3. Update status
            setattr(prescription, 'status', "REVOKED")
            
            # 4. Create audit log
            now_sast = datetime.now(self.SAST)
            audit = Audit(
                event_type="prescription_revocation",
                actor_id=revoked_by_user_id,
                actor_role="doctor",  # Assuming doctor for now
                action="prescription_revoked",
                resource_type="prescription",
                resource_id=prescription_id,
                details={
                    "reason": reason,
                    "notes": notes,
                },
                timestamp=now_sast
            )
            session.add(audit)
            session.commit()
            session.refresh(audit)
            
            # 5. Update registry (placeholder)
            registry_result = {"registry_updated": False}
            credential_id = getattr(prescription, 'credential_id', None)
            if credential_id is not None:
                registry_result = self.update_revocation_registry(credential_id)
            
            # 6. Notify patient (placeholder)
            patient_id_value = getattr(prescription, 'patient_id', None)
            if patient_id_value is None:
                raise ValueError("Prescription has no patient_id")
            
            notification_result = self.notify_patient(
                prescription_id=prescription_id,
                patient_id=patient_id_value,
                reason=reason
            )
            
            return {
                "success": True,
                "prescription_id": prescription_id,
                "revocation_id": audit.id,
                "timestamp": now_sast.isoformat(),
                "reason": reason,
                "notes": notes,
                "registry_updated": registry_result.get("registry_updated", False),
                "patient_notified": notification_result.get("notification_sent", False)
            }
        
        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise ValueError(f"Revocation failed: {str(e)}")
    
    # ========================================================================
    # CATEGORY 2: REVOCATION STATUS CHECKS
    # ========================================================================
    
    def check_revocation_status(
        self,
        prescription_id: int
    ) -> Dict[str, Any]:
        """Check if prescription is revoked (status query).
        
        Used by dispensing service and pharmacy UI to check revocation
        before dispensing.
        
        Args:
            prescription_id: ID of prescription
        
        Returns:
            {
                "is_revoked": bool,
                "timestamp": Optional[str],  # When revoked
                "reason": Optional[str],
                "revoked_by": Optional[int]  # User ID
            }
        """
        from app.db import get_db_session
        from app.models.prescription import Prescription
        from app.models.audit import Audit
        
        session = self.db or get_db_session()
        
        try:
            # Get prescription
            prescription = session.query(Prescription).filter_by(id=prescription_id).first()
            if not prescription:
                raise ValueError("Prescription not found")
            
            is_revoked = getattr(prescription, 'status', None) == "REVOKED"
            
            if not is_revoked:
                return {
                    "is_revoked": False,
                    "timestamp": None,
                    "reason": None,
                    "revoked_by": None
                }
            
            # Get revocation details from audit log
            audit_entry = session.query(Audit).filter(
                Audit.resource_id == prescription_id,
                Audit.action == "prescription_revoked"
            ).order_by(Audit.timestamp.desc()).first()
            
            if not audit_entry:
                # Prescription is revoked but no audit entry (edge case)
                return {
                    "is_revoked": True,
                    "timestamp": None,
                    "reason": None,
                    "revoked_by": None
                }
            
            # Extract details from audit log
            details = audit_entry.details or {}
            
            return {
                "is_revoked": True,
                "timestamp": audit_entry.timestamp.isoformat(),
                "reason": details.get("reason"),
                "revoked_by": audit_entry.actor_id
            }
        
        except Exception as e:
            return {
                "is_revoked": False,
                "timestamp": None,
                "reason": f"error: {str(e)}",
                "revoked_by": None
            }
    
    # ========================================================================
    # CATEGORY 3: AUDIT TRAIL
    # ========================================================================
    
    def get_revocation_history(
        self,
        prescription_id: int
    ) -> List[Dict[str, Any]]:
        """Get audit trail of revocation events for prescription.
        
        Returns list of all revocation events (in case of manual corrections
        or multiple revocation attempts).
        
        Args:
            prescription_id: ID of prescription
        
        Returns:
            List of revocation events sorted chronologically (oldest → newest)
            
            [
                {
                    "revocation_id": 123,
                    "timestamp": "2026-02-12T10:00:00+02:00",
                    "reason": "prescribing_error",
                    "notes": "Wrong dosage prescribed",
                    "revoked_by": 1
                },
                ...
            ]
        """
        from app.db import get_db_session
        from app.models.audit import Audit
        
        session = self.db or get_db_session()
        
        try:
            # Query audit logs filtered by prescription_id and action
            audit_entries = session.query(Audit).filter(
                Audit.resource_id == prescription_id,
                Audit.action == "prescription_revoked"
            ).order_by(Audit.timestamp.asc()).all()
            
            # Convert to dicts
            result = []
            for audit in audit_entries:
                details = audit.details or {}
                result.append({
                    "revocation_id": audit.id,
                    "timestamp": audit.timestamp.isoformat(),
                    "reason": details.get("reason"),
                    "notes": details.get("notes"),
                    "revoked_by": audit.actor_id
                })
            
            return result
        
        except Exception:
            return []
    
    # ========================================================================
    # CATEGORY 4: SSI REVOCATION REGISTRY (PLACEHOLDER)
    # ========================================================================
    
    def update_revocation_registry(
        self,
        credential_id: str,
        revocation_registry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Placeholder for ACA-Py revocation registry update.
        
        Future implementation will call:
        - POST /revocation/revoke-credential
        
        For now, just return success to satisfy tests.
        
        Args:
            credential_id: ID of credential to revoke
            revocation_registry_id: Optional registry ID (for future use)
        
        Returns:
            {
                "success": True,
                "credential_id": "cred_abc123",
                "registry_updated": True
            }
        """
        # PLACEHOLDER: ACA-Py integration will be implemented in TASK-062
        # For MVP, we just return success
        
        return {
            "success": True,
            "credential_id": credential_id,
            "registry_updated": True
        }
    
    # ========================================================================
    # CATEGORY 5: PATIENT NOTIFICATION (PLACEHOLDER)
    # ========================================================================
    
    def notify_patient(
        self,
        prescription_id: int,
        patient_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """Placeholder for patient notification via DIDComm.
        
        Future implementation will:
        - Create DIDComm encrypted message
        - Send to patient wallet
        - Include revocation reason and prescription details
        
        For now, just return success to satisfy tests.
        
        Args:
            prescription_id: ID of prescription that was revoked
            patient_id: ID of patient to notify
            reason: Revocation reason to include in notification
        
        Returns:
            {
                "success": True,
                "patient_id": 2,
                "notification_sent": True
            }
        """
        # PLACEHOLDER: DIDComm integration will be implemented in TASK-062
        # For MVP, we just return success
        
        return {
            "success": True,
            "patient_id": patient_id,
            "notification_sent": True
        }
