"""Time-based prescription validation service.

Implements US-012, US-013, US-014 for:
- Validity period checks (valid_from → valid_until)
- Expiration warnings (7-day, 24-hour thresholds)
- Repeat/refill eligibility calculations

All dates are handled in SAST (UTC+2) timezone.
FHIR R4 MedicationRequest structures with ISO8601 dates.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


class TimeValidationService:
    """Service for time-based prescription validation.
    
    Validates:
    1. Prescription validity window (valid_from → valid_until)
    2. Expiration warnings (7-day, 24-hour critical)
    3. Repeat/refill eligibility (interval + repeat count)
    """

    # SAST timezone (UTC+2)
    SAST = timezone(timedelta(hours=2))
    
    # Warning thresholds
    WARNING_7_DAYS = 7 * 24  # hours
    WARNING_24_HOURS = 24    # hours

    def __init__(self, tenant_id: str = "default"):
        """Initialize validation service."""
        self.tenant_id = tenant_id

    def check_validity_period(self, prescription_fhir: Dict[str, Any]) -> Dict[str, Any]:
        """Check if prescription is within validity period.
        
        Returns three possible states:
        - "active": prescription is valid NOW
        - "not_yet_valid": prescription valid_from is in the future
        - "expired": prescription valid_until has passed
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
        
        Returns:
            Dict with keys:
            - is_valid: bool (True if active/valid right now)
            - status: str ("active" | "not_yet_valid" | "expired")
            - valid_from: str (ISO8601 start date)
            - expires_at: str (ISO8601 end date)
            - expired: bool (True if past valid_until)
            - days_remaining: int (days until expiration, negative if expired)
            - utc_offset: int (SAST offset = 2)
        """
        # Extract validity period from FHIR dispenseRequest
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        validity_period = dispense_request.get("validityPeriod", {})
        
        # Parse ISO8601 dates
        valid_from_str = validity_period.get("start")
        valid_until_str = validity_period.get("end")
        
        if not valid_from_str or not valid_until_str:
            return {
                "is_valid": False,
                "status": "unknown",
                "error": "Missing validityPeriod in prescription"
            }
        
        # Parse dates (handle both with and without timezone)
        valid_from = self._parse_iso8601(valid_from_str)
        valid_until = self._parse_iso8601(valid_until_str)
        now = datetime.now(self.SAST)
        
        # Determine status
        if now < valid_from:
            status = "not_yet_valid"
            is_valid = False
        elif now > valid_until:
            status = "expired"
            is_valid = False
        else:
            status = "active"
            is_valid = True
        
        # Calculate days remaining (negative if expired)
        time_remaining = valid_until - now
        days_remaining = time_remaining.days
        
        return {
            "is_valid": is_valid,
            "status": status,
            "valid_from": valid_from.isoformat(),
            "expires_at": valid_until.isoformat(),
            "expired": status == "expired",
            "days_remaining": days_remaining,
            "utc_offset": 2,  # SAST
        }

    def check_expiration_warnings(self, prescription_fhir: Dict[str, Any]) -> Dict[str, Any]:
        """Check for expiration warnings at 7-day and 24-hour thresholds.
        
        Warning levels:
        - "24_hour": expires within 24 hours (CRITICAL)
        - "7_day": expires within 7 days but more than 24 hours
        - None: expires in more than 7 days
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
        
        Returns:
            Dict with keys:
            - should_notify: bool (True if warning triggered)
            - warning_level: str | None ("24_hour" | "7_day" | None)
            - notification_type: str | None ("expiration_critical_24h" | "expiration_warning_7d" | None)
            - urgency: str | None ("critical" | "warning" | None)
            - hours_remaining: int
            - expires_at: str (ISO8601)
        """
        # Extract validity period
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        validity_period = dispense_request.get("validityPeriod", {})
        valid_until_str = validity_period.get("end")
        
        if not valid_until_str:
            return {
                "should_notify": False,
                "warning_level": None,
                "notification_type": None
            }
        
        # Parse date and calculate time remaining
        valid_until = self._parse_iso8601(valid_until_str)
        now = datetime.now(self.SAST)
        
        time_remaining = valid_until - now
        hours_remaining = time_remaining.total_seconds() / 3600
        
        # Determine warning level
        if hours_remaining <= self.WARNING_24_HOURS and hours_remaining > 0:
            # Within 24 hours (critical)
            return {
                "should_notify": True,
                "warning_level": "24_hour",
                "notification_type": "expiration_critical_24h",
                "urgency": "critical",
                "hours_remaining": int(hours_remaining),
                "expires_at": valid_until.isoformat()
            }
        elif hours_remaining <= self.WARNING_7_DAYS and hours_remaining > self.WARNING_24_HOURS:
            # Within 7 days but more than 24 hours
            return {
                "should_notify": True,
                "warning_level": "7_day",
                "notification_type": "expiration_warning_7d",
                "urgency": "warning",
                "hours_remaining": int(hours_remaining),
                "expires_at": valid_until.isoformat()
            }
        else:
            # More than 7 days away, or already expired
            return {
                "should_notify": False,
                "warning_level": None,
                "notification_type": None,
                "hours_remaining": int(hours_remaining),
                "expires_at": valid_until.isoformat()
            }

    def check_repeat_eligibility(
        self,
        prescription_fhir: Dict[str, Any],
        last_dispensed_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if prescription is eligible for repeat/refill.
        
        Eligibility requires:
        1. numberOfRepeatsAllowed > 0
        2. Prescription still within validity period
        3. At least expectedSupplyDuration has passed since last dispense
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
            last_dispensed_at: ISO8601 datetime of last dispensing, or None
        
        Returns:
            Dict with keys:
            - is_eligible: bool (True if can refill now)
            - repeats_remaining: int (0 if no repeats, or numberOfRepeatsAllowed)
            - days_until_eligible: int (0 if eligible now, positive if not yet, negative if expired)
            - reason: str | None ("no_repeats" | "prescription_expired" | "too_soon" | "eligible")
            - last_dispensed_at: str | None (ISO8601 of last dispense)
            - next_eligible_at: str | None (ISO8601 when next eligible)
        """
        # Check validity period FIRST (most critical)
        validity_check = self.check_validity_period(prescription_fhir)
        if not validity_check["is_valid"]:
            dispense_request = prescription_fhir.get("dispenseRequest", {})
            repeats_allowed = dispense_request.get("numberOfRepeatsAllowed", 0)
            return {
                "is_eligible": False,
                "repeats_remaining": repeats_allowed,
                "days_until_eligible": -1,
                "reason": "prescription_expired",
                "last_dispensed_at": last_dispensed_at
            }
        
        # Get repeat count
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        repeats_allowed = dispense_request.get("numberOfRepeatsAllowed", 0)
        
        # No repeats available
        if repeats_allowed <= 0:
            return {
                "is_eligible": False,
                "repeats_remaining": 0,
                "days_until_eligible": 0,
                "reason": "no_repeats",
                "last_dispensed_at": last_dispensed_at
            }
        
        # If no last_dispensed_at, it's the first dispensing (eligible)
        if not last_dispensed_at:
            return {
                "is_eligible": True,
                "repeats_remaining": repeats_allowed,
                "days_until_eligible": 0,
                "reason": "eligible",
                "last_dispensed_at": None,
                "next_eligible_at": None
            }
        
        # Parse last dispensed date
        last_dispensed = self._parse_iso8601(last_dispensed_at)
        now = datetime.now(self.SAST)
        
        # Get expected supply duration (interval between repeats)
        expected_supply = dispense_request.get("expectedSupplyDuration", {})
        interval_days = expected_supply.get("value", 28)  # default 28 days
        
        # Calculate when next refill is eligible
        next_eligible = last_dispensed + timedelta(days=interval_days)
        time_until_eligible = next_eligible - now
        days_until_eligible = time_until_eligible.days
        
        # Check if eligible
        if now >= next_eligible:
            is_eligible = True
            reason = "eligible"
            days_until = 0
        else:
            is_eligible = False
            reason = "too_soon"
            # Round up if there are remaining hours
            days_until = days_until_eligible if time_until_eligible.total_seconds() % 86400 == 0 else days_until_eligible + 1
        
        return {
            "is_eligible": is_eligible,
            "repeats_remaining": repeats_allowed,
            "days_until_eligible": days_until,
            "reason": reason,
            "last_dispensed_at": last_dispensed_at,
            "next_eligible_at": next_eligible.isoformat()
        }

    def decrement_repeat_count(self, prescription_fhir: Dict[str, Any]) -> Dict[str, Any]:
        """Decrement numberOfRepeatsAllowed after a refill.
        
        This should be called AFTER dispensing to record the refill.
        In production, this would update the prescription in the database.
        For this test, it returns what the new count would be.
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
        
        Returns:
            Dict with keys:
            - repeats_remaining: int (numberOfRepeatsAllowed - 1)
            - repeats_used: int (1)
            - original_repeats: int (original numberOfRepeatsAllowed)
        """
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        current_repeats = dispense_request.get("numberOfRepeatsAllowed", 0)
        
        # Calculate new count
        new_repeats = max(0, current_repeats - 1)
        
        return {
            "repeats_remaining": new_repeats,
            "repeats_used": 1,
            "original_repeats": current_repeats
        }

    # ========================================================================
    # Private helper methods
    # ========================================================================

    def _parse_iso8601(self, date_str: str) -> datetime:
        """Parse ISO8601 date string, handling timezone-aware and naive dates.
        
        Args:
            date_str: ISO8601 format date string
        
        Returns:
            datetime object in SAST timezone
        """
        # Try parsing with timezone info first
        try:
            dt = datetime.fromisoformat(date_str)
            # If no timezone, assume SAST
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.SAST)
            else:
                # Convert to SAST if it has different timezone
                dt = dt.astimezone(self.SAST)
            return dt
        except (ValueError, TypeError):
            # Fallback for other formats
            raise ValueError(f"Cannot parse date: {date_str}")

    # ========================================================================
    # US-022: Advanced Time-Based Validation Methods
    # ========================================================================

    def validate_business_hours(
        self,
        pharmacy_hours: Dict[str, Any],
        current_time: Optional[datetime] = None,
        medication_schedule: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if dispensing is allowed based on pharmacy business hours.
        
        Validates:
        - Standard business hours (e.g., 08:00-17:00)
        - Extended hours (e.g., 08:00-20:00)
        - Weekend hours (different schedule)
        - Holiday closures
        - 24-hour pharmacy (always open)
        
        Args:
            pharmacy_hours: Dict with keys like:
                - type: "standard" | "extended" | "24hr"
                - weekday_open: "08:00", weekday_close: "17:00"
                - weekend_open: "09:00", weekend_close: "13:00"
                - is_closed_weekends: bool
                - is_24hr: bool
            current_time: datetime to check (defaults to now in SAST)
            medication_schedule: Optional medication scheduling info
        
        Returns:
            Dict with keys:
            - is_open: bool (pharmacy is currently open)
            - dispensing_allowed: bool (medication can be dispensed now)
            - current_time: str (ISO8601)
            - next_open_time: str | None (when pharmacy opens next)
            - hours_type: str (the type of hours in effect)
            - is_weekend: bool
            - is_holiday: bool
        """
        if current_time is None:
            current_time = datetime.now(self.SAST)
        
        # Ensure current_time is in SAST
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=self.SAST)
        else:
            current_time = current_time.astimezone(self.SAST)
        
        is_24hr = pharmacy_hours.get("is_24hr", False)
        
        # 24-hour pharmacy is always open
        if is_24hr:
            return {
                "is_open": True,
                "dispensing_allowed": True,
                "current_time": current_time.isoformat(),
                "next_open_time": None,
                "hours_type": "24hr",
                "is_weekend": False,
                "is_holiday": False
            }
        
        # Determine if weekend
        weekday = current_time.weekday()  # Monday=0, Sunday=6
        is_weekend = weekday >= 5  # Saturday or Sunday
        is_closed_weekends = pharmacy_hours.get("is_closed_weekends", False)
        
        # Get appropriate hours
        if is_weekend:
            if is_closed_weekends:
                return {
                    "is_open": False,
                    "dispensing_allowed": False,
                    "current_time": current_time.isoformat(),
                    "next_open_time": self._get_next_weekday_open(pharmacy_hours, current_time),
                    "hours_type": "closed_weekend",
                    "is_weekend": True,
                    "is_holiday": False
                }
            open_time_str = pharmacy_hours.get("weekend_open", "09:00")
            close_time_str = pharmacy_hours.get("weekend_close", "13:00")
            hours_type = "weekend"
        else:
            open_time_str = pharmacy_hours.get("weekday_open", "08:00")
            close_time_str = pharmacy_hours.get("weekday_close", "17:00")
            hours_type = "weekday"
        
        # Parse times
        open_hour, open_minute = map(int, open_time_str.split(":"))
        close_hour, close_minute = map(int, close_time_str.split(":"))
        
        open_time = current_time.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
        close_time = current_time.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
        
        # Check if currently open
        is_open = open_time <= current_time < close_time
        
        # Calculate next open time
        if is_open:
            next_open_time = None
        else:
            next_open_time = self._get_next_open_time(pharmacy_hours, current_time)
        
        return {
            "is_open": is_open,
            "dispensing_allowed": is_open,
            "current_time": current_time.isoformat(),
            "next_open_time": next_open_time.isoformat() if next_open_time else None,
            "hours_type": hours_type,
            "is_weekend": is_weekend,
            "is_holiday": False  # Would need holiday calendar integration
        }
    
    def _get_next_weekday_open(self, pharmacy_hours: Dict[str, Any], current_time: datetime) -> datetime:
        """Calculate next weekday opening time from current time."""
        # Move to next Monday
        days_until_monday = (7 - current_time.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If it's Monday, go to next Monday
        
        next_weekday = current_time + timedelta(days=days_until_monday)
        open_time_str = pharmacy_hours.get("weekday_open", "08:00")
        open_hour, open_minute = map(int, open_time_str.split(":"))
        
        return next_weekday.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
    
    def _get_next_open_time(self, pharmacy_hours: Dict[str, Any], current_time: datetime) -> Optional[datetime]:
        """Calculate next time pharmacy opens."""
        weekday = current_time.weekday()
        is_weekend = weekday >= 5
        is_closed_weekends = pharmacy_hours.get("is_closed_weekends", False)
        
        if is_weekend and is_closed_weekends:
            return self._get_next_weekday_open(pharmacy_hours, current_time)
        
        # Get appropriate open time
        if is_weekend:
            open_time_str = pharmacy_hours.get("weekend_open", "09:00")
        else:
            open_time_str = pharmacy_hours.get("weekday_open", "08:00")
        
        open_hour, open_minute = map(int, open_time_str.split(":"))
        
        # Check if before opening today
        today_open = current_time.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
        if current_time < today_open:
            return today_open
        
        # After closing, go to next opening
        if is_weekend:
            # After weekend hours, next is Monday
            return self._get_next_weekday_open(pharmacy_hours, current_time)
        else:
            # After weekday hours
            if weekday == 4:  # Friday
                if is_closed_weekends:
                    return self._get_next_weekday_open(pharmacy_hours, current_time)
                else:
                    # Next opening is Saturday
                    next_day = current_time + timedelta(days=1)
                    weekend_open_str = pharmacy_hours.get("weekend_open", "09:00")
                    wk_hour, wk_min = map(int, weekend_open_str.split(":"))
                    return next_day.replace(hour=wk_hour, minute=wk_min, second=0, microsecond=0)
            else:
                # Next opening is tomorrow
                next_day = current_time + timedelta(days=1)
                return next_day.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
    
    def convert_timezone(self, dt: datetime, from_tz: timezone, to_tz: timezone) -> datetime:
        """Convert datetime between timezones.
        
        Args:
            dt: datetime object (may be naive or timezone-aware)
            from_tz: Source timezone
            to_tz: Target timezone
        
        Returns:
            datetime in target timezone
        """
        # If dt is naive, assume from_tz
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=from_tz)
        
        # Convert to target timezone
        return dt.astimezone(to_tz)
    
    def check_holiday(self, date: datetime, region: str = "ZA") -> Dict[str, Any]:
        """Check if a date is a South African public holiday.
        
        Args:
            date: datetime to check
            region: Region code (default "ZA" for South Africa)
        
        Returns:
            Dict with keys:
            - is_holiday: bool
            - holiday_name: str | None
            - region: str
        """
        if region != "ZA":
            return {"is_holiday": False, "holiday_name": None, "region": region}
        
        year = date.year
        month = date.month
        day = date.day
        
        # South African public holidays (hardcoded for 2026)
        # Format: (month, day): "Holiday Name"
        sa_holidays_2026 = {
            (1, 1): "New Year's Day",
            (3, 21): "Human Rights Day",
            (4, 3): "Good Friday",
            (4, 6): "Family Day",
            (4, 27): "Freedom Day",
            (5, 1): "Workers' Day",
            (6, 16): "Youth Day",
            (8, 9): "National Women's Day",
            (9, 24): "Heritage Day",
            (12, 16): "Day of Reconciliation",
            (12, 25): "Christmas Day",
            (12, 26): "Day of Goodwill",
        }
        
        # For other years, use a simple approximation (Easter calculation is complex)
        if year == 2026:
            holiday_name = sa_holidays_2026.get((month, day))
        else:
            # For other years, check fixed-date holidays only
            fixed_holidays = {
                (1, 1): "New Year's Day",
                (3, 21): "Human Rights Day",
                (4, 27): "Freedom Day",
                (5, 1): "Workers' Day",
                (6, 16): "Youth Day",
                (8, 9): "National Women's Day",
                (9, 24): "Heritage Day",
                (12, 16): "Day of Reconciliation",
                (12, 25): "Christmas Day",
                (12, 26): "Day of Goodwill",
            }
            holiday_name = fixed_holidays.get((month, day))
        
        return {
            "is_holiday": holiday_name is not None,
            "holiday_name": holiday_name,
            "region": region
        }
    
    def get_sa_public_holidays(self, year: int) -> Dict[str, Any]:
        """Get list of South African public holidays for a given year.
        
        Args:
            year: Year to get holidays for
        
        Returns:
            Dict with keys:
            - year: int
            - holidays: list of dicts with date and name
            - count: int
        """
        if year == 2026:
            holidays = [
                {"date": "2026-01-01", "name": "New Year's Day"},
                {"date": "2026-03-21", "name": "Human Rights Day"},
                {"date": "2026-04-03", "name": "Good Friday"},
                {"date": "2026-04-06", "name": "Family Day"},
                {"date": "2026-04-27", "name": "Freedom Day"},
                {"date": "2026-05-01", "name": "Workers' Day"},
                {"date": "2026-06-16", "name": "Youth Day"},
                {"date": "2026-08-09", "name": "National Women's Day"},
                {"date": "2026-09-24", "name": "Heritage Day"},
                {"date": "2026-12-16", "name": "Day of Reconciliation"},
                {"date": "2026-12-25", "name": "Christmas Day"},
                {"date": "2026-12-26", "name": "Day of Goodwill"},
            ]
        else:
            # For other years, return fixed-date holidays only
            holidays = [
                {"date": f"{year}-01-01", "name": "New Year's Day"},
                {"date": f"{year}-03-21", "name": "Human Rights Day"},
                {"date": f"{year}-04-27", "name": "Freedom Day"},
                {"date": f"{year}-05-01", "name": "Workers' Day"},
                {"date": f"{year}-06-16", "name": "Youth Day"},
                {"date": f"{year}-08-09", "name": "National Women's Day"},
                {"date": f"{year}-09-24", "name": "Heritage Day"},
                {"date": f"{year}-12-16", "name": "Day of Reconciliation"},
                {"date": f"{year}-12-25", "name": "Christmas Day"},
                {"date": f"{year}-12-26", "name": "Day of Goodwill"},
            ]
        
        return {
            "year": year,
            "holidays": holidays,
            "count": len(holidays)
        }
    
    def validate_controlled_substance_timing(
        self,
        medication_schedule: Dict[str, Any],
        pharmacy_hours: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Validate dispensing timing for controlled substances (Schedules 5, 6, 7).
        
        Schedules:
        - Schedule 5: Restricted dispensing, some timing constraints
        - Schedule 6: Stricter controls, limited dispensing windows
        - Schedule 7: Strictest controls, specific timing requirements
        
        Args:
            medication_schedule: Dict with:
                - schedule: "5" | "6" | "7"
                - requires_supervision: bool
            pharmacy_hours: Pharmacy operating hours
            current_time: datetime to check (defaults to now)
        
        Returns:
            Dict with keys:
            - allowed: bool
            - schedule: str
            - reason: str | None
            - requires_pharmacist_supervision: bool
            - dispensing_window: dict with start/end times
        """
        if current_time is None:
            current_time = datetime.now(self.SAST)
        
        schedule = medication_schedule.get("schedule", "5")
        requires_supervision = medication_schedule.get("requires_supervision", schedule in ["6", "7"])
        
        # Check basic business hours first
        hours_check = self.validate_business_hours(pharmacy_hours, current_time)
        
        if not hours_check["is_open"]:
            return {
                "allowed": False,
                "schedule": schedule,
                "reason": "Pharmacy is closed",
                "requires_pharmacist_supervision": requires_supervision,
                "dispensing_window": None
            }
        
        # Schedule-specific rules
        if schedule == "7":
            # Schedule 7: Only during standard hours with pharmacist supervision
            if hours_check["hours_type"] != "weekday":
                return {
                    "allowed": False,
                    "schedule": schedule,
                    "reason": "Schedule 7 substances only dispensed during weekday hours",
                    "requires_pharmacist_supervision": True,
                    "dispensing_window": {
                        "weekday_start": "08:00",
                        "weekday_end": "17:00"
                    }
                }
        
        elif schedule == "6":
            # Schedule 6: Extended hours allowed but requires supervision
            if hours_check["hours_type"] == "weekend" and pharmacy_hours.get("is_closed_weekends", False):
                return {
                    "allowed": False,
                    "schedule": schedule,
                    "reason": "Schedule 6 substances not available on weekends at this pharmacy",
                    "requires_pharmacist_supervision": True,
                    "dispensing_window": None
                }
        
        # Schedule 5: Standard hours check is sufficient
        
        return {
            "allowed": True,
            "schedule": schedule,
            "reason": None,
            "requires_pharmacist_supervision": requires_supervision,
            "dispensing_window": {
                "start": pharmacy_hours.get("weekday_open", "08:00"),
                "end": pharmacy_hours.get("weekday_close", "17:00")
            }
        }
    
    def check_refill_interval(
        self,
        prescription_fhir: Dict[str, Any],
        last_dispensed_at: Optional[str] = None,
        medication_schedule: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if minimum refill interval has passed for controlled substances.
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
            last_dispensed_at: ISO8601 datetime of last dispensing
            medication_schedule: Optional schedule info for stricter intervals
        
        Returns:
            Dict with keys:
            - can_refill: bool
            - days_since_last: int | None
            - min_interval_days: int
            - days_until_eligible: int (0 if eligible now)
            - next_eligible_at: str | None (ISO8601)
        """
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        expected_supply = dispense_request.get("expectedSupplyDuration", {})
        base_interval = expected_supply.get("value", 28)  # Default 28 days
        
        # Apply schedule-specific minimum intervals
        if medication_schedule:
            schedule = medication_schedule.get("schedule", "5")
            min_interval_multiplier = {
                "5": 0.75,  # 75% of supply duration (21 days for 28-day supply)
                "6": 0.80,  # 80% of supply duration (22-23 days)
                "7": 0.85,  # 85% of supply duration (24 days)
            }.get(schedule, 0.75)
            min_interval_days = int(base_interval * min_interval_multiplier)
        else:
            min_interval_days = base_interval
        
        # If no last dispensed date, it's the first fill (always eligible)
        if not last_dispensed_at:
            return {
                "can_refill": True,
                "days_since_last": None,
                "min_interval_days": min_interval_days,
                "days_until_eligible": 0,
                "next_eligible_at": None
            }
        
        # Parse last dispensed date
        last_dispensed = self._parse_iso8601(last_dispensed_at)
        now = datetime.now(self.SAST)
        
        # Calculate days since last dispense
        days_since_last = (now - last_dispensed).days
        
        # Check if minimum interval has passed
        if days_since_last >= min_interval_days:
            return {
                "can_refill": True,
                "days_since_last": days_since_last,
                "min_interval_days": min_interval_days,
                "days_until_eligible": 0,
                "next_eligible_at": None
            }
        else:
            days_until = min_interval_days - days_since_last
            next_eligible = last_dispensed + timedelta(days=min_interval_days)
            
            return {
                "can_refill": False,
                "days_since_last": days_since_last,
                "min_interval_days": min_interval_days,
                "days_until_eligible": days_until,
                "next_eligible_at": next_eligible.isoformat()
            }
    
    def check_quantity_limits(
        self,
        patient_id: str,
        medication_code: str,
        dispensing_history: List[Dict[str, Any]],
        period_days: int = 30,
        max_quantity: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if patient has exceeded quantity limits for a medication.
        
        Args:
            patient_id: Patient identifier
            medication_code: Medication code (e.g., ATC code)
            dispensing_history: List of prior dispensing records with keys:
                - date_dispensed: ISO8601 datetime
                - quantity: int
            period_days: Lookback period in days
            max_quantity: Maximum allowed quantity in period (None = unlimited)
        
        Returns:
            Dict with keys:
            - within_limits: bool
            - period_days: int
            - max_quantity: int | None
            - total_dispensed: int
            - remaining_allowance: int | None
            - lookback_start: str (ISO8601)
        """
        now = datetime.now(self.SAST)
        lookback_start = now - timedelta(days=period_days)
        
        # Calculate total dispensed in period
        total_dispensed = 0
        for record in dispensing_history:
            dispense_date = self._parse_iso8601(record.get("date_dispensed", ""))
            if dispense_date >= lookback_start:
                total_dispensed += record.get("quantity", 0)
        
        # Check against limits
        if max_quantity is None:
            within_limits = True
            remaining = None
        else:
            within_limits = total_dispensed < max_quantity
            remaining = max(0, max_quantity - total_dispensed)
        
        return {
            "within_limits": within_limits,
            "period_days": period_days,
            "max_quantity": max_quantity,
            "total_dispensed": total_dispensed,
            "remaining_allowance": remaining,
            "lookback_start": lookback_start.isoformat()
        }
    
    def validate_scheduled_prescription(
        self,
        prescription_fhir: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Validate future-dated or scheduled prescriptions.
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
            current_time: datetime to check (defaults to now)
        
        Returns:
            Dict with keys:
            - is_valid: bool (prescription is currently valid)
            - status: str ("active" | "not_yet_valid" | "expired" | "scheduled")
            - valid_from: str (ISO8601)
            - expires_at: str (ISO8601)
            - can_dispense: bool (can be dispensed now)
            - activation_type: str ("immediate" | "scheduled")
        """
        if current_time is None:
            current_time = datetime.now(self.SAST)
        
        # Use existing validity check
        validity = self.check_validity_period(prescription_fhir)
        
        dispense_request = prescription_fhir.get("dispenseRequest", {})
        validity_period = dispense_request.get("validityPeriod", {})
        valid_from_str = validity_period.get("start")
        
        if valid_from_str:
            valid_from = self._parse_iso8601(valid_from_str)
            is_future_dated = valid_from > current_time
        else:
            is_future_dated = False
        
        # Determine activation type
        if is_future_dated:
            activation_type = "scheduled"
            can_dispense = False
        else:
            activation_type = "immediate"
            can_dispense = validity["is_valid"]
        
        return {
            "is_valid": validity["is_valid"],
            "status": validity["status"],
            "valid_from": validity.get("valid_from"),
            "expires_at": validity.get("expires_at"),
            "can_dispense": can_dispense,
            "activation_type": activation_type
        }
    
    def get_next_valid_dispensing_time(
        self,
        prescription_fhir: Dict[str, Any],
        pharmacy_hours: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate when a prescription can next be dispensed.
        
        Considers:
        - Prescription validity period
        - Pharmacy business hours
        - Minimum refill intervals
        
        Args:
            prescription_fhir: FHIR R4 MedicationRequest dict
            pharmacy_hours: Pharmacy operating hours
            current_time: datetime to check (defaults to now)
        
        Returns:
            Dict with keys:
            - can_dispense_now: bool
            - next_dispensing_time: str | None (ISO8601)
            - reasons: list of strings explaining any delays
            - prescription_valid: bool
        """
        if current_time is None:
            current_time = datetime.now(self.SAST)
        
        reasons = []
        
        # Check prescription validity
        validity = self.check_validity_period(prescription_fhir)
        if not validity["is_valid"]:
            return {
                "can_dispense_now": False,
                "next_dispensing_time": None,
                "reasons": [f"Prescription is {validity['status']}"],
                "prescription_valid": False
            }
        
        # Check pharmacy hours
        hours_check = self.validate_business_hours(pharmacy_hours, current_time)
        
        if hours_check["is_open"]:
            return {
                "can_dispense_now": True,
                "next_dispensing_time": current_time.isoformat(),
                "reasons": [],
                "prescription_valid": True
            }
        else:
            reasons.append("Pharmacy is closed")
            next_time_str = hours_check.get("next_open_time")
            
            return {
                "can_dispense_now": False,
                "next_dispensing_time": next_time_str,
                "reasons": reasons,
                "prescription_valid": True
            }
    
    def validate_emergency_override(
        self,
        override_code: str,
        prescription_fhir: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Validate emergency override for after-hours dispensing.
        
        Args:
            override_code: Emergency override authorization code
            prescription_fhir: FHIR R4 MedicationRequest dict
            current_time: datetime of override request (defaults to now)
        
        Returns:
            Dict with keys:
            - valid: bool (override code is valid)
            - dispensing_allowed: bool (can dispense under override)
            - override_type: str ("emergency" | "after_hours" | None)
            - reason: str | None
            - requires_audit: bool
            - audit_reason: str | None
        """
        if current_time is None:
            current_time = datetime.now(self.SAST)
        
        # Validate override code format (simplified for demo)
        # Format: EMRG-XXXX-XXXX where X are alphanumeric
        valid_prefixes = ["EMRG", "AHR", "CTRL"]
        code_parts = override_code.split("-")
        
        if len(code_parts) < 2:
            return {
                "valid": False,
                "dispensing_allowed": False,
                "override_type": None,
                "reason": "Invalid override code format",
                "requires_audit": False,
                "audit_reason": None
            }
        
        prefix = code_parts[0]
        
        if prefix not in valid_prefixes:
            return {
                "valid": False,
                "dispensing_allowed": False,
                "override_type": None,
                "reason": "Invalid override code prefix",
                "requires_audit": False,
                "audit_reason": None
            }
        
        # Check prescription validity
        validity = self.check_validity_period(prescription_fhir)
        if not validity["is_valid"]:
            return {
                "valid": True,  # Code is valid
                "dispensing_allowed": False,
                "override_type": prefix,
                "reason": f"Prescription is {validity['status']}",
                "requires_audit": True,
                "audit_reason": f"Attempted override on {validity['status']} prescription"
            }
        
        # Determine override type
        override_type_map = {
            "EMRG": "emergency",
            "AHR": "after_hours",
            "CTRL": "controlled_substance"
        }
        
        return {
            "valid": True,
            "dispensing_allowed": True,
            "override_type": override_type_map.get(prefix),
            "reason": None,
            "requires_audit": True,
            "audit_reason": f"Emergency override used ({override_type_map.get(prefix)})"
        }
    
    def get_time_validation_dashboard(
        self,
        pharmacy_hours: Optional[Dict[str, Any]] = None,
        prescriptions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate dashboard statistics for time-based validation.
        
        Args:
            pharmacy_hours: Optional pharmacy hours config
            prescriptions: Optional list of prescription FHIR dicts
        
        Returns:
            Dict with keys:
            - timestamp: str (ISO8601)
            - pharmacy_status: dict
            - prescription_summary: dict
            - alerts: list of alert dicts
        """
        now = datetime.now(self.SAST)
        
        # Pharmacy status
        if pharmacy_hours:
            hours_check = self.validate_business_hours(pharmacy_hours, now)
            pharmacy_status = {
                "is_open": hours_check["is_open"],
                "hours_type": hours_check["hours_type"],
                "next_open": hours_check.get("next_open_time")
            }
        else:
            pharmacy_status = {
                "is_open": None,
                "hours_type": None,
                "next_open": None
            }
        
        # Prescription summary
        prescription_summary = {
            "total": 0,
            "active": 0,
            "expired": 0,
            "expiring_24h": 0,
            "expiring_7d": 0
        }
        
        alerts = []
        
        if prescriptions:
            prescription_summary["total"] = len(prescriptions)
            
            for rx in prescriptions:
                validity = self.check_validity_period(rx)
                warnings = self.check_expiration_warnings(rx)
                
                if validity["is_valid"]:
                    prescription_summary["active"] += 1
                elif validity["status"] == "expired":
                    prescription_summary["expired"] += 1
                
                if warnings["should_notify"]:
                    if warnings["warning_level"] == "24_hour":
                        prescription_summary["expiring_24h"] += 1
                        alerts.append({
                            "type": "expiration_critical",
                            "level": "critical",
                            "prescription_id": rx.get("id", "unknown"),
                            "message": f"Prescription expires in {warnings.get('hours_remaining', 0)} hours",
                            "hours_remaining": warnings.get("hours_remaining", 0)
                        })
                    elif warnings["warning_level"] == "7_day":
                        prescription_summary["expiring_7d"] += 1
                        alerts.append({
                            "type": "expiration_warning",
                            "level": "warning",
                            "prescription_id": rx.get("id", "unknown"),
                            "message": f"Prescription expires in {warnings.get('hours_remaining', 0)} hours",
                            "hours_remaining": warnings.get("hours_remaining", 0)
                        })
        
        return {
            "timestamp": now.isoformat(),
            "pharmacy_status": pharmacy_status,
            "prescription_summary": prescription_summary,
            "alerts": alerts
        }
