"""Tests for US-020 Advanced Audit Trail & Reporting.

This test suite covers all new AuditService methods and API endpoints:
- get_event_by_id
- advanced_search
- generate_prescription_report
- generate_security_report
- generate_compliance_report
- get_dashboard_stats
- export_logs (JSON and CSV)
- compute_hash_chain
- verify_chain_integrity

All 15+ tests must PASS for US-020 implementation.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time


@pytest.fixture
def sast_tz():
    """South African Standard Time timezone (UTC+2)."""
    return timezone(timedelta(hours=2))


@pytest.fixture
def now_sast(sast_tz):
    """Current time in SAST."""
    return datetime.now(sast_tz)


@pytest.fixture
def sample_audit_events(test_session, doctor_user, pharmacist_user, patient_user):
    """Create sample audit events for testing."""
    from app.services.audit import AuditService

    service = AuditService()

    # Create prescription events
    events = []

    # Prescription created
    result = service.log_event(
        event_type="prescription.created",
        actor_id=doctor_user.id,
        actor_role="doctor",
        action="create",
        resource_type="prescription",
        resource_id=1,
        details={"medication": "Amoxicillin", "dosage": "500mg"},
        ip_address="192.168.1.100",
    )
    events.append(result)

    # Prescription signed
    result = service.log_event(
        event_type="prescription.signed",
        actor_id=doctor_user.id,
        actor_role="doctor",
        action="sign",
        resource_type="prescription",
        resource_id=1,
        details={"signature_id": "sig_123", "algorithm": "Ed25519"},
        ip_address="192.168.1.100",
    )
    events.append(result)

    # Prescription dispensed
    result = service.log_event(
        event_type="prescription.dispensed",
        actor_id=pharmacist_user.id,
        actor_role="pharmacist",
        action="dispense",
        resource_type="prescription",
        resource_id=1,
        details={"batch_number": "BATCH-001", "quantity": 30},
        ip_address="192.168.1.101",
    )
    events.append(result)

    # User login (for security report)
    result = service.log_event(
        event_type="user.login",
        actor_id=doctor_user.id,
        actor_role="doctor",
        action="login",
        resource_type="user",
        resource_id=doctor_user.id,
        details={"method": "password"},
        ip_address="192.168.1.100",
    )
    events.append(result)

    return events


# ============================================================================
# Test get_event_by_id
# ============================================================================

class TestGetEventById:
    """Test get_event_by_id method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_get_event_by_id_success(self, test_session, doctor_user):
        """Test retrieving a single event by ID."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create an event
        result = service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={"medication": "Amoxicillin"},
        )

        event_id = result["log_id"]

        # Retrieve the event
        event_result = service.get_event_by_id(event_id)

        assert event_result["success"] is True
        assert event_result["event"]["id"] == event_id
        assert event_result["event"]["event_type"] == "prescription.created"
        assert event_result["event"]["action"] == "create"
        assert event_result["event"]["actor_id"] == doctor_user.id

    def test_get_event_by_id_not_found(self, test_session):
        """Test retrieving non-existent event returns error."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.get_event_by_id(99999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ============================================================================
# Test advanced_search
# ============================================================================

class TestAdvancedSearch:
    """Test advanced_search method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_advanced_search_by_text(self, test_session, doctor_user, pharmacist_user):
        """Test searching by text across event fields."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create events
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
            resource_id=2,
            details={},
        )

        # Search for "dispensed"
        result = service.advanced_search(query_text="dispensed")

        assert result["success"] is True
        assert result["total_count"] >= 1
        assert all("dispensed" in log["event_type"] for log in result["logs"])

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_advanced_search_empty_results(self, test_session):
        """Test search with no matching results."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.advanced_search(query_text="nonexistent_search_term_xyz")

        assert result["success"] is True
        assert result["total_count"] == 0
        assert result["logs"] == []

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_advanced_search_with_filters(self, test_session, doctor_user, pharmacist_user):
        """Test advanced search with additional filters."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create events with different actors
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
            resource_id=2,
            details={},
        )

        # Search with actor filter
        result = service.advanced_search(
            query_text="prescription",
            filters={"actor_id": doctor_user.id}
        )

        assert result["success"] is True
        assert all(log["actor_id"] == doctor_user.id for log in result["logs"])


# ============================================================================
# Test generate_prescription_report
# ============================================================================

class TestGeneratePrescriptionReport:
    """Test generate_prescription_report method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_prescription_report_with_data(self, test_session, doctor_user, pharmacist_user, sast_tz):
        """Test prescription report with actual data."""
        from app.services.audit import AuditService
        from datetime import datetime

        service = AuditService()

        # Get frozen time
        now_sast = datetime.now(sast_tz)

        # Create prescription events
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

        # Generate report
        start_date = now_sast - timedelta(hours=1)
        end_date = now_sast + timedelta(hours=1)

        result = service.generate_prescription_report(start_date, end_date)

        assert result["success"] is True
        assert result["report"]["metrics"]["total_created"] >= 1
        assert result["report"]["metrics"]["total_signed"] >= 1
        assert result["report"]["metrics"]["total_dispensed"] >= 1
        assert "unique_doctors" in result["report"]["metrics"]

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_prescription_report_empty_period(self, test_session, now_sast):
        """Test prescription report with no data in period."""
        from app.services.audit import AuditService

        service = AuditService()

        # Generate report for future period with no data
        start_date = now_sast + timedelta(days=1)
        end_date = now_sast + timedelta(days=2)

        result = service.generate_prescription_report(start_date, end_date)

        assert result["success"] is True
        assert result["report"]["metrics"]["total_created"] == 0
        assert result["report"]["metrics"]["total_events"] == 0


# ============================================================================
# Test generate_security_report
# ============================================================================

class TestGenerateSecurityReport:
    """Test generate_security_report method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_security_report_with_failed_logins(self, test_session, doctor_user, now_sast):
        """Test security report captures failed login attempts."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create failed login event
        service.log_event(
            event_type="user.login",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="login",
            resource_type="user",
            resource_id=doctor_user.id,
            details={"error": "invalid_password"},
        )

        # Generate report
        start_date = now_sast - timedelta(hours=1)
        end_date = now_sast + timedelta(hours=1)

        result = service.generate_security_report(start_date, end_date)

        assert result["success"] is True
        assert "failed_logins" in result["report"]["metrics"]
        assert "successful_logins" in result["report"]["metrics"]
        assert "unauthorized_access_attempts" in result["report"]["metrics"]

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_security_report_empty_period(self, test_session, now_sast):
        """Test security report with no security events."""
        from app.services.audit import AuditService

        service = AuditService()

        start_date = now_sast + timedelta(days=1)
        end_date = now_sast + timedelta(days=2)

        result = service.generate_security_report(start_date, end_date)

        assert result["success"] is True
        assert result["report"]["metrics"]["failed_logins"] == 0
        assert result["report"]["metrics"]["total_events"] == 0


# ============================================================================
# Test generate_compliance_report
# ============================================================================

class TestGenerateComplianceReport:
    """Test generate_compliance_report method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_compliance_report_with_revocation(self, test_session, doctor_user, sast_tz):
        """Test compliance report includes revocation events."""
        from app.services.audit import AuditService
        from datetime import datetime

        service = AuditService()
        now_sast = datetime.now(sast_tz)

        # Create revocation event
        service.log_event(
            event_type="prescription.revoked",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="revoke",
            resource_type="prescription",
            resource_id=1,
            details={"reason": "prescribing_error", "notes": "Wrong dosage"},
        )

        # Generate report
        start_date = now_sast - timedelta(hours=1)
        end_date = now_sast + timedelta(hours=1)

        result = service.generate_compliance_report(start_date, end_date)

        assert result["success"] is True
        assert "popia_metrics" in result["report"]
        assert "prescription_metrics" in result["report"]
        assert result["report"]["prescription_metrics"]["total_revocations"] >= 1
        assert "compliance_status" in result["report"]

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_compliance_report_data_access_tracking(self, test_session, doctor_user, now_sast):
        """Test compliance report tracks data access events."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create view event
        service.log_event(
            event_type="prescription.viewed",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="view",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        start_date = now_sast - timedelta(hours=1)
        end_date = now_sast + timedelta(hours=1)

        result = service.generate_compliance_report(start_date, end_date)

        assert result["success"] is True
        assert "data_access_events" in result["report"]["popia_metrics"]


# ============================================================================
# Test get_dashboard_stats
# ============================================================================

class TestGetDashboardStats:
    """Test get_dashboard_stats method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_dashboard_stats_with_data(self, test_session, doctor_user, pharmacist_user):
        """Test dashboard statistics with actual data."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create some events
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

        result = service.get_dashboard_stats(period_days=30)

        assert result["success"] is True
        assert "stats" in result
        assert result["stats"]["period_days"] == 30
        assert "total_events" in result["stats"]
        assert "prescriptions_created" in result["stats"]
        assert "prescriptions_dispensed" in result["stats"]
        assert "failed_logins" in result["stats"]
        assert "chain_integrity" in result["stats"]

    def test_dashboard_stats_empty(self, test_session):
        """Test dashboard statistics with no data."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.get_dashboard_stats(period_days=7)

        assert result["success"] is True
        assert result["stats"]["total_events"] == 0
        assert result["stats"]["prescriptions_created"] == 0


# ============================================================================
# Test export_logs
# ============================================================================

class TestExportLogs:
    """Test export_logs method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_export_logs_json_format(self, test_session, doctor_user):
        """Test exporting logs in JSON format."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create an event
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={"medication": "Amoxicillin"},
        )

        result = service.export_logs(format="json")

        assert result["success"] is True
        assert result["format"] == "json"
        assert "data" in result
        assert result["count"] >= 1

        # Verify JSON is valid
        data = json.loads(result["data"])
        assert "logs" in data
        assert "exported_at" in data

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_export_logs_csv_format(self, test_session, doctor_user):
        """Test exporting logs in CSV format."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create an event
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={"medication": "Amoxicillin"},
        )

        result = service.export_logs(format="csv")

        assert result["success"] is True
        assert result["format"] == "csv"
        assert "data" in result
        assert result["count"] >= 1

        # Verify CSV has header
        lines = result["data"].strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 data row
        assert "id" in lines[0]
        assert "event_type" in lines[0]

    def test_export_logs_invalid_format(self, test_session):
        """Test export with invalid format returns error."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.export_logs(format="xml")

        assert result["success"] is False
        assert "unsupported" in result.get("error", "").lower() or "format" in result.get("error", "").lower()


# ============================================================================
# Test compute_hash_chain
# ============================================================================

class TestComputeHashChain:
    """Test compute_hash_chain method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_compute_hash_chain_with_logs(self, test_session, doctor_user):
        """Test computing hash chain with existing logs."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create some events
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        result = service.compute_hash_chain()

        assert result["success"] is True
        assert "chain_hash" in result
        assert "count" in result
        assert result["count"] >= 1
        assert len(result["chain_hash"]) == 64  # SHA-256 hex length

    def test_compute_hash_chain_empty(self, test_session):
        """Test computing hash chain with no logs."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.compute_hash_chain()

        assert result["success"] is True
        assert result["chain_hash"] == ""
        assert result["count"] == 0


# ============================================================================
# Test verify_chain_integrity
# ============================================================================

class TestVerifyChainIntegrity:
    """Test verify_chain_integrity method."""

    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_verify_chain_integrity_valid(self, test_session, doctor_user):
        """Test chain integrity verification with valid chain."""
        from app.services.audit import AuditService

        service = AuditService()

        # Create some events
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        result = service.verify_chain_integrity()

        assert result["success"] is True
        assert result["valid"] is True
        assert "message" in result
        assert "count" in result

    def test_verify_chain_integrity_empty(self, test_session):
        """Test chain integrity with no logs."""
        from app.services.audit import AuditService

        service = AuditService()

        result = service.verify_chain_integrity()

        assert result["success"] is True
        assert result["valid"] is True
        assert result["count"] == 0


# ============================================================================
# Test API Endpoints (Integration)
# ============================================================================

@pytest.mark.asyncio
class TestAuditAPIEndpoints:
    """Test audit API endpoints using FastAPI test client."""

    async def test_list_audit_events_endpoint(self, async_client, valid_jwt_token, override_get_db, doctor_user):
        """Test GET /api/v1/admin/audit/events endpoint."""
        from app.services.audit import AuditService

        service = AuditService()
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        response = await async_client.get(
            "/api/v1/admin/audit/events",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data
        assert "total_count" in data

    async def test_get_event_by_id_endpoint(self, async_client, valid_jwt_token, override_get_db, doctor_user):
        """Test GET /api/v1/admin/audit/events/{id} endpoint."""
        from app.services.audit import AuditService

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
        event_id = result["log_id"]

        response = await async_client.get(
            f"/api/v1/admin/audit/events/{event_id}",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event"]["id"] == event_id

    async def test_advanced_search_endpoint(self, async_client, valid_jwt_token, override_get_db, doctor_user):
        """Test POST /api/v1/admin/audit/search endpoint."""
        from app.services.audit import AuditService

        service = AuditService()
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        response = await async_client.post(
            "/api/v1/admin/audit/search",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            json={"query_text": "prescription", "limit": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data

    async def test_prescription_report_endpoint(self, async_client, valid_jwt_token, override_get_db, doctor_user):
        """Test GET /api/v1/admin/reports/prescriptions endpoint."""
        response = await async_client.get(
            "/api/v1/admin/reports/prescriptions",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            params={
                "start_date": "2026-02-01T00:00:00",
                "end_date": "2026-02-28T23:59:59",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data
        assert "metrics" in data["report"]

    async def test_dashboard_stats_endpoint(self, async_client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/admin/dashboard/compliance endpoint."""
        response = await async_client.get(
            "/api/v1/admin/dashboard/compliance",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            params={"period_days": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data

    async def test_export_logs_endpoint(self, async_client, valid_jwt_token, override_get_db, doctor_user):
        """Test POST /api/v1/admin/reports/export endpoint."""
        from app.services.audit import AuditService

        service = AuditService()
        service.log_event(
            event_type="prescription.created",
            actor_id=doctor_user.id,
            actor_role="doctor",
            action="create",
            resource_type="prescription",
            resource_id=1,
            details={},
        )

        response = await async_client.post(
            "/api/v1/admin/reports/export",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            json={"format": "json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "json"
        assert "data" in data

    async def test_unauthorized_access_endpoint(self, async_client, valid_patient_jwt_token, override_get_db):
        """Test that patient role cannot access audit endpoints."""
        response = await async_client.get(
            "/api/v1/admin/audit/events",
            headers={"Authorization": f"Bearer {valid_patient_jwt_token}"},
        )

        assert response.status_code == 403
