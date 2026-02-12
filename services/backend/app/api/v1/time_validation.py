"""Time validation API endpoints for advanced prescription timing.

Implements US-022:
- GET /api/v1/prescriptions/{id}/time-validity - Full time validation for a prescription
- GET /api/v1/pharmacy/{id}/hours - Get pharmacy hours (stub/config-based)
- GET /api/v1/holidays - List SA public holidays for year
- GET /api/v1/controlled-substances/patient/{id}/limits - Patient substance limits
- POST /api/v1/emergency-override - Emergency override validation
- GET /api/v1/admin/time-validation/dashboard - Time validation dashboard

All endpoints require authentication. Admin/dashboard endpoints require doctor/admin role.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.services.validation import TimeValidationService

router = APIRouter()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class PharmacyHours(BaseModel):
    """Pharmacy operating hours configuration."""
    type: str = Field(default="standard", description="Hours type: standard, extended, 24hr")
    weekday_open: str = Field(default="08:00", description="Weekday opening time (HH:MM)")
    weekday_close: str = Field(default="17:00", description="Weekday closing time (HH:MM)")
    weekend_open: str = Field(default="09:00", description="Weekend opening time (HH:MM)")
    weekend_close: str = Field(default="13:00", description="Weekend closing time (HH:MM)")
    is_closed_weekends: bool = Field(default=False, description="Closed on weekends")
    is_24hr: bool = Field(default=False, description="24-hour pharmacy")


class TimeValidityResponse(BaseModel):
    """Response for prescription time validity check."""
    prescription_id: str
    is_valid: bool
    status: str
    valid_from: Optional[str]
    expires_at: Optional[str]
    expired: bool
    days_remaining: int
    utc_offset: int
    can_dispense: bool
    next_dispensing_time: Optional[str]
    timezone: str = "SAST"


class PharmacyHoursResponse(BaseModel):
    """Response for pharmacy hours."""
    pharmacy_id: str
    is_open: bool
    hours_type: str
    current_time: str
    next_open_time: Optional[str]
    is_weekend: bool
    is_holiday: bool


class HolidaysResponse(BaseModel):
    """Response for public holidays list."""
    year: int
    holidays: List[Dict[str, str]]
    count: int


class PatientLimitsResponse(BaseModel):
    """Response for patient controlled substance limits."""
    patient_id: str
    within_limits: bool
    period_days: int
    max_quantity: Optional[int]
    total_dispensed: int
    remaining_allowance: Optional[int]
    lookback_start: str


class EmergencyOverrideRequest(BaseModel):
    """Request for emergency override validation."""
    override_code: str = Field(..., description="Emergency override code (e.g., EMRG-XXXX-XXXX)")
    prescription_id: str = Field(..., description="Prescription ID")
    reason: Optional[str] = Field(None, description="Reason for emergency override")


class EmergencyOverrideResponse(BaseModel):
    """Response for emergency override validation."""
    valid: bool
    dispensing_allowed: bool
    override_type: Optional[str]
    reason: Optional[str]
    requires_audit: bool
    audit_reason: Optional[str]


class TimeValidationDashboardResponse(BaseModel):
    """Response for time validation dashboard."""
    timestamp: str
    pharmacy_status: Dict[str, Any]
    prescription_summary: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class TimezoneConversionRequest(BaseModel):
    """Request for timezone conversion."""
    datetime_str: str = Field(..., description="ISO8601 datetime string")
    from_timezone: str = Field(default="UTC", description="Source timezone offset (e.g., UTC, SAST)")
    to_timezone: str = Field(default="SAST", description="Target timezone offset (e.g., UTC, SAST)")


class TimezoneConversionResponse(BaseModel):
    """Response for timezone conversion."""
    original_datetime: str
    converted_datetime: str
    from_timezone: str
    to_timezone: str
    utc_offset_hours: int


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get(
    "/prescriptions/{prescription_id}/time-validity",
    response_model=TimeValidityResponse,
    tags=["time-validation"]
)
async def get_prescription_time_validity(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get full time validation for a prescription.
    
    Returns comprehensive timing information including:
    - Validity period status (active, expired, not_yet_valid)
    - Days remaining until expiration
    - Whether prescription can be dispensed now
    - Next available dispensing time
    
    Args:
        prescription_id: Prescription ID to validate
        current_user: Authenticated user
    
    Returns:
        TimeValidityResponse with full validation details
    
    Raises:
        HTTPException 401: Not authenticated
    """
    # For this implementation, we construct a sample FHIR prescription
    # In production, this would fetch from database
    now = datetime.now(timezone(timedelta(hours=2)))
    
    # Sample prescription structure for demonstration
    prescription_fhir = {
        "resourceType": "MedicationRequest",
        "id": prescription_id,
        "dispenseRequest": {
            "validityPeriod": {
                "start": now.isoformat(),
                "end": (now + timedelta(days=30)).isoformat()
            }
        }
    }
    
    service = TimeValidationService()
    
    validity = service.check_validity_period(prescription_fhir)
    next_dispensing = service.get_next_valid_dispensing_time(
        prescription_fhir,
        pharmacy_hours={"is_24hr": True},  # Assume 24hr for basic check
        current_time=now
    )
    
    return TimeValidityResponse(
        prescription_id=prescription_id,
        is_valid=validity["is_valid"],
        status=validity["status"],
        valid_from=validity.get("valid_from"),
        expires_at=validity.get("expires_at"),
        expired=validity.get("expired", False),
        days_remaining=validity.get("days_remaining", 0),
        utc_offset=2,
        can_dispense=next_dispensing["can_dispense_now"],
        next_dispensing_time=next_dispensing.get("next_dispensing_time"),
        timezone="SAST"
    )


@router.get(
    "/pharmacy/{pharmacy_id}/hours",
    response_model=PharmacyHoursResponse,
    tags=["time-validation"]
)
async def get_pharmacy_hours(
    pharmacy_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get pharmacy hours and current open status.
    
    Returns pharmacy operating hours information including:
    - Current open/closed status
    - Hours type (weekday, weekend, 24hr)
    - Next opening time if closed
    - Weekend and holiday indicators
    
    Args:
        pharmacy_id: Pharmacy identifier
        current_user: Authenticated user
    
    Returns:
        PharmacyHoursResponse with hours information
    
    Raises:
        HTTPException 401: Not authenticated
    """
    # Default pharmacy hours (would be fetched from database in production)
    pharmacy_hours = {
        "type": "standard",
        "weekday_open": "08:00",
        "weekday_close": "17:00",
        "weekend_open": "09:00",
        "weekend_close": "13:00",
        "is_closed_weekends": False,
        "is_24hr": False
    }
    
    service = TimeValidationService()
    hours_check = service.validate_business_hours(pharmacy_hours)
    
    return PharmacyHoursResponse(
        pharmacy_id=pharmacy_id,
        is_open=hours_check["is_open"],
        hours_type=hours_check["hours_type"],
        current_time=hours_check["current_time"],
        next_open_time=hours_check.get("next_open_time"),
        is_weekend=hours_check["is_weekend"],
        is_holiday=hours_check["is_holiday"]
    )


@router.get(
    "/holidays",
    response_model=HolidaysResponse,
    tags=["time-validation"]
)
async def get_public_holidays(
    year: int = Query(default=2026, description="Year to get holidays for"),
    current_user: User = Depends(get_current_user),
):
    """Get South African public holidays for a given year.
    
    Returns list of all public holidays in South Africa for the specified year.
    Currently supports 2026 with full Easter dates. Other years return fixed-date
    holidays only.
    
    Args:
        year: Year to get holidays for (default: 2026)
        current_user: Authenticated user
    
    Returns:
        HolidaysResponse with list of holidays
    
    Raises:
        HTTPException 401: Not authenticated
    """
    service = TimeValidationService()
    holidays_data = service.get_sa_public_holidays(year)
    
    return HolidaysResponse(
        year=holidays_data["year"],
        holidays=holidays_data["holidays"],
        count=holidays_data["count"]
    )


@router.get(
    "/controlled-substances/patient/{patient_id}/limits",
    response_model=PatientLimitsResponse,
    tags=["time-validation"]
)
async def get_patient_substance_limits(
    patient_id: str,
    medication_code: str = Query(..., description="Medication ATC code"),
    period_days: int = Query(default=30, description="Lookback period in days"),
    max_quantity: Optional[int] = Query(default=None, description="Maximum allowed quantity"),
    current_user: User = Depends(get_current_user),
):
    """Get patient controlled substance dispensing limits.
    
    Calculates total quantity dispensed to patient for a specific medication
    within the lookback period and checks against limits.
    
    Args:
        patient_id: Patient identifier
        medication_code: Medication ATC code
        period_days: Lookback period in days (default: 30)
        max_quantity: Maximum allowed quantity (optional)
        current_user: Authenticated user
    
    Returns:
        PatientLimitsResponse with limit information
    
    Raises:
        HTTPException 401: Not authenticated
    """
    # In production, this would fetch dispensing history from database
    # For demo, we return sample data
    dispensing_history = [
        # Sample: would be fetched from database
    ]
    
    service = TimeValidationService()
    limits = service.check_quantity_limits(
        patient_id=patient_id,
        medication_code=medication_code,
        dispensing_history=dispensing_history,
        period_days=period_days,
        max_quantity=max_quantity
    )
    
    return PatientLimitsResponse(
        patient_id=patient_id,
        within_limits=limits["within_limits"],
        period_days=limits["period_days"],
        max_quantity=limits["max_quantity"],
        total_dispensed=limits["total_dispensed"],
        remaining_allowance=limits["remaining_allowance"],
        lookback_start=limits["lookback_start"]
    )


@router.post(
    "/emergency-override",
    response_model=EmergencyOverrideResponse,
    status_code=status.HTTP_200_OK,
    tags=["time-validation"]
)
async def validate_emergency_override(
    request: EmergencyOverrideRequest,
    current_user: User = Depends(require_role(["doctor", "pharmacist", "admin"])),
):
    """Validate emergency override for after-hours dispensing.
    
    Validates an emergency override code and determines if dispensing
    is allowed under emergency conditions. Requires doctor, pharmacist,
    or admin role.
    
    Override code formats:
    - EMRG-XXXX-XXXX: General emergency
    - AHR-XXXX-XXXX: After-hours override
    - CTRL-XXXX-XXXX: Controlled substance override
    
    Args:
        request: Emergency override request with code and prescription ID
        current_user: Authenticated user with required role
    
    Returns:
        EmergencyOverrideResponse with validation result
    
    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: User lacks required role
    """
    # Sample prescription for validation
    now = datetime.now(timezone(timedelta(hours=2)))
    prescription_fhir = {
        "resourceType": "MedicationRequest",
        "id": request.prescription_id,
        "dispenseRequest": {
            "validityPeriod": {
                "start": now.isoformat(),
                "end": (now + timedelta(days=30)).isoformat()
            }
        }
    }
    
    service = TimeValidationService()
    override_result = service.validate_emergency_override(
        override_code=request.override_code,
        prescription_fhir=prescription_fhir
    )
    
    return EmergencyOverrideResponse(
        valid=override_result["valid"],
        dispensing_allowed=override_result["dispensing_allowed"],
        override_type=override_result.get("override_type"),
        reason=override_result.get("reason"),
        requires_audit=override_result["requires_audit"],
        audit_reason=override_result.get("audit_reason")
    )


@router.get(
    "/admin/time-validation/dashboard",
    response_model=TimeValidationDashboardResponse,
    tags=["time-validation", "admin"]
)
async def get_time_validation_dashboard(
    pharmacy_hours: Optional[str] = Query(default=None, description="Pharmacy hours config JSON"),
    current_user: User = Depends(require_role(["doctor", "admin"])),
):
    """Get time validation dashboard statistics.
    
    Returns comprehensive dashboard with:
    - Pharmacy open/closed status
    - Prescription summary (active, expired, expiring soon)
    - Time-based alerts (24h warnings, 7d warnings)
    
    Requires doctor or admin role.
    
    Args:
        pharmacy_hours: Optional JSON string with pharmacy hours config
        current_user: Authenticated user with doctor or admin role
    
    Returns:
        TimeValidationDashboardResponse with dashboard data
    
    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: User lacks required role
    """
    import json
    
    # Parse pharmacy hours if provided
    hours_config = None
    if pharmacy_hours:
        try:
            hours_config = json.loads(pharmacy_hours)
        except json.JSONDecodeError:
            hours_config = None
    
    if not hours_config:
        hours_config = {
            "type": "standard",
            "weekday_open": "08:00",
            "weekday_close": "17:00",
            "is_24hr": False
        }
    
    # Sample prescriptions for dashboard (would be from DB in production)
    now = datetime.now(timezone(timedelta(hours=2)))
    prescriptions = [
        {
            "resourceType": "MedicationRequest",
            "id": "rx-001",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": now.isoformat(),
                    "end": (now + timedelta(days=30)).isoformat()
                }
            }
        },
        {
            "resourceType": "MedicationRequest",
            "id": "rx-002",
            "dispenseRequest": {
                "validityPeriod": {
                    "start": now.isoformat(),
                    "end": (now + timedelta(hours=12)).isoformat()  # Expires in 12 hours
                }
            }
        }
    ]
    
    service = TimeValidationService()
    dashboard = service.get_time_validation_dashboard(
        pharmacy_hours=hours_config,
        prescriptions=prescriptions
    )
    
    return TimeValidationDashboardResponse(
        timestamp=dashboard["timestamp"],
        pharmacy_status=dashboard["pharmacy_status"],
        prescription_summary=dashboard["prescription_summary"],
        alerts=dashboard["alerts"]
    )


@router.post(
    "/timezone/convert",
    response_model=TimezoneConversionResponse,
    tags=["time-validation"]
)
async def convert_timezone(
    request: TimezoneConversionRequest,
    current_user: User = Depends(get_current_user),
):
    """Convert datetime between timezones.
    
    Converts a datetime from one timezone to another. Supports SAST
    (South African Standard Time, UTC+2) and UTC.
    
    Args:
        request: Timezone conversion request with datetime and zones
        current_user: Authenticated user
    
    Returns:
        TimezoneConversionResponse with converted datetime
    
    Raises:
        HTTPException 401: Not authenticated
        HTTPException 422: Invalid datetime format
    """
    service = TimeValidationService()
    
    # Parse source datetime
    try:
        dt = datetime.fromisoformat(request.datetime_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid datetime format. Use ISO8601 format."
        )
    
    # Determine timezones
    SAST = timezone(timedelta(hours=2))
    UTC = timezone.utc
    
    from_tz = SAST if request.from_timezone.upper() == "SAST" else UTC
    to_tz = SAST if request.to_timezone.upper() == "SAST" else UTC
    
    # Perform conversion
    converted = service.convert_timezone(dt, from_tz, to_tz)
    
    return TimezoneConversionResponse(
        original_datetime=request.datetime_str,
        converted_datetime=converted.isoformat(),
        from_timezone=request.from_timezone,
        to_timezone=request.to_timezone,
        utc_offset_hours=2 if request.to_timezone.upper() == "SAST" else 0
    )


@router.get(
    "/holidays/check",
    response_model=Dict[str, Any],
    tags=["time-validation"]
)
async def check_holiday(
    date: str = Query(..., description="Date to check (ISO8601 format)"),
    region: str = Query(default="ZA", description="Region code (default: ZA)"),
    current_user: User = Depends(get_current_user),
):
    """Check if a specific date is a public holiday.
    
    Args:
        date: Date to check in ISO8601 format
        region: Region code (default: ZA for South Africa)
        current_user: Authenticated user
    
    Returns:
        Dict with is_holiday, holiday_name, and region
    
    Raises:
        HTTPException 401: Not authenticated
        HTTPException 422: Invalid date format
    """
    service = TimeValidationService()
    
    try:
        dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid date format. Use ISO8601 format."
        )
    
    result = service.check_holiday(dt, region)
    return result
