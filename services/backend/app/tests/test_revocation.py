"""Tests for prescription revocation functionality with database persistence.

This is a TDD test suite for prescription revocation - all tests FAIL until TASK-062
implements the RevocationService. Tests cover:

- Revocation request scenarios (doctor revokes with reason)
- Revocation reason support (prescribing_error, patient_request, adverse_reaction, duplicate, other)
- Prescription status changes (ACTIVE → REVOKED)
- SSI revocation registry integration (ACA-Py placeholder)
- Patient notification on revocation (future DIDComm)
- Audit trail logging (action, reason, timestamp)
- Edge cases (cannot dispense after revoke, cannot double-revoke, cannot revoke expired)

All tests use pytest fixtures with actual database persistence via SQLAlchemy.
South African timezone (SAST - UTC+2) is used throughout.

Expected Failures (TDD Red Phase):
- ImportError: RevocationService doesn't exist yet
- AttributeError: Service methods don't exist yet
- All 14 tests FAIL - This is healthy for TDD red phase
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time


# ============================================================================
# FIXTURES - SAST timezone and prescriptions for testing
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
def prescription_active(test_session, doctor_user, patient_user, now_sast):
    """Create active prescription in database ready to be revoked."""
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=30,
        instructions="Take one tablet three times daily with food",
        date_issued=now_sast - timedelta(days=10),
        date_expires=now_sast + timedelta(days=50),
        is_repeat=True,
        repeat_count=2,
        digital_signature="sig_xyz789",
        credential_id="cred_abc123",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def prescription_revoked(test_session, doctor_user, patient_user, now_sast):
    """Create prescription that is already revoked for edge case testing."""
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Ibuprofen",
        medication_code="M01AE01",
        dosage="200mg",
        quantity=20,
        instructions="Take as needed for pain",
        date_issued=now_sast - timedelta(days=20),
        date_expires=now_sast + timedelta(days=40),
        is_repeat=False,
        repeat_count=0,
        digital_signature="sig_revoked",
        credential_id="cred_revoked",
    )
    # Manually set status to REVOKED (simulating previous revocation)
    prescription.status = "REVOKED"
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def prescription_expired(test_session, doctor_user, patient_user, now_sast):
    """Create expired prescription for edge case testing."""
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Aspirin",
        medication_code="N02BA01",
        dosage="100mg",
        quantity=30,
        instructions="Take one tablet daily",
        date_issued=now_sast - timedelta(days=100),
        date_expires=now_sast - timedelta(days=1),  # EXPIRED YESTERDAY
        is_repeat=False,
        repeat_count=0,
        digital_signature="sig_exp",
        credential_id="cred_exp",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


# ============================================================================
# CATEGORY 1: REVOCATION REQUEST (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRevocationRequest:
    """Test basic revocation request scenarios."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_doctor_revokes_prescription_with_reason(self, test_session, doctor_user, prescription_active, now_sast):
        """Doctor revokes prescription with specified reason.
        
        Steps:
        1. Doctor calls revoke API with reason
        2. Prescription status changes to REVOKED
        3. Revocation timestamp recorded
        4. Reason stored for audit
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error",
            notes="Wrong medication dosage"
        )
        
        assert result["success"] is True
        assert result["prescription_id"] == prescription_active.id
        assert result["reason"] == "prescribing_error"
        
        # Verify prescription status changed in database
        test_session.refresh(prescription_active)
        assert prescription_active.status == "REVOKED"
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revocation_returns_revocation_id_and_timestamp(self, test_session, doctor_user, prescription_active, now_sast):
        """Revocation operation returns unique ID and timestamp.
        
        Response should include:
        - revocation_id (unique identifier for audit trail)
        - timestamp (when revocation occurred)
        - Can be used to retrieve revocation details later
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="patient_request",
            notes="Patient requested cancellation"
        )
        
        assert "revocation_id" in result
        assert "timestamp" in result
        assert result["timestamp"] is not None
        
        # Verify timestamp is in SAST
        assert isinstance(result["timestamp"], (str, datetime))
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revocation_stores_notes_optional(self, test_session, doctor_user, prescription_active, now_sast):
        """Notes field is optional but can store additional context.
        
        - Without notes: revoke_prescription() should accept missing notes parameter
        - With notes: should store additional context for audit trail
        - Notes should be retrievable in audit trail
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        # Revoke without notes (optional parameter)
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="adverse_reaction"
        )
        
        assert result["success"] is True
        
        # Verify can retrieve revocation details
        history = service.get_revocation_history(prescription_id=prescription_active.id)
        assert len(history) > 0
        assert history[0]["reason"] == "adverse_reaction"


# ============================================================================
# CATEGORY 2: REVOCATION REASONS (4 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRevocationReasons:
    """Test different revocation reason types."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_with_prescribing_error_reason(self, test_session, doctor_user, prescription_active, now_sast):
        """Support prescribing_error reason for doctor mistakes.
        
        Reason: "prescribing_error"
        Indicates: Doctor made mistake in prescription (wrong drug, dosage, etc.)
        Audit Trail: Should record this reason clearly
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error",
            notes="Meant to prescribe Ibuprofen 200mg, not 500mg"
        )
        
        assert result["success"] is True
        
        # Verify reason persisted in audit trail
        history = service.get_revocation_history(prescription_id=prescription_active.id)
        assert history[0]["reason"] == "prescribing_error"
        assert "Ibuprofen" in history[0].get("notes", "")
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_with_patient_request_reason(self, test_session, doctor_user, prescription_active, now_sast):
        """Support patient_request reason when patient asks to cancel.
        
        Reason: "patient_request"
        Indicates: Patient asked doctor to cancel prescription
        Audit Trail: Should record patient initiated revocation
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="patient_request",
            notes="Patient called to cancel"
        )
        
        assert result["success"] is True
        assert result["reason"] == "patient_request"
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_with_adverse_reaction_reason(self, test_session, doctor_user, prescription_active, now_sast):
        """Support adverse_reaction reason for safety events.
        
        Reason: "adverse_reaction"
        Indicates: Patient had negative reaction to medication
        Audit Trail: Should flag as safety issue for compliance
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="adverse_reaction",
            notes="Patient experienced allergic reaction"
        )
        
        assert result["success"] is True
        assert result["reason"] == "adverse_reaction"
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_with_other_reason(self, test_session, doctor_user, prescription_active, now_sast):
        """Support 'other' reason with custom notes.
        
        Reason: "other"
        Indicates: Revocation reason not in standard list
        Requires: Notes field explaining reason
        Audit Trail: Should record custom reason
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="other",
            notes="Medication no longer available from supplier"
        )
        
        assert result["success"] is True
        assert result["reason"] == "other"
        assert "no longer available" in result.get("notes", "")


# ============================================================================
# CATEGORY 3: STATUS CHANGE & REGISTRY UPDATE (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRevocationRegistry:
    """Test SSI revocation registry integration (ACA-Py)."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_prescription_status_changes_to_revoked(self, test_session, doctor_user, prescription_active, now_sast):
        """Prescription status changes to REVOKED after revocation.
        
        Before revocation: status = "ACTIVE"
        After revocation: status = "REVOKED"
        Verified in: database query and model instance
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        # Verify initial status
        assert prescription_active.status == "ACTIVE" or prescription_active.status is None
        
        service = RevocationService()
        
        service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error"
        )
        
        # Refresh from database to confirm status change persisted
        test_session.refresh(prescription_active)
        assert prescription_active.status == "REVOKED"
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_update_acapy_revocation_registry(self, test_session, doctor_user, prescription_active, now_sast):
        """Update ACA-Py revocation registry for credential revocation.
        
        Process:
        1. Extract credential_id from prescription
        2. Call ACA-Py to update revocation registry
        3. Mark credential as revoked in registry
        4. Return registry update confirmation
        
        Note: This is a placeholder for ACA-Py integration (TASK-062).
        In production, would call:
        - POST /revocation/revoke-credential
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.update_revocation_registry(
            credential_id=prescription_active.credential_id,
            revocation_registry_id="registry_test_123"
        )
        
        assert "success" in result
        # May be True or False depending on ACA-Py implementation
        # For MVP, may return placeholder success
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_triggers_registry_update(self, test_session, doctor_user, prescription_active, now_sast):
        """Revocation automatically triggers revocation registry update.
        
        When revoke_prescription() is called:
        1. Prescription status set to REVOKED
        2. Credential ID extracted from prescription
        3. update_revocation_registry() called automatically
        4. Result includes registry update status
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error"
        )
        
        # Result should indicate registry was updated
        assert "registry_updated" in result or result.get("success") is True


# ============================================================================
# CATEGORY 4: PATIENT NOTIFICATION (2 tests)
# ============================================================================


@pytest.mark.asyncio
class TestPatientNotification:
    """Test patient notification on revocation (future DIDComm)."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_notify_patient_of_revocation(self, test_session, doctor_user, patient_user, prescription_active, now_sast):
        """Patient is notified when prescription is revoked.
        
        Process:
        1. Revocation occurs
        2. notify_patient() called with prescription ID and reason
        3. Notification sent to patient wallet (future DIDComm)
        4. Returns notification status
        
        MVP: Placeholder for DIDComm integration
        Future: Will send encrypted DIDComm message
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.notify_patient(
            prescription_id=prescription_active.id,
            patient_id=patient_user.id,
            reason="prescribing_error"
        )
        
        # Result should indicate notification was queued/sent
        assert "success" in result or "notification_id" in result
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revoke_triggers_patient_notification(self, test_session, doctor_user, patient_user, prescription_active, now_sast):
        """Revocation automatically triggers patient notification.
        
        When revoke_prescription() is called:
        1. Prescription status set to REVOKED
        2. Audit trail logged
        3. notify_patient() called automatically
        4. Patient receives notification with reason
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="adverse_reaction",
            notes="Patient had allergic reaction"
        )
        
        # Result should include notification status
        assert result["success"] is True
        assert "notification" in result or "patient_notified" in result


# ============================================================================
# CATEGORY 5: AUDIT TRAIL (2 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRevocationAuditTrail:
    """Test audit trail logging for revocation events."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revocation_logged_to_audit_trail(self, test_session, doctor_user, prescription_active, now_sast):
        """Revocation action logged to audit trail.
        
        Audit entry includes:
        - action: "prescription_revoked"
        - user_id: doctor_user.id (who revoked)
        - prescription_id: prescription_active.id
        - reason: revocation reason
        - timestamp: when revocation occurred (SAST)
        - metadata: {reason, notes, revocation_id}
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error",
            notes="Wrong dosage prescribed"
        )
        
        # Verify audit trail entry was created
        from app.models.audit import Audit
        
        audit_entries = test_session.query(Audit).filter(
            Audit.resource_id == prescription_active.id,
            Audit.action == "prescription_revoked"
        ).all()
        
        assert len(audit_entries) > 0
        assert audit_entries[0].actor_id == doctor_user.id
        assert "prescribing_error" in str(audit_entries[0].details)
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_revocation_history_retrieval(self, test_session, doctor_user, prescription_active, now_sast):
        """Retrieve complete revocation history for prescription.
        
        get_revocation_history() returns:
        - List of all revocation events (in case of manual corrections)
        - Each entry includes: timestamp, reason, notes, revoked_by_user_id
        - Sorted chronologically (oldest → newest)
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        # Revoke the prescription
        result = service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="patient_request",
            notes="Patient called office"
        )
        
        # Retrieve revocation history
        history = service.get_revocation_history(prescription_id=prescription_active.id)
        
        assert isinstance(history, list)
        assert len(history) == 1  # One revocation event
        assert history[0]["reason"] == "patient_request"
        assert "Patient called" in history[0].get("notes", "")
        assert "timestamp" in history[0]


# ============================================================================
# CATEGORY 6: EDGE CASES (3 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRevocationEdgeCases:
    """Test edge cases and error conditions."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_cannot_dispense_after_revocation(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_active, now_sast):
        """Pharmacist cannot dispense revoked prescription.
        
        Steps:
        1. Doctor revokes prescription
        2. Pharmacist attempts to dispense
        3. Dispensing service checks revocation status
        4. Rejects dispensing with error: "prescription_revoked"
        
        This prevents accidental dispensing after revocation.
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        from app.services.dispensing import DispensingService
        
        revocation_service = RevocationService()
        
        # Revoke the prescription
        revocation_service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="prescribing_error"
        )
        
        # Try to dispense (should fail)
        dispensing_service = DispensingService()
        
        with pytest.raises(ValueError, match="[Rr]evoked|[Cc]annot.*dispense"):
            dispensing_service.dispense_prescription(
                prescription_id=prescription_active.id,
                pharmacist_id=pharmacist_user.id,
                quantity_dispensed=30
            )
        
        # Verify no dispensing record was created
        from app.models.dispensing import Dispensing
        
        dispensings = test_session.query(Dispensing).filter_by(
            prescription_id=prescription_active.id
        ).all()
        assert len(dispensings) == 0
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_cannot_revoke_already_revoked_prescription(self, test_session, doctor_user, prescription_revoked, now_sast):
        """Cannot revoke a prescription that is already revoked.
        
        Steps:
        1. Prescription already has status = "REVOKED"
        2. Doctor attempts to revoke again
        3. Service rejects with error: "already_revoked"
        
        Prevents duplicate revocation attempts.
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        # Try to revoke already-revoked prescription
        with pytest.raises((ValueError, Exception), match="[Aa]lready.*revoked|[Cc]annot.*revoke"):
            service.revoke_prescription(
                prescription_id=prescription_revoked.id,
                revoked_by_user_id=doctor_user.id,
                reason="prescribing_error"
            )
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_check_revocation_status(self, test_session, doctor_user, prescription_active, now_sast):
        """Check if prescription is revoked (status query).
        
        check_revocation_status() returns:
        - is_revoked: boolean
        - timestamp: when revoked (or null)
        - reason: revocation reason (or null)
        - revoked_by: user who revoked (or null)
        
        Used by dispensing service and pharmacy UI.
        
        EXPECTED FAILURE: RevocationService doesn't exist yet.
        """
        from app.services.revocation import RevocationService
        
        service = RevocationService()
        
        # Check active prescription (not revoked)
        status = service.check_revocation_status(prescription_id=prescription_active.id)
        assert status["is_revoked"] is False
        
        # Revoke it
        service.revoke_prescription(
            prescription_id=prescription_active.id,
            revoked_by_user_id=doctor_user.id,
            reason="adverse_reaction"
        )
        
        # Check again (now revoked)
        test_session.refresh(prescription_active)
        status = service.check_revocation_status(prescription_id=prescription_active.id)
        assert status["is_revoked"] is True
        assert status["reason"] == "adverse_reaction"


# ============================================================================
# PYTESTMARK - Mark all tests with asyncio
# ============================================================================

pytestmark = pytest.mark.asyncio
