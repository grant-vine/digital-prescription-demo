"""Tests for advanced time-based validation (US-022).

This test suite covers all new methods added to TimeValidationService for US-022:
- validate_business_hours: Pharmacy hours validation
- convert_timezone: Timezone conversion helper
- check_holiday: Holiday detection
- get_sa_public_holidays: SA public holidays list
- validate_controlled_substance_timing: Schedule 5/6/7 rules
- check_refill_interval: Minimum refill interval checking
- check_quantity_limits: Quantity per period tracking
- validate_scheduled_prescription: Future-dated prescription check
- get_next_valid_dispensing_time: Next dispensing time calculation
- validate_emergency_override: Emergency override validation
- get_time_validation_dashboard: Dashboard statistics

All tests use SAST (UTC+2) timezone throughout.
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
from fastapi.testclient import TestClient

from app.main import app
from app.services.validation import TimeValidationService


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def client():
    """Create FastAPI TestClient for making requests."""
    return TestClient(app)


@pytest.fixture
def sast_tz():
    """South African Standard Time timezone (UTC+2)."""
    return timezone(timedelta(hours=2))


@pytest.fixture
def validation_service():
    """Create a TimeValidationService instance."""
    return TimeValidationService()


@pytest.fixture
def standard_pharmacy_hours():
    """Standard pharmacy operating hours."""
    return {
        "type": "standard",
        "weekday_open": "08:00",
        "weekday_close": "17:00",
        "weekend_open": "09:00",
        "weekend_close": "13:00",
        "is_closed_weekends": False,
        "is_24hr": False
    }


@pytest.fixture
def extended_pharmacy_hours():
    """Extended pharmacy operating hours."""
    return {
        "type": "extended",
        "weekday_open": "08:00",
        "weekday_close": "20:00",
        "weekend_open": "09:00",
        "weekend_close": "17:00",
        "is_closed_weekends": False,
        "is_24hr": False
    }


@pytest.fixture
def pharmacy_closed_weekends():
    """Pharmacy closed on weekends."""
    return {
        "type": "standard",
        "weekday_open": "08:00",
        "weekday_close": "17:00",
        "is_closed_weekends": True,
        "is_24hr": False
    }


@pytest.fixture
def pharmacy_24hr():
    """24-hour pharmacy."""
    return {
        "type": "24hr",
        "is_24hr": True
    }


@pytest.fixture
def sample_prescription_fhir(sast_tz):
    """Sample FHIR prescription for testing."""
    now = datetime.now(sast_tz)
    return {
        "resourceType": "MedicationRequest",
        "id": "rx-test-001",
        "dispenseRequest": {
            "validityPeriod": {
                "start": now.isoformat(),
                "end": (now + timedelta(days=30)).isoformat()
            },
            "numberOfRepeatsAllowed": 2,
            "expectedSupplyDuration": {
                "value": 28,
                "unit": "days"
            }
        }
    }


# ============================================================================
# BUSINESS HOURS VALIDATION TESTS
# ============================================================================


class TestBusinessHoursValidation:
    """Test pharmacy business hours validation."""

    @freeze_time("2026-02-12 08:00:00")  # Thursday 08:00 UTC = 10:00 SAST
    def test_business_hours_during_open_weekday(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test validation during weekday open hours."""
        current_time = datetime.now(sast_tz)  # Get time in SAST
        result = validation_service.validate_business_hours(standard_pharmacy_hours, current_time)
        
        assert result["is_open"] is True
        assert result["dispensing_allowed"] is True
        assert result["hours_type"] == "weekday"
        assert result["is_weekend"] is False
        assert result["next_open_time"] is None

    @freeze_time("2026-02-12 16:00:00")  # Thursday 16:00 UTC = 18:00 SAST
    def test_business_hours_after_close_weekday(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test validation after weekday closing."""
        current_time = datetime.now(sast_tz)  # Get time in SAST
        result = validation_service.validate_business_hours(standard_pharmacy_hours, current_time)
        
        assert result["is_open"] is False
        assert result["dispensing_allowed"] is False
        assert result["hours_type"] == "weekday"
        assert result["next_open_time"] is not None

    @freeze_time("2026-02-14 08:00:00")  # Saturday 08:00 UTC = 10:00 SAST
    def test_business_hours_during_open_weekend(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test validation during weekend open hours."""
        current_time = datetime.now(sast_tz)  # Get time in SAST
        result = validation_service.validate_business_hours(standard_pharmacy_hours, current_time)
        
        assert result["is_open"] is True
        assert result["dispensing_allowed"] is True
        assert result["hours_type"] == "weekend"
        assert result["is_weekend"] is True

    @freeze_time("2026-02-14 13:00:00")  # Saturday 13:00 UTC = 15:00 SAST
    def test_business_hours_after_close_weekend(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test validation after weekend closing."""
        current_time = datetime.now(sast_tz)  # Get time in SAST
        result = validation_service.validate_business_hours(standard_pharmacy_hours, current_time)
        
        assert result["is_open"] is False
        assert result["dispensing_allowed"] is False
        assert result["is_weekend"] is True

    @freeze_time("2026-02-14 08:00:00")  # Saturday 08:00 UTC = 10:00 SAST
    def test_business_hours_closed_weekends(self, validation_service, pharmacy_closed_weekends, sast_tz):
        """Test validation when pharmacy closed on weekends."""
        current_time = datetime.now(sast_tz)  # Get time in SAST
        result = validation_service.validate_business_hours(pharmacy_closed_weekends, current_time)
        
        assert result["is_open"] is False
        assert result["dispensing_allowed"] is False
        assert result["hours_type"] == "closed_weekend"
        assert result["is_weekend"] is True
        assert result["next_open_time"] is not None

    def test_business_hours_24hr_pharmacy(self, validation_service, pharmacy_24hr):
        """Test validation for 24-hour pharmacy."""
        result = validation_service.validate_business_hours(pharmacy_24hr)
        
        assert result["is_open"] is True
        assert result["dispensing_allowed"] is True
        assert result["hours_type"] == "24hr"
        assert result["next_open_time"] is None


# ============================================================================
# TIMEZONE CONVERSION TESTS
# ============================================================================


class TestTimezoneConversion:
    """Test timezone conversion helper."""

    def test_convert_sast_to_utc(self, validation_service, sast_tz):
        """Test converting from SAST to UTC."""
        sast_time = datetime(2026, 2, 12, 12, 0, 0, tzinfo=sast_tz)  # 12:00 SAST
        utc = timezone.utc
        
        result = validation_service.convert_timezone(sast_time, sast_tz, utc)
        
        # SAST is UTC+2, so 12:00 SAST = 10:00 UTC
        assert result.hour == 10
        assert result.minute == 0
        assert result.tzinfo == utc

    def test_convert_utc_to_sast(self, validation_service, sast_tz):
        """Test converting from UTC to SAST."""
        utc_time = datetime(2026, 2, 12, 10, 0, 0, tzinfo=timezone.utc)  # 10:00 UTC
        
        result = validation_service.convert_timezone(utc_time, timezone.utc, sast_tz)
        
        # UTC is SAST-2, so 10:00 UTC = 12:00 SAST
        assert result.hour == 12
        assert result.minute == 0
        assert result.tzinfo == sast_tz

    def test_convert_naive_datetime(self, validation_service, sast_tz):
        """Test converting naive datetime (assumes source timezone)."""
        naive_time = datetime(2026, 2, 12, 12, 0, 0)  # No timezone
        utc = timezone.utc
        
        result = validation_service.convert_timezone(naive_time, sast_tz, utc)
        
        # Should assume SAST, so 12:00 SAST = 10:00 UTC
        assert result.hour == 10


# ============================================================================
# HOLIDAY DETECTION TESTS
# ============================================================================


class TestHolidayDetection:
    """Test South African public holiday detection."""

    def test_check_holiday_new_years_day_2026(self, validation_service, sast_tz):
        """Test detecting New Year's Day 2026."""
        new_years = datetime(2026, 1, 1, 12, 0, 0, tzinfo=sast_tz)
        
        result = validation_service.check_holiday(new_years)
        
        assert result["is_holiday"] is True
        assert result["holiday_name"] == "New Year's Day"
        assert result["region"] == "ZA"

    def test_check_holiday_freedom_day_2026(self, validation_service, sast_tz):
        """Test detecting Freedom Day 2026."""
        freedom_day = datetime(2026, 4, 27, 12, 0, 0, tzinfo=sast_tz)
        
        result = validation_service.check_holiday(freedom_day)
        
        assert result["is_holiday"] is True
        assert result["holiday_name"] == "Freedom Day"

    def test_check_holiday_not_holiday(self, validation_service, sast_tz):
        """Test non-holiday date."""
        regular_day = datetime(2026, 2, 12, 12, 0, 0, tzinfo=sast_tz)
        
        result = validation_service.check_holiday(regular_day)
        
        assert result["is_holiday"] is False
        assert result["holiday_name"] is None

    def test_check_holiday_different_region(self, validation_service, sast_tz):
        """Test holiday check for non-ZA region."""
        any_day = datetime(2026, 1, 1, 12, 0, 0, tzinfo=sast_tz)
        
        result = validation_service.check_holiday(any_day, region="US")
        
        assert result["is_holiday"] is False
        assert result["region"] == "US"


# ============================================================================
# SA PUBLIC HOLIDAYS LIST TESTS
# ============================================================================


class TestSAPublicHolidays:
    """Test South African public holidays list generation."""

    def test_get_sa_public_holidays_2026(self, validation_service):
        """Test getting 2026 SA public holidays."""
        result = validation_service.get_sa_public_holidays(2026)
        
        assert result["year"] == 2026
        assert result["count"] == 12
        
        holiday_dates = [h["date"] for h in result["holidays"]]
        assert "2026-01-01" in holiday_dates  # New Year's Day
        assert "2026-04-03" in holiday_dates  # Good Friday
        assert "2026-04-27" in holiday_dates  # Freedom Day
        assert "2026-12-25" in holiday_dates  # Christmas Day

    def test_get_sa_public_holidays_other_year(self, validation_service):
        """Test getting holidays for a different year (fixed dates only)."""
        result = validation_service.get_sa_public_holidays(2025)
        
        assert result["year"] == 2025
        # Only fixed-date holidays for non-2026 years
        assert result["count"] == 10
        
        holiday_dates = [h["date"] for h in result["holidays"]]
        assert "2025-01-01" in holiday_dates
        assert "2025-12-25" in holiday_dates


# ============================================================================
# CONTROLLED SUBSTANCE TIMING TESTS
# ============================================================================


class TestControlledSubstanceTiming:
    """Test controlled substance (Schedule 5/6/7) dispensing rules."""

    @freeze_time("2026-02-12 08:00:00")  # Thursday 08:00 UTC = 10:00 SAST
    def test_schedule_5_allowed_weekday(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test Schedule 5 dispensing during weekday hours."""
        medication_schedule = {
            "schedule": "5",
            "requires_supervision": False
        }
        current_time = datetime.now(sast_tz)
        
        result = validation_service.validate_controlled_substance_timing(
            medication_schedule,
            standard_pharmacy_hours,
            current_time
        )
        
        assert result["allowed"] is True
        assert result["schedule"] == "5"
        assert result["requires_pharmacist_supervision"] is False

    @freeze_time("2026-02-12 08:00:00")  # Thursday 08:00 UTC = 10:00 SAST
    def test_schedule_6_allowed_weekday(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test Schedule 6 dispensing during weekday hours."""
        medication_schedule = {
            "schedule": "6",
            "requires_supervision": True
        }
        current_time = datetime.now(sast_tz)
        
        result = validation_service.validate_controlled_substance_timing(
            medication_schedule,
            standard_pharmacy_hours,
            current_time
        )
        
        assert result["allowed"] is True
        assert result["schedule"] == "6"
        assert result["requires_pharmacist_supervision"] is True

    @freeze_time("2026-02-14 08:00:00")  # Saturday 08:00 UTC = 10:00 SAST
    def test_schedule_6_blocked_weekend_closed(self, validation_service, pharmacy_closed_weekends, sast_tz):
        """Test Schedule 6 blocked on weekends when pharmacy closed."""
        medication_schedule = {
            "schedule": "6",
            "requires_supervision": True
        }
        current_time = datetime.now(sast_tz)
        
        result = validation_service.validate_controlled_substance_timing(
            medication_schedule,
            pharmacy_closed_weekends,
            current_time
        )
        
        assert result["allowed"] is False
        assert result["schedule"] == "6"

    @freeze_time("2026-02-14 08:00:00")  # Saturday 08:00 UTC = 10:00 SAST
    def test_schedule_7_blocked_weekend(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test Schedule 7 blocked on weekends."""
        medication_schedule = {
            "schedule": "7",
            "requires_supervision": True
        }
        current_time = datetime.now(sast_tz)
        
        result = validation_service.validate_controlled_substance_timing(
            medication_schedule,
            standard_pharmacy_hours,
            current_time
        )
        
        assert result["allowed"] is False
        assert result["schedule"] == "7"


# ============================================================================
# REFILL INTERVAL TESTS
# ============================================================================


class TestRefillInterval:
    """Test minimum refill interval checking."""

    def test_refill_eligible_first_fill(self, validation_service, sample_prescription_fhir):
        """Test first fill is always eligible (no last_dispensed_at)."""
        result = validation_service.check_refill_interval(
            sample_prescription_fhir,
            last_dispensed_at=None
        )
        
        assert result["can_refill"] is True
        assert result["days_since_last"] is None
        assert result["days_until_eligible"] == 0

    @freeze_time("2026-02-12 08:00:00")
    def test_refill_too_soon(self, validation_service, sample_prescription_fhir, sast_tz):
        """Test refill blocked when too soon."""
        last_dispensed = (datetime.now(sast_tz) - timedelta(days=10)).isoformat()

        result = validation_service.check_refill_interval(
            sample_prescription_fhir,
            last_dispensed_at=last_dispensed
        )

        assert result["can_refill"] is False
        assert result["days_since_last"] == 10
        assert result["days_until_eligible"] > 0
        assert result["next_eligible_at"] is not None

    @freeze_time("2026-02-12 08:00:00")
    def test_refill_eligible_after_interval(self, validation_service, sample_prescription_fhir, sast_tz):
        """Test refill allowed after minimum interval."""
        last_dispensed = (datetime.now(sast_tz) - timedelta(days=30)).isoformat()

        result = validation_service.check_refill_interval(
            sample_prescription_fhir,
            last_dispensed_at=last_dispensed
        )

        assert result["can_refill"] is True
        assert result["days_since_last"] == 30
        assert result["days_until_eligible"] == 0

    @freeze_time("2026-02-12 08:00:00")
    def test_refill_interval_schedule_6_stricter(self, validation_service, sample_prescription_fhir, sast_tz):
        """Test Schedule 6 has stricter interval."""
        last_dispensed = (datetime.now(sast_tz) - timedelta(days=20)).isoformat()
        medication_schedule = {"schedule": "6"}

        result = validation_service.check_refill_interval(
            sample_prescription_fhir,
            last_dispensed_at=last_dispensed,
            medication_schedule=medication_schedule
        )

        # Schedule 6 requires 80% of 28 days = ~22 days
        assert result["can_refill"] is False
        assert result["min_interval_days"] == 22  # 28 * 0.8 rounded


# ============================================================================
# QUANTITY LIMITS TESTS
# ============================================================================


class TestQuantityLimits:
    """Test quantity limits per period."""

    def test_quantity_within_limits(self, validation_service):
        """Test quantity within allowed limits."""
        dispensing_history = [
            {"date_dispensed": "2026-01-15T10:00:00+02:00", "quantity": 10},
            {"date_dispensed": "2026-01-25T10:00:00+02:00", "quantity": 10},
        ]
        
        result = validation_service.check_quantity_limits(
            patient_id="patient-001",
            medication_code="J01CA04",
            dispensing_history=dispensing_history,
            period_days=30,
            max_quantity=50
        )
        
        assert result["within_limits"] is True
        assert result["total_dispensed"] == 20
        assert result["remaining_allowance"] == 30

    def test_quantity_exceeds_limits(self, validation_service):
        """Test quantity exceeds allowed limits."""
        dispensing_history = [
            {"date_dispensed": "2026-01-15T10:00:00+02:00", "quantity": 30},
            {"date_dispensed": "2026-01-25T10:00:00+02:00", "quantity": 30},
        ]
        
        result = validation_service.check_quantity_limits(
            patient_id="patient-001",
            medication_code="J01CA04",
            dispensing_history=dispensing_history,
            period_days=30,
            max_quantity=50
        )
        
        assert result["within_limits"] is False
        assert result["total_dispensed"] == 60
        assert result["remaining_allowance"] == 0

    def test_quantity_no_limits(self, validation_service):
        """Test with no maximum quantity set."""
        dispensing_history = [
            {"date_dispensed": "2026-01-15T10:00:00+02:00", "quantity": 100},
        ]
        
        result = validation_service.check_quantity_limits(
            patient_id="patient-001",
            medication_code="J01CA04",
            dispensing_history=dispensing_history,
            period_days=30,
            max_quantity=None
        )
        
        assert result["within_limits"] is True
        assert result["max_quantity"] is None
        assert result["remaining_allowance"] is None

    def test_quantity_old_dispensing_excluded(self, validation_service):
        """Test that old dispensing outside period is excluded."""
        dispensing_history = [
            {"date_dispensed": "2026-01-01T10:00:00+02:00", "quantity": 50},  # 42 days ago from Feb 12
            {"date_dispensed": "2026-02-01T10:00:00+02:00", "quantity": 10},  # 11 days ago
        ]
        
        result = validation_service.check_quantity_limits(
            patient_id="patient-001",
            medication_code="J01CA04",
            dispensing_history=dispensing_history,
            period_days=30,
            max_quantity=50
        )
        
        # Only the Feb 1 dispensing should count (within 30 days)
        assert result["total_dispensed"] == 10
        assert result["within_limits"] is True


# ============================================================================
# SCHEDULED PRESCRIPTION TESTS
# ============================================================================


class TestScheduledPrescription:
    """Test future-dated prescription validation."""

    @freeze_time("2026-02-12 08:00:00")
    def test_scheduled_prescription_not_yet_valid(self, validation_service, sast_tz):
        """Test future-dated prescription is not yet valid."""
        future_date = (datetime.now(sast_tz) + timedelta(days=7)).isoformat()
        prescription = {
            "resourceType": "MedicationRequest",
            "id": "rx-future",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": future_date,
                    "end": (datetime.now(sast_tz) + timedelta(days=37)).isoformat()
                }
            }
        }

        result = validation_service.validate_scheduled_prescription(prescription)

        assert result["is_valid"] is False
        assert result["status"] == "not_yet_valid"
        assert result["can_dispense"] is False
        assert result["activation_type"] == "scheduled"

    @freeze_time("2026-02-12 08:00:00")
    def test_scheduled_prescription_now_active(self, validation_service, sast_tz):
        """Test prescription becomes active on start date."""
        now = datetime.now(sast_tz)
        prescription = {
            "resourceType": "MedicationRequest",
            "id": "rx-active",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": now.isoformat(),
                    "end": (now + timedelta(days=30)).isoformat()
                }
            }
        }
        
        result = validation_service.validate_scheduled_prescription(prescription)
        
        assert result["is_valid"] is True
        assert result["status"] == "active"
        assert result["can_dispense"] is True
        assert result["activation_type"] == "immediate"


# ============================================================================
# NEXT DISPENSING TIME TESTS
# ============================================================================


class TestNextDispensingTime:
    """Test next valid dispensing time calculation."""

    @freeze_time("2026-02-12 08:00:00")
    def test_can_dispense_now(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test dispensing allowed now when pharmacy is open."""
        now = datetime.now(sast_tz)
        prescription = {
            "resourceType": "MedicationRequest",
            "id": "rx-001",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": now.isoformat(),
                    "end": (now + timedelta(days=30)).isoformat()
                }
            }
        }
        
        result = validation_service.get_next_valid_dispensing_time(
            prescription,
            standard_pharmacy_hours
        )
        
        assert result["can_dispense_now"] is True
        assert result["prescription_valid"] is True
        assert result["next_dispensing_time"] is not None
        assert len(result["reasons"]) == 0

    @freeze_time("2026-02-12 16:00:00")
    def test_cannot_dispense_pharmacy_closed(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test dispensing blocked when pharmacy closed."""
        now = datetime.now(sast_tz)
        prescription = {
            "resourceType": "MedicationRequest",
            "id": "rx-001",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": now.isoformat(),
                    "end": (now + timedelta(days=30)).isoformat()
                }
            }
        }
        
        result = validation_service.get_next_valid_dispensing_time(
            prescription,
            standard_pharmacy_hours
        )
        
        assert result["can_dispense_now"] is False
        assert result["prescription_valid"] is True
        assert result["next_dispensing_time"] is not None
        assert len(result["reasons"]) > 0


# ============================================================================
# EMERGENCY OVERRIDE TESTS
# ============================================================================


class TestEmergencyOverride:
    """Test emergency override validation."""

    def test_emergency_override_valid_code(self, validation_service, sample_prescription_fhir):
        """Test valid emergency override code."""
        result = validation_service.validate_emergency_override(
            override_code="EMRG-1234-ABCD",
            prescription_fhir=sample_prescription_fhir
        )
        
        assert result["valid"] is True
        assert result["dispensing_allowed"] is True
        assert result["override_type"] == "emergency"
        assert result["requires_audit"] is True
        assert result["audit_reason"] is not None

    def test_emergency_override_after_hours_code(self, validation_service, sample_prescription_fhir):
        """Test after-hours override code."""
        result = validation_service.validate_emergency_override(
            override_code="AHR-5678-EFGH",
            prescription_fhir=sample_prescription_fhir
        )
        
        assert result["valid"] is True
        assert result["dispensing_allowed"] is True
        assert result["override_type"] == "after_hours"

    def test_emergency_override_invalid_code(self, validation_service, sample_prescription_fhir):
        """Test invalid override code."""
        result = validation_service.validate_emergency_override(
            override_code="INVALID-CODE",
            prescription_fhir=sample_prescription_fhir
        )
        
        assert result["valid"] is False
        assert result["dispensing_allowed"] is False
        assert result["override_type"] is None
        assert result["requires_audit"] is False

    def test_emergency_override_invalid_prefix(self, validation_service, sample_prescription_fhir):
        """Test override code with invalid prefix."""
        result = validation_service.validate_emergency_override(
            override_code="WRONG-1234-ABCD",
            prescription_fhir=sample_prescription_fhir
        )
        
        assert result["valid"] is False
        assert "prefix" in result.get("reason", "").lower()


# ============================================================================
# DASHBOARD TESTS
# ============================================================================


class TestTimeValidationDashboard:
    """Test dashboard statistics generation."""

    def test_dashboard_with_pharmacy_hours(self, validation_service, standard_pharmacy_hours):
        """Test dashboard with pharmacy hours."""
        result = validation_service.get_time_validation_dashboard(
            pharmacy_hours=standard_pharmacy_hours,
            prescriptions=[]
        )
        
        assert "timestamp" in result
        assert "pharmacy_status" in result
        assert "prescription_summary" in result
        assert "alerts" in result
        assert result["pharmacy_status"]["is_open"] is not None

    def test_dashboard_prescription_counts(self, validation_service, standard_pharmacy_hours, sast_tz):
        """Test dashboard counts prescriptions correctly."""
        now = datetime.now(sast_tz)
        prescriptions = [
            {
                "id": "rx-001",
                "dispenseRequest": {
                    "validityPeriod": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(days=30)).isoformat()  # Normal
                    }
                }
            },
            {
                "id": "rx-002",
                "dispenseRequest": {
                    "validityPeriod": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(hours=12)).isoformat()  # Expires in 12h
                    }
                }
            },
        ]
        
        result = validation_service.get_time_validation_dashboard(
            pharmacy_hours=standard_pharmacy_hours,
            prescriptions=prescriptions
        )
        
        assert result["prescription_summary"]["total"] == 2
        assert result["prescription_summary"]["active"] == 2
        assert result["prescription_summary"]["expiring_24h"] == 1
        assert len(result["alerts"]) == 1
        assert result["alerts"][0]["level"] == "critical"

    def test_dashboard_no_prescriptions(self, validation_service):
        """Test dashboard with no prescriptions."""
        result = validation_service.get_time_validation_dashboard(
            pharmacy_hours=None,
            prescriptions=None
        )
        
        assert result["prescription_summary"]["total"] == 0
        assert result["prescription_summary"]["active"] == 0
        assert len(result["alerts"]) == 0


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================


class TestTimeValidationAPI:
    """Test API endpoints for time validation."""

    def test_get_time_validity_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/prescriptions/{id}/time-validity endpoint."""
        response = client.get(
            "/api/v1/prescriptions/rx-001/time-validity",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prescription_id"] == "rx-001"
        assert "is_valid" in data
        assert "status" in data
        assert "can_dispense" in data

    def test_get_pharmacy_hours_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/pharmacy/{id}/hours endpoint."""
        response = client.get(
            "/api/v1/pharmacy/pharmacy-001/hours",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pharmacy_id"] == "pharmacy-001"
        assert "is_open" in data
        assert "hours_type" in data

    def test_get_holidays_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/holidays endpoint."""
        response = client.get(
            "/api/v1/holidays?year=2026",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert data["count"] == 12
        assert len(data["holidays"]) == 12

    def test_get_patient_limits_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/controlled-substances/patient/{id}/limits endpoint."""
        response = client.get(
            "/api/v1/controlled-substances/patient/patient-001/limits?medication_code=J01CA04",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "patient-001"
        assert "within_limits" in data

    def test_emergency_override_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test POST /api/v1/emergency-override endpoint."""
        response = client.post(
            "/api/v1/emergency-override",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            json={
                "override_code": "EMRG-1234-ABCD",
                "prescription_id": "rx-001"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["dispensing_allowed"] is True

    def test_dashboard_endpoint_requires_admin(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/admin/time-validation/dashboard requires admin/doctor role."""
        response = client.get(
            "/api/v1/admin/time-validation/dashboard",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        # Doctor token should have access
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "pharmacy_status" in data
        assert "prescription_summary" in data
        assert "alerts" in data

    def test_patient_cannot_access_dashboard(self, client, valid_patient_jwt_token, override_get_db):
        """Test patient cannot access admin dashboard."""
        response = client.get(
            "/api/v1/admin/time-validation/dashboard",
            headers={"Authorization": f"Bearer {valid_patient_jwt_token}"}
        )

        # Patient token should be denied
        assert response.status_code == 403

    def test_timezone_convert_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test POST /api/v1/timezone/convert endpoint."""
        response = client.post(
            "/api/v1/timezone/convert",
            headers={"Authorization": f"Bearer {valid_jwt_token}"},
            json={
                "datetime_str": "2026-02-12T12:00:00+02:00",
                "from_timezone": "SAST",
                "to_timezone": "UTC"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "original_datetime" in data
        assert "converted_datetime" in data

    def test_check_holiday_endpoint(self, client, valid_jwt_token, override_get_db):
        """Test GET /api/v1/holidays/check endpoint."""
        response = client.get(
            "/api/v1/holidays/check?date=2026-01-01&region=ZA",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_holiday"] is True
        assert data["holiday_name"] == "New Year's Day"
        assert data["region"] == "ZA"

    def test_unauthorized_access_denied(self, client):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/prescriptions/rx-001/time-validity")

        assert response.status_code == 401
