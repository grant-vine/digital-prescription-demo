"""Tests for time-based prescription validation.

This is a TDD test suite for time validation - all tests FAIL until TASK-058 
implements the TimeValidationService. Tests cover:

- Validity period checks (prescription valid_from → valid_until)
- Expiration detection (7-day warning, 24-hour critical warning, expired state)
- Repeat interval calculation (eligibility for next refill)

All tests use pytest fixtures and mock datetime to test fixed time scenarios.
South African timezone (SAST - UTC+2) is used throughout.

Expected Failures (TDD Red Phase):
- ImportError: TimeValidationService doesn't exist yet
- AttributeError: Service methods don't exist yet
- All 10 tests FAIL - This is healthy for TDD red phase
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time


# ============================================================================
# FIXTURES - Time-based prescription data with FHIR R4 structure
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
def valid_prescription_fhir(now_sast):
    """Prescription issued today, expires in 30 days (VALID).
    
    FHIR R4 MedicationRequest structure with validity period.
    """
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-valid-001",
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
        "subject": {
            "reference": "Patient/123"
        },
        "authoredOn": now_sast.isoformat(),
        "requester": {
            "reference": "Practitioner/456"
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
        ],
        "dispenseRequest": {
            "validityPeriod": {
                "start": now_sast.isoformat(),
                "end": (now_sast + timedelta(days=30)).isoformat()
            },
            "numberOfRepeatsAllowed": 0,
            "quantity": {
                "value": 21,
                "unit": "tablets"
            },
            "expectedSupplyDuration": {
                "value": 30,
                "unit": "days"
            }
        }
    }


@pytest.fixture
def prescription_not_yet_valid_fhir(now_sast):
    """Prescription with valid_from TOMORROW (not yet valid)."""
    tomorrow = now_sast + timedelta(days=1)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-future-001",
        "status": "active",
        "authoredOn": tomorrow.isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=30)).isoformat()
            }
        }
    }


@pytest.fixture
def prescription_expired_fhir(now_sast):
    """Prescription valid_until was YESTERDAY (expired)."""
    yesterday = now_sast - timedelta(days=1)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-expired-001",
        "status": "revoked",
        "authoredOn": (yesterday - timedelta(days=30)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (yesterday - timedelta(days=30)).isoformat(),
                "end": yesterday.isoformat()
            }
        }
    }


@pytest.fixture
def prescription_expires_in_7_days_fhir(now_sast):
    """Prescription expires EXACTLY 7 days from now (warning threshold)."""
    expires_7_days = now_sast + timedelta(days=7)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-warning-7d-001",
        "status": "active",
        "authoredOn": (now_sast - timedelta(days=23)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=23)).isoformat(),
                "end": expires_7_days.isoformat()
            }
        }
    }


@pytest.fixture
def prescription_expires_in_24_hours_fhir(now_sast):
    """Prescription expires in EXACTLY 24 hours (critical warning)."""
    expires_24h = now_sast + timedelta(hours=24)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-critical-24h-001",
        "status": "active",
        "authoredOn": (now_sast - timedelta(days=29)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=29)).isoformat(),
                "end": expires_24h.isoformat()
            }
        }
    }


@pytest.fixture
def prescription_expires_in_8_days_fhir(now_sast):
    """Prescription expires in 8 days (no warning - more than 7 days)."""
    expires_8_days = now_sast + timedelta(days=8)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-no-warning-8d-001",
        "status": "active",
        "authoredOn": (now_sast - timedelta(days=22)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=22)).isoformat(),
                "end": expires_8_days.isoformat()
            }
        }
    }


@pytest.fixture
def prescription_with_repeats_fhir(now_sast):
    """Prescription with numberOfRepeatsAllowed = 2 (can refill twice).
    
    Last dispensed 30 days ago, interval = 28 days → ELIGIBLE NOW.
    """
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-repeats-001",
        "status": "active",
        "authoredOn": (now_sast - timedelta(days=60)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=60)).isoformat(),
                "end": (now_sast + timedelta(days=30)).isoformat()
            },
            "numberOfRepeatsAllowed": 2,
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
                "timing": {
                    "repeat": {
                        "boundsDuration": {
                            "value": 28,
                            "unit": "d"
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def prescription_recently_dispensed_fhir(now_sast):
    """Prescription last dispensed 10 days ago, interval = 28 days.
    
    NOT ELIGIBLE YET (need to wait 18 more days).
    """
    last_dispensed = now_sast - timedelta(days=10)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-recent-001",
        "status": "active",
        "authoredOn": (now_sast - timedelta(days=40)).isoformat(),
        "dispenseRequest": {
            "validityPeriod": {
                "start": (now_sast - timedelta(days=40)).isoformat(),
                "end": (now_sast + timedelta(days=20)).isoformat()
            },
            "numberOfRepeatsAllowed": 2,
            "quantity": {
                "value": 28,
                "unit": "tablets"
            },
            "expectedSupplyDuration": {
                "value": 28,
                "unit": "d"
            }
        },
        # In production, last_dispensed_at would be stored separately
        # For this test, we simulate it via fixture metadata
        "_last_dispensed_at": last_dispensed.isoformat()
    }


# ============================================================================
# VALIDITY PERIOD TESTS
# ============================================================================


@pytest.mark.asyncio
class TestValidityPeriod:
    """Test prescriptions within or outside validity period."""

    def test_prescription_within_validity_period(self, valid_prescription_fhir):
        """Test prescription issued today, expires in 30 days - should be VALID.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_validity_period(valid_prescription_fhir)
        
        assert result["is_valid"] is True
        assert result["status"] == "active"
        assert "expires_at" in result

    def test_prescription_not_yet_valid(self, prescription_not_yet_valid_fhir):
        """Test prescription with valid_from TOMORROW - should be INVALID.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_validity_period(prescription_not_yet_valid_fhir)
        
        assert result["is_valid"] is False
        assert result["status"] == "not_yet_valid"
        assert "valid_from" in result

    def test_prescription_expired(self, prescription_expired_fhir):
        """Test prescription with valid_until YESTERDAY - should be EXPIRED.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_validity_period(prescription_expired_fhir)
        
        assert result["is_valid"] is False
        assert result["status"] == "expired"
        assert result["expired"] is True


# ============================================================================
# EXPIRATION WARNING TESTS
# ============================================================================


@pytest.mark.asyncio
class TestExpirationWarnings:
    """Test expiration warning thresholds (7 days, 24 hours, expired)."""

    def test_warning_at_7_days(self, prescription_expires_in_7_days_fhir):
        """Test prescription expiring in exactly 7 days - should trigger warning.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_expiration_warnings(prescription_expires_in_7_days_fhir)
        
        assert result["warning_level"] == "7_day"
        assert result["should_notify"] is True
        assert result["notification_type"] == "expiration_warning_7d"

    def test_critical_warning_at_24_hours(self, prescription_expires_in_24_hours_fhir):
        """Test prescription expiring in 24 hours - should trigger CRITICAL warning.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_expiration_warnings(prescription_expires_in_24_hours_fhir)
        
        assert result["warning_level"] == "24_hour"
        assert result["should_notify"] is True
        assert result["notification_type"] == "expiration_critical_24h"
        assert result["urgency"] == "critical"

    def test_no_warning_at_8_days(self, prescription_expires_in_8_days_fhir):
        """Test prescription expiring in 8 days - should have NO warning.
        
        No warning if more than 7 days remain.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_expiration_warnings(prescription_expires_in_8_days_fhir)
        
        assert result["should_notify"] is False
        assert result.get("warning_level") is None


# ============================================================================
# REPEAT ELIGIBILITY TESTS (US-014)
# ============================================================================


@pytest.mark.asyncio
class TestRepeatEligibility:
    """Test repeat/refill eligibility calculations."""

    def test_eligible_for_refill_after_interval(self, prescription_with_repeats_fhir):
        """Test repeat eligibility after minimum interval has passed.
        
        Last dispensed 30 days ago, interval=28 days → ELIGIBLE.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        
        # Supply duration = 28 days (interval for next refill)
        result = service.check_repeat_eligibility(
            prescription_with_repeats_fhir,
            last_dispensed_at=(datetime.now(timezone(timedelta(hours=2))) - timedelta(days=30)).isoformat()
        )
        
        assert result["is_eligible"] is True
        assert result["repeats_remaining"] >= 1
        assert result["days_until_eligible"] <= 0

    def test_not_eligible_for_refill_too_soon(self, prescription_recently_dispensed_fhir):
        """Test that repeat NOT eligible when minimum interval not yet passed.
        
        Last dispensed 10 days ago, interval=28 days → NOT ELIGIBLE.
        Needs to wait 18 more days.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        
        result = service.check_repeat_eligibility(
            prescription_recently_dispensed_fhir,
            last_dispensed_at=(datetime.now(timezone(timedelta(hours=2))) - timedelta(days=10)).isoformat()
        )
        
        assert result["is_eligible"] is False
        assert result["days_until_eligible"] >= 18

    def test_repeat_count_decrements_after_dispense(self, prescription_with_repeats_fhir):
        """Test that numberOfRepeatsAllowed decrements after dispensing.
        
        Initial value: 2 repeats allowed
        After dispense: should be 1 repeat remaining
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        initial_repeats = prescription_with_repeats_fhir["dispenseRequest"]["numberOfRepeatsAllowed"]
        
        result = service.decrement_repeat_count(prescription_with_repeats_fhir)
        
        assert result["repeats_remaining"] == initial_repeats - 1
        assert result["repeats_used"] == 1

    def test_no_repeats_available(self, valid_prescription_fhir):
        """Test prescription with numberOfRepeatsAllowed = 0 (no refills).
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        
        result = service.check_repeat_eligibility(
            valid_prescription_fhir,
            last_dispensed_at=None
        )
        
        assert result["repeats_remaining"] == 0
        assert result["is_eligible"] is False


# ============================================================================
# TIMEZONE HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
class TestTimezoneHandling:
    """Test South African timezone (SAST - UTC+2) handling."""

    def test_sast_timezone_conversion(self, valid_prescription_fhir):
        """Test that dates are properly handled in SAST (UTC+2).
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_validity_period(valid_prescription_fhir)
        
        # Result should include timezone info
        assert "timezone" in result or "utc_offset" in result
        # SAST is UTC+2
        assert result.get("utc_offset") == 2 or "UTC+2" in str(result)

    @freeze_time("2026-02-12 10:00:00", tz_offset=2)
    def test_frozen_time_sast(self, valid_prescription_fhir):
        """Test with frozen time in SAST to ensure consistency.
        
        Uses freezegun to fix time at 2026-02-12 10:00:00 SAST.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        result = service.check_validity_period(valid_prescription_fhir)
        
        # With frozen time, results should be deterministic
        assert "is_valid" in result
        assert "expires_at" in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
class TestValidationIntegration:
    """Integration tests combining multiple validations."""

    def test_full_validation_workflow(self, valid_prescription_fhir):
        """Test complete validation workflow: validity → warnings → repeats.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        
        # 1. Check validity period
        validity_result = service.check_validity_period(valid_prescription_fhir)
        assert validity_result["is_valid"] is True
        
        # 2. Check expiration warnings
        warning_result = service.check_expiration_warnings(valid_prescription_fhir)
        assert "should_notify" in warning_result
        
        # 3. Check repeat eligibility
        repeat_result = service.check_repeat_eligibility(
            valid_prescription_fhir,
            last_dispensed_at=None
        )
        assert "is_eligible" in repeat_result

    def test_expired_prescription_no_repeats(self, prescription_expired_fhir):
        """Test that expired prescriptions cannot be refilled.
        
        EXPECTED FAILURE: TimeValidationService doesn't exist yet.
        """
        from app.services.validation import TimeValidationService
        
        service = TimeValidationService()
        
        # Expired prescriptions should not be eligible for repeats
        repeat_result = service.check_repeat_eligibility(
            prescription_expired_fhir,
            last_dispensed_at=None
        )
        
        assert repeat_result["is_eligible"] is False
        assert repeat_result.get("reason") == "prescription_expired"
