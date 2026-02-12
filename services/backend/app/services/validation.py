"""Time-based prescription validation service.

Implements US-012, US-013, US-014 for:
- Validity period checks (valid_from → valid_until)
- Expiration warnings (7-day, 24-hour thresholds)
- Repeat/refill eligibility calculations

All dates are handled in SAST (UTC+2) timezone.
FHIR R4 MedicationRequest structures with ISO8601 dates.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional


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
