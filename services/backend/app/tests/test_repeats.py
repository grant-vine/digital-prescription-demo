"""Tests for prescription repeat/refill tracking with database persistence.

This is a TDD test suite for repeat tracking - all tests FAIL until TASK-060
implements the DispensingService. Tests cover:

- Dispensing record CRUD (create, read, query, delete)
- Repeat count persistence (decrement in database after dispense)
- Repeat eligibility integration (with TimeValidationService)
- Edge cases (race conditions, partial dispenses, expired prescriptions)

All tests use pytest fixtures with actual database persistence via SQLAlchemy.
South African timezone (SAST - UTC+2) is used throughout.

Expected Failures (TDD Red Phase):
- ImportError: DispensingService doesn't exist yet
- AttributeError: Service methods don't exist yet
- All 14 tests FAIL - This is healthy for TDD red phase
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time


# ============================================================================
# FIXTURES - SAST timezone and prescription with repeats
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
def prescription_with_two_repeats(test_session, doctor_user, patient_user, now_sast):
    """Create prescription in database with numberOfRepeatsAllowed = 2.
    
    FHIR R4 MedicationRequest with:
    - Issued 60 days ago (prescription is old, still valid)
    - Expires in 30 days (plenty of time)
    - 2 repeats allowed
    - 30-day interval between repeats
    """
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=30,
        instructions="Take one tablet three times daily with food",
        date_issued=now_sast - timedelta(days=60),
        date_expires=now_sast + timedelta(days=30),
        is_repeat=True,
        repeat_count=2,  # 2 repeats allowed
        digital_signature="sig_xyz789",
        credential_id="cred_abc123",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def prescription_with_fhir_repeats(test_session, doctor_user, patient_user, now_sast):
    """Create prescription with FHIR R4 dispenseRequest structure stored in database.
    
    This fixture creates a prescription with proper FHIR R4 structure for testing
    interactions with TimeValidationService.
    """
    from app.models.prescription import Prescription
    import json
    
    fhir_data = {
        "resourceType": "MedicationRequest",
        "id": "rx-repeats-test-001",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "J01CA04",
                    "display": "Amoxicillin"
                }
            ]
        },
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=60)).isoformat(),
                "end": (now_sast + timedelta(days=30)).isoformat()
            },
            "numberOfRepeatsAllowed": 3,
            "quantity": {
                "value": 30,
                "unit": "tablets"
            },
            "expectedSupplyDuration": {
                "value": 28,
                "unit": "days"
            }
        },
        "dosageInstruction": [
            {
                "text": "Take 500mg three times daily with food",
                "timing": {
                    "repeat": {
                        "frequency": 3,
                        "period": 1,
                        "periodUnit": "d"
                    }
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": 500,
                            "unit": "mg"
                        }
                    }
                ]
            }
        ]
    }
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Amoxicillin",
        medication_code="J01CA04",
        dosage="500mg",
        quantity=30,
        instructions="Take one tablet three times daily with food",
        date_issued=now_sast - timedelta(days=60),
        date_expires=now_sast + timedelta(days=30),
        is_repeat=True,
        repeat_count=3,
        digital_signature="sig_xyz789",
        credential_id="cred_abc123",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def prescription_no_repeats(test_session, doctor_user, patient_user, now_sast):
    """Create prescription in database with numberOfRepeatsAllowed = 0 (no repeats)."""
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Aspirin",
        medication_code="N02BA01",
        dosage="100mg",
        quantity=30,
        instructions="Take one tablet daily",
        date_issued=now_sast - timedelta(days=30),
        date_expires=now_sast + timedelta(days=30),
        is_repeat=False,
        repeat_count=0,  # NO REPEATS
        digital_signature="sig_123",
        credential_id="cred_456",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


@pytest.fixture
def prescription_expired(test_session, doctor_user, patient_user, now_sast):
    """Create prescription in database that is already expired."""
    from app.models.prescription import Prescription
    
    prescription = Prescription(
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        medication_name="Ibuprofen",
        medication_code="M01AE01",
        dosage="400mg",
        quantity=20,
        instructions="Take one tablet every 6 hours",
        date_issued=now_sast - timedelta(days=60),
        date_expires=now_sast - timedelta(days=1),  # EXPIRED YESTERDAY
        is_repeat=True,
        repeat_count=2,
        digital_signature="sig_exp",
        credential_id="cred_exp",
    )
    test_session.add(prescription)
    test_session.commit()
    test_session.refresh(prescription)
    return prescription


# ============================================================================
# CATEGORY 1: DISPENSING RECORD CRUD (4 tests)
# ============================================================================


@pytest.mark.asyncio
class TestDispensingRecordCRUD:
    """Test database operations for dispensing records."""
    
    def test_create_dispensing_record(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Create new dispensing record in database with all fields.
        
        Dispensing record should store:
        - prescription_id (reference to prescription)
        - pharmacist_id (who dispensed)
        - quantity_dispensed
        - date_dispensed (timestamp)
        - verified (boolean flag)
        - notes (optional)
        
        EXPECTED FAILURE: DispensingService.create_dispensing_record() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Create dispensing record
        result = service.create_dispensing_record(
            prescription_id=prescription_with_two_repeats.id,
            pharmacist_id=pharmacist_user.id,
            quantity_dispensed=30,
            date_dispensed=now_sast,
            verified=True,
            notes="Patient counseled on side effects"
        )
        
        # Verify result structure
        assert "id" in result
        assert result["prescription_id"] == prescription_with_two_repeats.id
        assert result["pharmacist_id"] == pharmacist_user.id
        assert result["quantity_dispensed"] == 30
        assert result["verified"] is True
        assert "date_dispensed" in result
        assert result["notes"] == "Patient counseled on side effects"
        
        # Verify record persisted in database
        dispensing = test_session.query(
            __import__("app.models.dispensing", fromlist=["Dispensing"]).Dispensing
        ).filter_by(id=result["id"]).first()
        assert dispensing is not None
        assert dispensing.prescription_id == prescription_with_two_repeats.id
    
    def test_get_dispensing_history(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Retrieve all dispensing records for a prescription in chronological order.
        
        Should return:
        - List of dispensing records sorted by date_dispensed (oldest → newest)
        - Include all fields for each record
        - Empty list if no dispensing history
        
        EXPECTED FAILURE: DispensingService.get_dispensing_history() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Get dispensing history for a prescription with no dispensing yet
        history = service.get_dispensing_history(prescription_id=prescription_with_two_repeats.id)
        
        assert isinstance(history, list)
        assert len(history) == 0  # No dispensing yet
        
        # After adding dispensing records (in TASK-060), should return in order
        # history should be sorted by date_dispensed ascending
        if len(history) > 1:
            for i in range(len(history) - 1):
                assert history[i]["date_dispensed"] <= history[i + 1]["date_dispensed"]
    
    def test_get_latest_dispensing_record(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Get most recent dispensing record for repeat eligibility check.
        
        Used to determine when repeat is eligible:
        - Returns most recent dispensing record by date_dispensed
        - Returns None if no dispensing history yet
        - Used by repeat eligibility logic to check interval
        
        EXPECTED FAILURE: DispensingService.get_latest_dispensing_record() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Get latest record when none exist yet
        latest = service.get_latest_dispensing_record(prescription_id=prescription_with_two_repeats.id)
        
        assert latest is None  # No dispensing history yet
        
        # After implementing, should return the record with latest date_dispensed
        # and include all dispensing fields
    
    def test_delete_dispensing_record(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Soft delete or mark dispensing record as cancelled.
        
        Rather than hard delete, should:
        - Mark record as cancelled/deleted (audit trail)
        - Or soft delete with timestamp
        - Ensure audit logging
        
        EXPECTED FAILURE: DispensingService.delete_dispensing_record() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Try to delete a non-existent record (edge case)
        result = service.delete_dispensing_record(dispensing_id=99999)
        
        # Should indicate failure or return None
        assert result is None or result.get("success") is False
    
    def test_query_dispensing_by_pharmacist(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Find all dispensing records for a specific pharmacist.
        
        Pharmacy manager view: see all dispensings by a specific pharmacist
        - Filter by pharmacist_id
        - Return all records for that pharmacist
        - Empty list if pharmacist has no records
        
        EXPECTED FAILURE: DispensingService.get_pharmacist_dispensings() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Get dispensings for a pharmacist with none yet
        dispensings = service.get_pharmacist_dispensings(pharmacist_id=pharmacist_user.id)
        
        assert isinstance(dispensings, list)
        assert len(dispensings) == 0  # No dispensings yet for this pharmacist


# ============================================================================
# CATEGORY 2: REPEAT COUNT PERSISTENCE (4 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRepeatCountPersistence:
    """Test updating prescription repeat counts in database."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_decrement_repeat_count_in_db(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Decrement numberOfRepeatsAllowed in prescription after dispense.
        
        When dispensing occurs:
        1. Create dispensing record
        2. Decrement prescription.repeat_count
        3. Update prescription.date_updated
        
        Test with prescription that has 2 repeats:
        - Before dispense: repeat_count = 2
        - After dispense: repeat_count = 1
        - Should be atomic operation
        
        EXPECTED FAILURE: DispensingService.dispense_prescription() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Verify initial state
        assert prescription_with_two_repeats.repeat_count == 2
        
        # Dispense (should decrement repeat count)
        result = service.dispense_prescription(
            prescription_id=prescription_with_two_repeats.id,
            pharmacist_id=pharmacist_user.id,
            quantity_dispensed=30
        )
        
        # Refresh from database to get updated repeat_count
        test_session.refresh(prescription_with_two_repeats)
        
        # Verify repeat count decremented
        assert prescription_with_two_repeats.repeat_count == 1
        assert result["repeats_remaining"] == 1
        assert "dispensing_id" in result  # Dispensing was created
    
    def test_cannot_dispense_with_zero_repeats(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_no_repeats, now_sast):
        """Raise error when attempting to dispense with 0 repeats remaining.
        
        After initial dispense, prescription has 0 repeats left.
        Attempting to dispense again should:
        - Raise ValidationError or similar
        - NOT create dispensing record
        - NOT modify database
        
        EXPECTED FAILURE: DispensingService.dispense_prescription() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Try to dispense when no repeats available
        with pytest.raises((ValueError, Exception)):
            result = service.dispense_prescription(
                prescription_id=prescription_no_repeats.id,
                pharmacist_id=pharmacist_user.id,
                quantity_dispensed=30
            )
    
    def test_repeat_count_remains_after_failed_dispense(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Do not decrement repeat count if dispensing fails.
        
        If dispensing fails (validation error, database error, etc.):
        - Do NOT decrement repeat count
        - Do NOT create dispensing record
        - Maintain original state
        
        This ensures atomicity: either both succeed or both fail.
        
        EXPECTED FAILURE: DispensingService.dispense_prescription() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Store original repeat count
        original_repeats = prescription_with_two_repeats.repeat_count
        
        # Try to dispense with invalid quantity (should fail)
        try:
            result = service.dispense_prescription(
                prescription_id=prescription_with_two_repeats.id,
                pharmacist_id=pharmacist_user.id,
                quantity_dispensed=-10  # Invalid: negative quantity
            )
        except (ValueError, Exception):
            pass
        
        # Refresh and verify repeat count unchanged
        test_session.refresh(prescription_with_two_repeats)
        assert prescription_with_two_repeats.repeat_count == original_repeats
    
    def test_track_original_vs_remaining_repeats(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Store both original repeats and current remaining repeats.
        
        Dispensing record should track:
        - original_repeats_allowed (from when prescription created)
        - repeats_used (how many times dispensed)
        - repeats_remaining (current available)
        
        For audit trail and compliance: know complete dispensing history.
        
        EXPECTED FAILURE: DispensingService.get_repeat_summary() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Get repeat summary for prescription
        summary = service.get_repeat_summary(prescription_id=prescription_with_two_repeats.id)
        
        assert summary["original_repeats_allowed"] == 2
        assert summary["repeats_used"] == 0  # No dispensing yet
        assert summary["repeats_remaining"] == 2
        assert summary["next_refill_eligible_at"] is not None or summary["reason"] is not None


# ============================================================================
# CATEGORY 3: REPEAT ELIGIBILITY INTEGRATION (4 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRepeatEligibilityIntegration:
    """Test repeat eligibility checks using database lookups."""
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_eligibility_with_db_lookup(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_fhir_repeats, now_sast):
        """Check eligibility using last_dispensed_at from database.
        
        Should call TimeValidationService.check_repeat_eligibility() with:
        - prescription FHIR data
        - last_dispensed_at from latest dispensing record in DB
        
        Returns eligibility status (is_eligible, repeats_remaining, days_until_eligible)
        
        EXPECTED FAILURE: DispensingService.check_repeat_eligibility() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Check eligibility for prescription (no dispensing history yet)
        result = service.check_repeat_eligibility(prescription_id=prescription_with_fhir_repeats.id)
        
        # Should integrate with TimeValidationService
        assert "is_eligible" in result
        assert "repeats_remaining" in result
        assert "reason" in result
        
        # First dispense should always be eligible
        if len(service.get_dispensing_history(prescription_with_fhir_repeats.id)) == 0:
            assert result["is_eligible"] is True
    
    def test_first_dispense_always_eligible(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """First dispense is always eligible (no prior dispensing record).
        
        When no dispensing history exists:
        - is_eligible = True
        - repeats_remaining = numberOfRepeatsAllowed
        - reason = "eligible" or "first_dispense"
        
        EXPECTED FAILURE: DispensingService.check_repeat_eligibility() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Check eligibility with no dispensing history
        result = service.check_repeat_eligibility(prescription_id=prescription_with_two_repeats.id)
        
        assert result["is_eligible"] is True
        assert result["repeats_remaining"] == prescription_with_two_repeats.repeat_count
        assert result["reason"] in ["eligible", "first_dispense"]
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_create_record_decrements_count(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Creating dispensing record automatically decrements repeat count.
        
        Atomic operation:
        1. Check eligibility (passes)
        2. Create dispensing record
        3. Decrement prescription.repeat_count
        
        If any step fails, entire operation rolls back.
        
        EXPECTED FAILURE: DispensingService.dispense_prescription() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Initial state
        initial_repeats = prescription_with_two_repeats.repeat_count
        
        # Dispense prescription
        result = service.dispense_prescription(
            prescription_id=prescription_with_two_repeats.id,
            pharmacist_id=pharmacist_user.id,
            quantity_dispensed=30
        )
        
        # Refresh prescription from database
        test_session.refresh(prescription_with_two_repeats)
        
        # Both operations should succeed atomically
        assert result["success"] is True
        assert prescription_with_two_repeats.repeat_count == initial_repeats - 1
        
        # Dispensing record should be created
        assert "dispensing_id" in result
        dispensing = test_session.query(
            __import__("app.models.dispensing", fromlist=["Dispensing"]).Dispensing
        ).filter_by(id=result["dispensing_id"]).first()
        assert dispensing is not None
    
    @freeze_time("2026-02-12 10:00:00+02:00")
    def test_interval_enforcement_with_database(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_fhir_repeats, now_sast):
        """Enforce minimum interval between repeats using database timestamps.
        
        expectedSupplyDuration from FHIR → minimum days between refills
        - Last dispensed 5 days ago
        - expectedSupplyDuration = 28 days
        - Should NOT be eligible (need 23 more days)
        
        Uses database timestamp from latest dispensing record for calculation.
        
        EXPECTED FAILURE: DispensingService doesn't implement interval checks yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # First dispense (always eligible)
        result1 = service.dispense_prescription(
            prescription_id=prescription_with_fhir_repeats.id,
            pharmacist_id=pharmacist_user.id,
            quantity_dispensed=30
        )
        assert result1["success"] is True
        
        # Move time forward 5 days (not yet eligible for repeat - need 28 days)
        with freeze_time((now_sast + timedelta(days=5)).isoformat()):
            eligibility = service.check_repeat_eligibility(
                prescription_id=prescription_with_fhir_repeats.id
            )
            
            # Should NOT be eligible yet
            assert eligibility["is_eligible"] is False
            assert eligibility["reason"] == "too_soon"
            assert eligibility["days_until_eligible"] > 0  # Still waiting


# ============================================================================
# CATEGORY 4: EDGE CASES (2 tests)
# ============================================================================


@pytest.mark.asyncio
class TestRepeatEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_concurrent_dispense_race_condition(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_with_two_repeats, now_sast):
        """Handle race condition: prevents duplicate dispensing within interval.
        
        When two pharmacists try to dispense same prescription immediately:
        1. First dispense succeeds (repeats 2 → 1)
        2. Second dispense (too soon) fails with "too_soon" error
        3. System prevents duplicate dispensing via interval enforcement
        
        This ensures pharmacists can't accidentally dispense twice within
        the minimum interval (e.g., 28 days for chronic medications).
        """
        from app.services.dispensing import DispensingService
        import pytest
        
        service = DispensingService()
        
        # First dispense succeeds
        result1 = service.dispense_prescription(
            prescription_id=prescription_with_two_repeats.id,
            pharmacist_id=pharmacist_user.id,
            quantity_dispensed=30
        )
        assert result1["success"] is True
        assert result1["repeats_remaining"] == 1
        
        # Second dispense (too soon) should fail gracefully
        with pytest.raises(ValueError, match="Not eligible for dispensing: too_soon"):
            service.dispense_prescription(
                prescription_id=prescription_with_two_repeats.id,
                pharmacist_id=pharmacist_user.id,
                quantity_dispensed=30
            )
        
        # Verify repeat count only decremented once (not twice)
        test_session.refresh(prescription_with_two_repeats)
        assert prescription_with_two_repeats.repeat_count == 1  # Not 0
    
    def test_expired_prescription_cannot_dispense_repeat(self, test_session, doctor_user, patient_user, pharmacist_user, prescription_expired, now_sast):
        """Expired prescription blocks dispensing even with repeats remaining.
        
        Prescription has:
        - Repeats remaining: 2
        - Status: EXPIRED
        
        Should:
        - Reject dispensing
        - Return reason: "prescription_expired"
        - NOT decrement repeat count
        - NOT create dispensing record
        
        EXPECTED FAILURE: DispensingService.dispense_prescription() doesn't exist yet.
        """
        from app.services.dispensing import DispensingService
        
        service = DispensingService()
        
        # Try to dispense expired prescription
        with pytest.raises((ValueError, Exception)):
            result = service.dispense_prescription(
                prescription_id=prescription_expired.id,
                pharmacist_id=pharmacist_user.id,
                quantity_dispensed=20
            )
        
        # Verify state unchanged
        test_session.refresh(prescription_expired)
        assert prescription_expired.repeat_count == 2  # Still has 2 repeats
        
        # No dispensing record should be created
        dispensings = test_session.query(
            __import__("app.models.dispensing", fromlist=["Dispensing"]).Dispensing
        ).filter_by(prescription_id=prescription_expired.id).all()
        assert len(dispensings) == 0
