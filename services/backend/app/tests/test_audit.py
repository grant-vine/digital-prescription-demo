"""Tests for audit trail logging with immutable persistence and compliance.

This is a TDD test suite for audit logging - all tests FAIL until TASK-064
implements the AuditService. Tests cover:

- Event logging (prescription lifecycle events)
- Query interface (list, filter, date range)
- Immutability (cannot update/delete logs after creation)
- Filtering capabilities (by actor, resource type, action)
- Pagination (limit, offset, ordering)
- Edge cases (missing actors, large JSON, concurrent writes)

All tests use pytest fixtures with actual database persistence via SQLAlchemy.
South African timezone (SAST - UTC+2) is used throughout.

Expected Failures (TDD Red Phase):
- ImportError: AuditService doesn't exist yet
- AttributeError: Service methods don't exist yet
- All 18 tests FAIL - This is healthy for TDD red phase

IMPORTANT: Tests use from app.services.audit import AuditService which will fail
because the service hasn't been implemented yet. This is EXPECTED and CORRECT for
TDD red phase (TASK-063). Tests will pass once AuditService is implemented (TASK-064).
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
import json


# ============================================================================
# FIXTURES - SAST timezone and test data
# ============================================================================


@pytest.fixture
def sast_tz():
    """South African Standard Time timezone (UTC+2)."""
    return timezone(timedelta(hours=2))


@pytest.fixture
def now_sast(sast_tz):
    """Current time in SAST."""
    return datetime.now(sast_tz)


@pytest.fixture
def sample_event_details():
    """Sample event details JSON for tests."""
    return {
        "medication": "Amoxicillin 500mg",
        "quantity": 30,
        "dosage": "500mg",
        "duration": "10 days",
        "instructions": "Take one tablet three times daily with food",
    }


@pytest.fixture
def large_event_details():
    """Large JSON details to test handling of substantial data."""
    return {
        "medication_name": "Amoxicillin",
        "medication_code": "J01CA04",
        "dosage": "500mg",
        "quantity": 30,
        "instructions": "Take one tablet three times daily with food for 10 days",
        "patient_notes": "Patient reports allergy to Penicillin group medications",
        "doctor_notes": "Monitor for adverse reactions. Patient has history of gastric issues.",
        "pharmacy_notes": "Standard dispensing. Patient requested blister pack format.",
        "directions": json.dumps(
            {
                "steps": [
                    {"step": 1, "instruction": "Take with food"},
                    {"step": 2, "instruction": "Do not exceed dose"},
                    {"step": 3, "instruction": "Refrigerate if needed"},
                    {"step": 4, "instruction": "Keep in original container"},
                ],
                "warnings": [
                    "May cause dizziness",
                    "Do not drive if dizzy",
                    "Report any adverse effects immediately",
                ],
            }
        ),
    }


# ============================================================================
# CATEGORY 1: EVENT LOGGING (5 tests)
# ============================================================================


@pytest.mark.asyncio
class TestEventLogging:
    """Test core event logging functionality."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_log_prescription_created_event(
        self, test_session, doctor_user, patient_user, sample_event_details
    ):
        """Test logging prescription creation event with actor and details.

        Expected behavior:
        - Service creates audit log entry in database
        - Captures event_type, actor_id, actor_role, action, resource_type, resource_id
        - Stores medication details in JSON details field
        - Returns log_id for future reference

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=123,
            details=sample_event_details,
            ip_address="192.168.1.100",
        )

        assert result["success"] is True
        assert "log_id" in result
        assert result["event_type"] == "prescription.created"

        # Verify database persistence
        from app.models.audit import Audit

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.event_type == "prescription.created"
        assert log.actor_id == doctor_user.id
        assert log.action == "create"

    @freeze_time("2026-02-12 10:30:00+02:00")
    def test_log_prescription_signed_event(self, test_session, doctor_user, now_sast):
        """Test logging prescription digital signature event.

        Expected behavior:
        - Records signature action by doctor
        - Includes signature details (signature_id, algorithm)
        - Timestamp is SAST
        - Immutable after creation

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        result = service.log_event(
            event_type="prescription.signed",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="sign",
            resource_type="prescription",
            resource_id=123,
            details={
                "signature_id": "sig_xyz789",
                "algorithm": "Ed25519",
                "timestamp": now_sast.isoformat(),
            },
            ip_address="192.168.1.100",
        )

        assert result["success"] is True
        assert result["action"] == "sign"

        from app.models.audit import Audit

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.event_type == "prescription.signed"
        assert log.details["algorithm"] == "Ed25519"

    @freeze_time("2026-02-12 11:00:00+02:00")
    def test_log_prescription_dispensed_event(self, test_session, pharmacist_user, now_sast):
        """Test logging medication dispensing event.

        Expected behavior:
        - Records dispense action by pharmacist
        - Includes dispensing details (batch_number, expiry_date)
        - Links to original prescription resource
        - Timestamp captures exact dispense time

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        result = service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=123,
            details={
                "batch_number": "BATCH-2026-001",
                "medication_name": "Amoxicillin 500mg",
                "quantity_dispensed": 30,
                "expiry_date": "2027-02-12",
            },
            ip_address="192.168.1.101",
        )

        assert result["success"] is True
        assert result["action"] == "dispense"

        from app.models.audit import Audit

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.event_type == "prescription.dispensed"
        assert log.actor_role == "pharmacist"
        assert log.details["batch_number"] == "BATCH-2026-001"

    @freeze_time("2026-02-12 14:00:00+02:00")
    def test_log_prescription_verified_event(self, test_session, pharmacist_user):
        """Test logging prescription verification event.

        Expected behavior:
        - Records verify action during pharmacist checking
        - Stores verification results (signature_valid, trust_registry_status)
        - Links to prescription resource
        - Audit trail shows full verification path

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        result = service.log_event(
            event_type="prescription.verified",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="verify",
            resource_type="prescription",
            resource_id=123,
            details={
                "signature_valid": True,
                "trust_registry_status": "verified",
                "revocation_status": "active",
                "issuer_did": "did:cheqd:testnet:doctor-abc123",
            },
            ip_address="192.168.1.101",
        )

        assert result["success"] is True
        assert result["action"] == "verify"

        from app.models.audit import Audit

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.details["signature_valid"] is True

    @freeze_time("2026-02-12 15:30:00+02:00")
    def test_log_prescription_revoked_event(self, test_session, doctor_user):
        """Test logging prescription revocation event.

        Expected behavior:
        - Records revoke action by doctor
        - Stores revocation reason (prescribing_error, patient_request, etc.)
        - Immutable record of why prescription was revoked
        - Essential for compliance audit trail

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        result = service.log_event(
            event_type="prescription.revoked",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="revoke",
            resource_type="prescription",
            resource_id=123,
            details={
                "reason": "prescribing_error",
                "notes": "Wrong medication dosage - should be 250mg not 500mg",
                "revocation_timestamp": "2026-02-12T15:30:00+02:00",
            },
            ip_address="192.168.1.100",
        )

        assert result["success"] is True
        assert result["action"] == "revoke"

        from app.models.audit import Audit

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.details["reason"] == "prescribing_error"


# ============================================================================
# CATEGORY 2: QUERY INTERFACE (4 tests)
# ============================================================================


@pytest.mark.asyncio
class TestQueryInterface:
    """Test audit log querying and filtering."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_query_all_audit_logs(self, test_session, doctor_user, pharmacist_user):
        """Test retrieving all audit logs from database.

        Expected behavior:
        - Service can list all audit logs
        - Returns logs in default order (reverse chronological)
        - Includes all fields (event_type, actor_id, timestamp, etc.)
        - Pageable results

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log multiple events
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={"medication": "Amoxicillin"},
        )

        service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=2,
            details={"medication": "Ibuprofen"},
        )

        # Query all logs
        logs = service.query_logs(filters={}, limit=10, offset=0, order_by="timestamp DESC")

        assert logs["success"] is True
        assert logs["total_count"] >= 2
        assert len(logs["logs"]) >= 2
        assert logs["logs"][0]["event_type"] in ["prescription.created", "prescription.dispensed"]

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_filter_logs_by_actor_id(self, test_session, doctor_user, pharmacist_user):
        """Test filtering audit logs by actor (user who performed action).

        Expected behavior:
        - Can filter logs by actor_id
        - Returns only logs where specified actor took action
        - Excludes logs from other actors
        - Case-insensitive filtering

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log events from different actors
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        # Filter by doctor actor
        logs = service.query_logs(filters={"actor_id": doctor_user.id}, limit=10, offset=0)

        assert logs["success"] is True
        assert len(logs["logs"]) >= 1
        for log in logs["logs"]:
            assert log["actor_id"] == doctor_user.id

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_filter_logs_by_event_type(self, test_session, doctor_user, pharmacist_user):
        """Test filtering audit logs by specific event type.

        Expected behavior:
        - Can filter by event_type (e.g., prescription.created)
        - Returns only matching event types
        - Excludes other event types
        - Can filter multiple event types with OR condition

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log different event types
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="prescription.signed",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="sign",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        # Filter by specific event type
        logs = service.query_logs(
            filters={"event_type": "prescription.dispensed"}, limit=10, offset=0
        )

        assert logs["success"] is True
        for log in logs["logs"]:
            assert log["event_type"] == "prescription.dispensed"

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_filter_logs_by_date_range(self, test_session, doctor_user):
        """Test filtering audit logs by date range.

        Expected behavior:
        - Can filter logs between start_date and end_date
        - Includes logs within SAST timezone range
        - Excludes logs outside date range
        - Supports open-ended ranges (start only, end only)

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from datetime import timezone

        service = AuditService()

        # Get current time INSIDE freeze_time (fixture runs before decorator)
        sast = timezone(timedelta(hours=2))
        now_sast = datetime.now(sast)

        # Log event
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        # Query with date range
        start_date = now_sast - timedelta(hours=1)
        end_date = now_sast + timedelta(hours=1)

        logs = service.query_logs(
            filters={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            limit=10,
            offset=0,
        )

        assert logs["success"] is True
        assert len(logs["logs"]) >= 1


# ============================================================================
# CATEGORY 3: IMMUTABILITY (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestImmutability:
    """Test that audit logs cannot be modified after creation."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_cannot_update_audit_log_action_field(self, test_session, doctor_user):
        """Test that audit log action field is immutable.

        Expected behavior:
        - Log is created with action="create"
        - Attempting to update action field should fail silently or raise error
        - Database should still show original action="create"
        - Immutability prevents tampering with audit trail

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from app.models.audit import Audit

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        log_id = result["log_id"]
        log = test_session.query(Audit).filter_by(id=log_id).first()

        # Try to modify action field
        original_action = log.action
        log.action = "tampered"
        test_session.commit()

        # Verify immutability - should still be original
        test_session.refresh(log)
        assert log.action == original_action  # Should not change

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_cannot_delete_audit_log(self, test_session, doctor_user):
        """Test that audit logs cannot be deleted.

        Expected behavior:
        - Attempt to delete should raise error or be blocked
        - Log should remain in database
        - Prevents destruction of compliance records

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from app.models.audit import Audit

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        log_id = result["log_id"]

        # Try to delete
        log = test_session.query(Audit).filter_by(id=log_id).first()
        assert log is not None

        # Service should prevent deletion
        delete_result = service.delete_log(log_id=log_id)
        assert (
            delete_result["success"] is False
            or delete_result["message"] == "Cannot delete audit logs"
        )

        # Verify log still exists
        log_after = test_session.query(Audit).filter_by(id=log_id).first()
        assert log_after is not None

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_audit_log_model_blocks_modification_with_immutable_flag(
        self, test_session, doctor_user
    ):
        """Test that Audit model's __setattr__ method blocks modifications.

        Expected behavior:
        - Audit model has _immutable flag set to True after __init__
        - Attempting to modify fields after init should be blocked
        - __setattr__ method returns silently on blocked modifications

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from app.models.audit import Audit

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={"key": "value"},
        )

        log_id = result["log_id"]
        log = test_session.query(Audit).filter_by(id=log_id).first()

        # Verify immutable flag is set
        assert hasattr(log, "_immutable")
        assert log._immutable is True

        # Try to set attribute - should be blocked
        log.event_type = "tampered.event"

        # Verify it didn't change
        test_session.refresh(log)
        assert log.event_type == "prescription.created"


# ============================================================================
# CATEGORY 4: FILTERING CAPABILITIES (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestFiltering:
    """Test advanced filtering combinations."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_filter_logs_by_resource_type(self, test_session, doctor_user, pharmacist_user):
        """Test filtering by resource type (prescription, dispensing, etc.).

        Expected behavior:
        - Can filter logs by resource_type field
        - Returns only logs for specified resource type
        - Supports multiple resource types with OR

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log events for different resources
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="user.login",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="login",
            resource_type="user",
            resource_id=doctor_user.id,
            details={},
        )

        # Filter by resource type
        logs = service.query_logs(filters={"resource_type": "prescription"}, limit=10, offset=0)

        assert logs["success"] is True
        for log in logs["logs"]:
            assert log["resource_type"] == "prescription"

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_filter_logs_by_action(self, test_session, doctor_user, pharmacist_user):
        """Test filtering by action (create, sign, dispense, verify, revoke).

        Expected behavior:
        - Can filter by action field
        - Returns only logs with specified action
        - Useful for finding all dispensing events, all revocations, etc.

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log different actions
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        # Filter by action
        logs = service.query_logs(filters={"action": "dispense"}, limit=10, offset=0)

        assert logs["success"] is True
        for log in logs["logs"]:
            assert log["action"] == "dispense"

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_complex_filter_combination(self, test_session, doctor_user, pharmacist_user, now_sast):
        """Test combining multiple filters (actor + event_type + date_range).

        Expected behavior:
        - Can filter by multiple criteria simultaneously
        - Returns logs matching ALL criteria (AND logic)
        - Useful for compliance reports (e.g., all revocations by this doctor in this period)

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Log multiple events
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        service.log_event(
            event_type="prescription.revoked",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="revoke",
            resource_type="prescription",
            resource_id=1,
            details={"reason": "prescribing_error"},
        )

        service.log_event(
            event_type="prescription.dispensed",
            actor_id=pharmacist_user.id,
            actor_role="pharmacist",
            action="dispense",
            resource_type="prescription",
            resource_id=2,
            details={},
        )

        # Complex filter: doctor's revocations today
        start_date = now_sast - timedelta(hours=24)
        logs = service.query_logs(
            filters={
                "actor_id": doctor_user.id,
                "event_type": "prescription.revoked",
                "start_date": start_date.isoformat(),
            },
            limit=10,
            offset=0,
        )

        assert logs["success"] is True
        for log in logs["logs"]:
            assert log["actor_id"] == doctor_user.id
            assert log["event_type"] == "prescription.revoked"


# ============================================================================
# CATEGORY 5: PAGINATION (2 tests)
# ============================================================================


@pytest.mark.asyncio
class TestPagination:
    """Test pagination and ordering of audit logs."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_pagination_with_limit_and_offset(self, test_session, doctor_user):
        """Test paginating results with limit and offset.

        Expected behavior:
        - limit=5, offset=0 returns first 5 logs
        - limit=5, offset=5 returns next 5 logs
        - offset > total_count returns empty list
        - Preserves order across pagination

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Create 12 logs
        for i in range(12):
            service.log_event(
                event_type="prescription.created",
                actor_id=doctor_user.id,
                actor_role="doctor",
                action="create",
                resource_type="prescription",
                resource_id=i,
                details={"index": i},
            )

        # Get first page
        page1 = service.query_logs(filters={}, limit=5, offset=0, order_by="timestamp DESC")

        # Get second page
        page2 = service.query_logs(filters={}, limit=5, offset=5, order_by="timestamp DESC")

        assert page1["success"] is True
        assert page2["success"] is True
        assert len(page1["logs"]) == 5
        assert len(page2["logs"]) == 5

        # Verify different logs on each page
        ids_page1 = [log["id"] for log in page1["logs"]]
        ids_page2 = [log["id"] for log in page2["logs"]]
        assert len(set(ids_page1) & set(ids_page2)) == 0  # No overlap

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_default_ordering_most_recent_first(self, test_session, doctor_user):
        """Test that logs are ordered by timestamp (most recent first).

        Expected behavior:
        - Default order is timestamp DESC (most recent first)
        - Can override with order_by parameter
        - Consistent ordering across pagination

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Create logs with time separation
        for i in range(3):
            service.log_event(
                event_type="prescription.created",
                actor_id=doctor_user.id,
                actor_role="doctor",
                action="create",
                resource_type="prescription",
                resource_id=i,
                details={},
            )

        logs = service.query_logs(filters={}, limit=10, offset=0, order_by="timestamp DESC")

        assert logs["success"] is True

        # Verify reverse chronological order
        if len(logs["logs"]) > 1:
            for i in range(len(logs["logs"]) - 1):
                assert logs["logs"][i]["timestamp"] >= logs["logs"][i + 1]["timestamp"]


# ============================================================================
# CATEGORY 6: EDGE CASES (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_log_event_with_missing_optional_actor_metadata(self, test_session, doctor_user):
        """Test logging event when optional fields are missing.

        Expected behavior:
        - Should handle missing ip_address gracefully
        - Should handle empty or null details
        - Should still create audit log with required fields
        - Optional fields can be null in database

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from app.models.audit import Audit

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details=None,  # Missing details
            # Missing ip_address
        )

        assert result["success"] is True

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.ip_address is None or log.ip_address == ""
        assert log.details is None or log.details == {}

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_log_event_with_large_json_details(
        self, test_session, doctor_user, large_event_details
    ):
        """Test logging event with substantial JSON details.

        Expected behavior:
        - Should handle large JSON objects without error
        - Details should be stored completely and accurately
        - Should preserve nested structures (arrays, objects)
        - Should handle special characters and escaped quotes

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService
        from app.models.audit import Audit

        service = AuditService()

        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details=large_event_details,
        )

        assert result["success"] is True

        log = test_session.query(Audit).filter_by(id=result["log_id"]).first()
        assert log is not None
        assert log.details is not None
        assert log.details["medication_name"] == "Amoxicillin"
        assert "warnings" in log.details.get("directions", {}) or isinstance(
            log.details.get("directions"), str
        )

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_concurrent_audit_log_writes_from_multiple_actors(
        self, test_session, doctor_user, pharmacist_user, patient_user
    ):
        """Test concurrent writes to audit log from different actors.

        Expected behavior:
        - Multiple actors can log events simultaneously
        - No race conditions or missing logs
        - All logs recorded in database
        - Timestamp resolution sufficient to distinguish order

        EXPECTED FAILURE: AuditService doesn't exist yet.
        """
        from app.services.audit import AuditService

        service = AuditService()

        # Simulate concurrent writes
        actors = [
            (doctor_user.id, "doctor"),
            (pharmacist_user.id, "pharmacist"),
            (patient_user.id, "patient"),
            (doctor_user.id, "doctor"),
        ]

        log_ids = []
        for actor_id, actor_role in actors:
            result = service.log_event(
                event_type=f"{actor_role}.action",
                actor_id=actor_id,
                actor_role=actor_role,
                action="test_action",
                resource_type="prescription",
                resource_id=1,
                details={},
            )
            log_ids.append(result["log_id"])

        # Verify all logs created
        assert len(log_ids) == 4
        assert len(set(log_ids)) == 4  # All unique

        # Query should return all logs
        logs = service.query_logs(filters={}, limit=10, offset=0)

        assert logs["success"] is True
        assert logs["total_count"] >= 4
