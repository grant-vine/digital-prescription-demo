"""Tests for advanced prescription revocation workflows (US-021).

This test suite covers:
- Bulk revocation operations (preview and execute)
- Bulk rollback within 24 hours
- Scheduled revocations (create, cancel, list, process)
- Conditional revocation rules (create, evaluate)
- Impact analysis (single and bulk)
- Dashboard statistics

All tests use pytest fixtures with actual database persistence via SQLAlchemy.
South African timezone (SAST - UTC+2) is used throughout.
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

from app.services.revocation import RevocationService
from app.models.prescription import Prescription
from app.models.user import User
from app.models.audit import Audit


SAST = timezone(timedelta(hours=2))


def _create_test_prescription(session, doctor_id, patient_id, status="ACTIVE", medication_name="Amoxicillin", **kwargs):
    """Helper to create test prescriptions."""
    rx = Prescription(
        doctor_id=doctor_id,
        patient_id=patient_id,
        medication_name=medication_name,
        medication_code="J01CA04",
        dosage="500mg",
        quantity=21,
        instructions="Take three times daily",
        date_issued=datetime.now(SAST),
        date_expires=datetime.now(SAST) + timedelta(days=90),
        status=status,
        **kwargs
    )
    session.add(rx)
    session.commit()
    session.refresh(rx)
    return rx


# ============================================================================
# BULK REVOCATION TESTS
# ============================================================================


class TestBulkRevocation:
    """Test bulk revocation operations."""
    
    def test_bulk_revoke_preview(self, test_session, doctor_user, patient_user):
        """Test bulk revoke preview mode - should not actually revoke."""
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        result = svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id},
            reason="patient_request",
            actor_id=doctor_user.id,
            preview_only=True
        )
        
        assert result["preview"] is True
        assert result["affected_count"] >= 2
        assert "bulk_operation_id" in result
        
        # Verify prescriptions are NOT actually revoked
        test_session.refresh(rx1)
        test_session.refresh(rx2)
        assert rx1.status == "ACTIVE"
        assert rx2.status == "ACTIVE"
    
    def test_bulk_revoke_execute(self, test_session, doctor_user, patient_user):
        """Test bulk revoke execution."""
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        result = svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id},
            reason="prescribing_error",
            actor_id=doctor_user.id,
            preview_only=False
        )
        
        assert result["preview"] is False
        assert result["affected_count"] == 2
        assert rx1.id in result["prescription_ids"]
        assert rx2.id in result["prescription_ids"]
        
        # Verify prescriptions ARE revoked
        test_session.refresh(rx1)
        test_session.refresh(rx2)
        assert rx1.status == "REVOKED"
        assert rx2.status == "REVOKED"
    
    def test_bulk_revoke_max_100_limit(self, test_session, doctor_user, patient_user):
        """Test that bulk revoke is limited to 100 prescriptions."""
        # Create 101 prescriptions
        for i in range(101):
            _create_test_prescription(test_session, doctor_user.id, patient_user.id, medication_name=f"Med{i}")
        
        svc = RevocationService(db_session=test_session)
        
        with pytest.raises(ValueError, match="100 prescriptions maximum"):
            svc.revoke_bulk(
                filter_criteria={"patient_id": patient_user.id},
                reason="test",
                actor_id=doctor_user.id
            )
    
    def test_bulk_revoke_filter_by_medication(self, test_session, doctor_user, patient_user):
        """Test bulk revoke with medication name filter."""
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id, medication_name="Amoxicillin")
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id, medication_name="Ibuprofen")
        
        svc = RevocationService(db_session=test_session)
        result = svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id, "medication_name": "Amoxi"},
            reason="test",
            actor_id=doctor_user.id
        )
        
        assert result["affected_count"] == 1
        assert rx1.id in result["prescription_ids"]
        assert rx2.id not in result["prescription_ids"]
    
    def test_bulk_revoke_filter_by_date_range(self, test_session, doctor_user, patient_user):
        """Test bulk revoke with date range filter."""
        # Create prescription with specific date
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx1.date_issued = datetime.now(SAST) - timedelta(days=5)
        test_session.commit()
        
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx2.date_issued = datetime.now(SAST) - timedelta(days=20)
        test_session.commit()
        
        svc = RevocationService(db_session=test_session)
        result = svc.revoke_bulk(
            filter_criteria={
                "patient_id": patient_user.id,
                "date_range": {
                    "start": (datetime.now(SAST) - timedelta(days=10)).isoformat(),
                    "end": datetime.now(SAST).isoformat()
                }
            },
            reason="test",
            actor_id=doctor_user.id
        )
        
        # Should only include rx1 (5 days ago), not rx2 (20 days ago)
        assert result["affected_count"] == 1
        assert rx1.id in result["prescription_ids"]


# ============================================================================
# BULK ROLLBACK TESTS
# ============================================================================


class TestBulkRollback:
    """Test bulk rollback operations."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_rollback_bulk_success(self, test_session, doctor_user, patient_user):
        """Test successful rollback within 24 hours."""
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Execute bulk revoke
        revoke_result = svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id},
            reason="test",
            actor_id=doctor_user.id
        )
        
        bulk_id = revoke_result["bulk_operation_id"]
        
        # Verify revoked
        test_session.refresh(rx1)
        assert rx1.status == "REVOKED"
        
        # Rollback
        rollback_result = svc.rollback_bulk(bulk_id, actor_id=doctor_user.id)
        
        assert rollback_result["success"] is True
        assert rollback_result["restored_count"] == 2
        
        # Verify restored
        test_session.refresh(rx1)
        test_session.refresh(rx2)
        assert rx1.status == "ACTIVE"
        assert rx2.status == "ACTIVE"
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_rollback_after_24_hours_fails(self, test_session, doctor_user, patient_user):
        """Test rollback fails after 24 hour window."""
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Execute bulk revoke
        revoke_result = svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id},
            reason="test",
            actor_id=doctor_user.id
        )
        
        bulk_id = revoke_result["bulk_operation_id"]
        
        # Move time forward 25 hours
        with freeze_time("2026-02-13 11:00:00+02:00"):
            with pytest.raises(ValueError, match="Rollback window expired"):
                svc.rollback_bulk(bulk_id, actor_id=doctor_user.id)
    
    def test_rollback_nonexistent_bulk(self, test_session, doctor_user):
        """Test rollback fails for non-existent bulk operation."""
        svc = RevocationService(db_session=test_session)
        
        with pytest.raises(ValueError, match="Bulk operation not found"):
            svc.rollback_bulk("nonexistent-uuid", actor_id=doctor_user.id)


# ============================================================================
# SCHEDULED REVOCATION TESTS
# ============================================================================


class TestScheduledRevocation:
    """Test scheduled revocation operations."""
    
    def test_schedule_revocation_success(self, test_session, doctor_user, patient_user):
        """Test scheduling a future revocation."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        scheduled_time = datetime.now(SAST) + timedelta(days=7)
        
        result = svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=scheduled_time,
            reason="expiry",
            actor_id=doctor_user.id
        )
        
        assert "schedule_id" in result
        assert result["prescription_id"] == rx.id
        assert result["status"] == "scheduled"
        assert result["reason"] == "expiry"
    
    def test_schedule_revocation_prescription_not_found(self, test_session, doctor_user):
        """Test scheduling fails for non-existent prescription."""
        svc = RevocationService(db_session=test_session)
        
        with pytest.raises(ValueError, match="Prescription not found"):
            svc.schedule_revocation(
                prescription_id=99999,
                scheduled_at=datetime.now(SAST) + timedelta(days=7),
                reason="test",
                actor_id=doctor_user.id
            )
    
    def test_cancel_scheduled_revocation(self, test_session, doctor_user, patient_user):
        """Test canceling a scheduled revocation."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        scheduled_time = datetime.now(SAST) + timedelta(days=7)
        
        # Schedule
        schedule_result = svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=scheduled_time,
            reason="test",
            actor_id=doctor_user.id
        )
        
        schedule_id = schedule_result["schedule_id"]
        
        # Cancel
        cancel_result = svc.cancel_scheduled_revocation(schedule_id, actor_id=doctor_user.id)
        
        assert cancel_result["success"] is True
        assert cancel_result["schedule_id"] == schedule_id
    
    def test_cancel_already_cancelled_fails(self, test_session, doctor_user, patient_user):
        """Test canceling an already cancelled schedule fails."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Schedule
        schedule_result = svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=datetime.now(SAST) + timedelta(days=7),
            reason="test",
            actor_id=doctor_user.id
        )
        
        schedule_id = schedule_result["schedule_id"]
        
        # Cancel once
        svc.cancel_scheduled_revocation(schedule_id, actor_id=doctor_user.id)
        
        # Cancel again should fail
        with pytest.raises(ValueError, match="already cancelled"):
            svc.cancel_scheduled_revocation(schedule_id, actor_id=doctor_user.id)
    
    def test_get_scheduled_revocations(self, test_session, doctor_user, patient_user):
        """Test listing scheduled revocations."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Schedule two revocations
        svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=datetime.now(SAST) + timedelta(days=7),
            reason="test1",
            actor_id=doctor_user.id
        )
        
        svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=datetime.now(SAST) + timedelta(days=14),
            reason="test2",
            actor_id=doctor_user.id
        )
        
        # Get scheduled
        scheduled = svc.get_scheduled_revocations()
        
        assert len(scheduled) >= 2
        reasons = [s["reason"] for s in scheduled]
        assert "test1" in reasons
        assert "test2" in reasons
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_process_due_revocations(self, test_session, doctor_user, patient_user):
        """Test processing due scheduled revocations."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Schedule revocation in the past (should be due)
        scheduled_time = datetime.now(SAST) - timedelta(hours=1)
        
        svc.schedule_revocation(
            prescription_id=rx.id,
            scheduled_at=scheduled_time,
            reason="scheduled_expiry",
            actor_id=doctor_user.id
        )
        
        # Process due revocations
        result = svc.process_due_revocations()
        
        assert result["processed_count"] >= 1
        assert result["revoked_count"] >= 1
        
        # Verify prescription is revoked
        test_session.refresh(rx)
        assert rx.status == "REVOKED"


# ============================================================================
# CONDITIONAL REVOCATION RULES TESTS
# ============================================================================


class TestConditionalRevocationRules:
    """Test conditional revocation rules."""
    
    def test_create_revocation_rule(self, test_session, doctor_user):
        """Test creating a revocation rule."""
        svc = RevocationService(db_session=test_session)
        
        result = svc.create_revocation_rule(
            trigger_type="expiry",
            conditions={"auto_revoke": True},
            reason="auto_expired",
            actor_id=doctor_user.id
        )
        
        assert "rule_id" in result
        assert result["trigger_type"] == "expiry"
        assert result["conditions"]["auto_revoke"] is True
        assert result["reason"] == "auto_expired"
    
    def test_evaluate_expiry_rule(self, test_session, doctor_user, patient_user):
        """Test evaluating expiry rule against expired prescription."""
        # Create expired prescription
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx.date_expires = datetime.now(SAST) - timedelta(days=1)  # Expired yesterday
        test_session.commit()
        
        svc = RevocationService(db_session=test_session)
        
        # Create expiry rule
        svc.create_revocation_rule(
            trigger_type="expiry",
            conditions={},
            reason="auto_expired",
            actor_id=doctor_user.id
        )
        
        # Evaluate
        triggered = svc.evaluate_revocation_rules(rx.id)
        
        assert len(triggered) >= 1
        assert any(t["trigger_type"] == "expiry" for t in triggered)
    
    def test_evaluate_repeat_exhausted_rule(self, test_session, doctor_user, patient_user):
        """Test evaluating repeat exhausted rule."""
        rx = _create_test_prescription(
            test_session, doctor_user.id, patient_user.id,
            is_repeat=True, repeat_count=3
        )
        
        svc = RevocationService(db_session=test_session)
        
        # Create repeat exhausted rule
        svc.create_revocation_rule(
            trigger_type="repeat_exhausted",
            conditions={"max_repeats": 3},
            reason="repeats_exhausted",
            actor_id=doctor_user.id
        )
        
        # Evaluate
        triggered = svc.evaluate_revocation_rules(rx.id)
        
        assert len(triggered) >= 1
        assert any(t["trigger_type"] == "repeat_exhausted" for t in triggered)
    
    def test_evaluate_time_based_rule(self, test_session, doctor_user, patient_user):
        """Test evaluating time-based rule."""
        # Create prescription issued 60 days ago
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx.date_issued = datetime.now(SAST) - timedelta(days=60)
        test_session.commit()
        
        svc = RevocationService(db_session=test_session)
        
        # Create time-based rule (revoke after 30 days)
        svc.create_revocation_rule(
            trigger_type="time_based",
            conditions={"days_after_issue": 30},
            reason="time_limit_reached",
            actor_id=doctor_user.id
        )
        
        # Evaluate
        triggered = svc.evaluate_revocation_rules(rx.id)
        
        assert len(triggered) >= 1
        assert any(t["trigger_type"] == "time_based" for t in triggered)


# ============================================================================
# IMPACT ANALYSIS TESTS
# ============================================================================


class TestImpactAnalysis:
    """Test impact analysis functionality."""
    
    def test_analyze_revocation_impact_active(self, test_session, doctor_user, patient_user):
        """Test impact analysis for active prescription."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        result = svc.analyze_revocation_impact(rx.id)
        
        assert result["prescription_id"] == rx.id
        assert result["can_revoke"] is True
        assert result["impact_level"] == "low"
        assert result["affected_entities"]["patient"] is True
    
    def test_analyze_revocation_impact_already_revoked(self, test_session, doctor_user, patient_user):
        """Test impact analysis for already revoked prescription."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id, status="REVOKED")
        
        svc = RevocationService(db_session=test_session)
        result = svc.analyze_revocation_impact(rx.id)
        
        assert result["can_revoke"] is False
        assert "already revoked" in str(result["warnings"])
    
    def test_analyze_revocation_impact_with_repeats(self, test_session, doctor_user, patient_user):
        """Test impact analysis for prescription with repeats."""
        rx = _create_test_prescription(
            test_session, doctor_user.id, patient_user.id,
            is_repeat=True, repeat_count=2
        )
        
        svc = RevocationService(db_session=test_session)
        result = svc.analyze_revocation_impact(rx.id)
        
        assert result["impact_level"] == "medium"
        assert any("repeat" in str(w).lower() for w in result["warnings"])
    
    def test_analyze_bulk_impact(self, test_session, doctor_user, patient_user):
        """Test bulk impact analysis."""
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        result = svc.analyze_bulk_impact(
            filter_criteria={"patient_id": patient_user.id}
        )
        
        assert result["total_count"] == 2
        assert "by_impact_level" in result
        assert "by_status" in result
        assert patient_user.id in result["affected_patients"]


# ============================================================================
# DASHBOARD TESTS
# ============================================================================


class TestDashboard:
    """Test dashboard statistics."""
    
    def test_get_revocation_dashboard(self, test_session, doctor_user, patient_user):
        """Test dashboard statistics generation."""
        # Create and revoke some prescriptions
        rx1 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        rx2 = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Revoke them
        svc.revoke_prescription(rx1.id, doctor_user.id, "prescribing_error")
        svc.revoke_prescription(rx2.id, doctor_user.id, "patient_request")
        
        # Get dashboard
        dashboard = svc.get_revocation_dashboard(days=30)
        
        assert "period" in dashboard
        assert "summary" in dashboard
        assert dashboard["summary"]["total_revocations"] >= 2
        assert "by_reason" in dashboard
        assert "prescribing_error" in dashboard["by_reason"] or "patient_request" in dashboard["by_reason"]
        assert "trends" in dashboard
        assert "recent_activity" in dashboard
    
    def test_dashboard_with_bulk_revocation(self, test_session, doctor_user, patient_user):
        """Test dashboard includes bulk revocations."""
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        svc = RevocationService(db_session=test_session)
        
        # Bulk revoke
        svc.revoke_bulk(
            filter_criteria={"patient_id": patient_user.id},
            reason="bulk_test",
            actor_id=doctor_user.id
        )
        
        # Get dashboard
        dashboard = svc.get_revocation_dashboard(days=30)
        
        assert dashboard["summary"]["bulk_revocations"] >= 1
        assert "bulk_test" in dashboard["by_reason"]


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestRevocationAPI:
    """Test FastAPI endpoints for revocation."""
    
    async def test_api_revoke_prescription(self, async_client, doctor_user, patient_user, test_session):
        """Test API endpoint for single revocation."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        from app.core.auth import create_access_token
        token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        response = await async_client.post(
            f"/api/v1/prescriptions/{rx.id}/revoke",
            json={"reason": "prescribing_error"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["reason"] == "prescribing_error"
    
    async def test_api_bulk_revoke_preview(self, async_client, doctor_user, patient_user, test_session):
        """Test API endpoint for bulk revoke preview."""
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        from app.core.auth import create_access_token
        token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        response = await async_client.post(
            "/api/v1/prescriptions/bulk-revoke",
            json={
                "filter_criteria": {"patient_id": patient_user.id},
                "reason": "test",
                "preview_only": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["preview"] is True
        assert data["affected_count"] >= 2
    
    async def test_api_schedule_revocation(self, async_client, doctor_user, patient_user, test_session):
        """Test API endpoint for scheduling revocation."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        from app.core.auth import create_access_token
        token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        scheduled_time = (datetime.now(SAST) + timedelta(days=7)).isoformat()
        
        response = await async_client.post(
            "/api/v1/prescriptions/schedule-revoke",
            json={
                "prescription_id": rx.id,
                "scheduled_at": scheduled_time,
                "reason": "future_expiry"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["prescription_id"] == rx.id
        assert data["status"] == "scheduled"
    
    async def test_api_get_revocations_list(self, async_client, doctor_user, patient_user, test_session):
        """Test API endpoint for listing revocations."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        # Revoke it first
        svc = RevocationService(db_session=test_session)
        svc.revoke_prescription(rx.id, doctor_user.id, "test")
        
        from app.core.auth import create_access_token
        token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        response = await async_client.get(
            "/api/v1/prescriptions/revocations",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_api_analyze_impact(self, async_client, doctor_user, patient_user, test_session):
        """Test API endpoint for impact analysis."""
        rx = _create_test_prescription(test_session, doctor_user.id, patient_user.id)
        
        from app.core.auth import create_access_token
        token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        response = await async_client.get(
            f"/api/v1/prescriptions/{rx.id}/revoke-impact",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["prescription_id"] == rx.id
        assert "can_revoke" in data
        assert "impact_level" in data
    
    async def test_api_dashboard_admin_only(self, async_client, doctor_user, patient_user, test_session):
        """Test dashboard endpoint requires admin role."""
        from app.core.auth import create_access_token
        
        # Doctor token should be denied
        doctor_token = create_access_token({
            "sub": str(doctor_user.id),
            "username": doctor_user.username,
            "role": "doctor",
            "tenant_id": "default"
        })
        
        response = await async_client.get(
            "/api/v1/admin/revocations/dashboard",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 403
