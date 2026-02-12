"""FHIR R4 service for MedicationRequest operations.

Implements US-017-v2: Full FHIR R4 Implementation
Converts between simplified Prescription model and FHIR R4 format.
Supports dual-mode: simplified (existing) and full FHIR R4.

No external FHIR libraries used - implements FHIR JSON structure manually
to avoid adding dependencies.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.prescription import Prescription
from app.models.user import User


class FHIRService:
    """Service for FHIR R4 MedicationRequest operations.
    
    Converts between simplified Prescription model and FHIR R4 format.
    Supports dual-mode: simplified (existing) and full FHIR R4.
    """
    
    FHIR_VERSION = "4.0.1"
    FHIR_BASE_URL = "http://hl7.org/fhir"
    
    # Status mapping from internal to FHIR
    STATUS_MAP = {
        "ACTIVE": "active",
        "REVOKED": "cancelled",
        "EXPIRED": "stopped",
        "DISPENSED": "completed",
        "DRAFT": "draft",
    }
    
    # Reverse status mapping from FHIR to internal
    STATUS_MAP_REVERSE = {
        "active": "ACTIVE",
        "cancelled": "REVOKED",
        "stopped": "EXPIRED",
        "completed": "DISPENSED",
        "draft": "DRAFT",
        "on-hold": "ACTIVE",  # Treat on-hold as active
        "entered-in-error": "REVOKED",
        "unknown": "ACTIVE",
    }
    
    # SAST timezone (UTC+2)
    SAST = timezone(timedelta(hours=2))
    
    def __init__(self, db_session: Optional[Session] = None, tenant_id: str = "default"):
        """Initialize FHIR service.
        
        Args:
            db_session: SQLAlchemy session for database operations
            tenant_id: Tenant identifier for multi-tenancy scoping
        """
        self.db = db_session
        self.tenant_id = tenant_id
    
    def _get_session(self) -> Session:
        """Get database session, either from initialization or fallback."""
        if self.db is not None:
            return self.db
        from app.db import get_db_session
        return get_db_session()
    
    def _parse_dosage(self, dosage: str) -> Dict[str, Any]:
        """Parse dosage string like '500mg' into value and unit."""
        if not dosage:
            return {"value": None, "unit": None}
        
        # Match patterns like "500mg", "10 mg", "2.5ml", "100 units"
        match = re.match(r"^(\d+(?:\.\d+)?)\s*(\w+)$", dosage.strip())
        if match:
            return {
                "value": float(match.group(1)) if "." in match.group(1) else int(match.group(1)),
                "unit": match.group(2)
            }
        return {"value": None, "unit": dosage}
    
    def _format_timestamp(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime as ISO8601 string with SAST timezone."""
        if dt is None:
            return None
        
        # Ensure datetime has timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.SAST)
        
        return dt.isoformat()
    
    def _now_sast(self) -> datetime:
        """Get current datetime in SAST timezone."""
        return datetime.now(tz=self.SAST)
    
    def prescription_to_fhir(self, prescription: Prescription) -> Dict[str, Any]:
        """Convert a Prescription model instance to FHIR R4 MedicationRequest JSON.
        
        Args:
            prescription: Prescription model instance
            
        Returns:
            FHIR R4 MedicationRequest resource as dict
        """
        now = self._now_sast()
        
        # Build dosage instruction
        dosage_instruction = []
        if prescription.dosage or prescription.instructions:
            dosage_data: Dict[str, Any] = {
                "text": prescription.instructions or f"Take {prescription.dosage}",
            }
            
            # Parse dosage for structured data
            parsed = self._parse_dosage(prescription.dosage)
            if parsed["value"] is not None:
                dosage_data["doseAndRate"] = [{
                    "doseQuantity": {
                        "value": parsed["value"],
                        "unit": parsed["unit"],
                        "system": "http://unitsofmeasure.org",
                        "code": parsed["unit"].lower() if parsed["unit"] else None
                    }
                }]
            
            # Try to extract timing from instructions
            if prescription.instructions:
                timing = self._extract_timing_from_instructions(prescription.instructions)
                if timing:
                    dosage_data["timing"] = timing
            
            dosage_instruction.append(dosage_data)
        
        # Build dispense request
        dispense_request: Dict[str, Any] = {}
        if prescription.quantity:
            dispense_request["quantity"] = {
                "value": prescription.quantity,
                "unit": "tablets"  # Default, could be more specific
            }
        
        # Validity period
        validity_period: Dict[str, Any] = {}
        if prescription.date_issued:
            validity_period["start"] = self._format_timestamp(prescription.date_issued)
        if prescription.date_expires:
            validity_period["end"] = self._format_timestamp(prescription.date_expires)
        
        if validity_period:
            dispense_request["validityPeriod"] = validity_period
        
        # Repeat/refill count
        if prescription.is_repeat:
            dispense_request["numberOfRepeatsAllowed"] = prescription.repeat_count or 0
        else:
            dispense_request["numberOfRepeatsAllowed"] = 0
        
        # Build medication codeable concept
        medication_codeable_concept: Dict[str, Any] = {
            "text": prescription.medication_name or "Unknown medication"
        }
        
        if prescription.medication_code:
            medication_codeable_concept["coding"] = [{
                "system": "http://www.whocc.no/atc",
                "code": prescription.medication_code,
                "display": prescription.medication_name
            }]
        
        # Build the FHIR MedicationRequest resource
        fhir_resource: Dict[str, Any] = {
            "resourceType": "MedicationRequest",
            "id": f"rx-{prescription.id}",
            "meta": {
                "versionId": "1",
                "lastUpdated": self._format_timestamp(prescription.updated_at or now),
                "profile": [f"{self.FHIR_BASE_URL}/StructureDefinition/MedicationRequest"]
            },
            "identifier": [{
                "system": "urn:oid:rxdistribute",
                "value": str(prescription.id)
            }],
            "status": self.STATUS_MAP.get(prescription.status, "unknown"),
            "intent": "order",
            "medicationCodeableConcept": medication_codeable_concept,
            "subject": {
                "reference": f"Patient/{prescription.patient_id}",
                "type": "Patient"
            },
            "requester": {
                "reference": f"Practitioner/{prescription.doctor_id}",
                "type": "Practitioner"
            },
            "authoredOn": self._format_timestamp(prescription.date_issued) or self._format_timestamp(now),
        }
        
        if dosage_instruction:
            fhir_resource["dosageInstruction"] = dosage_instruction
        
        if dispense_request:
            fhir_resource["dispenseRequest"] = dispense_request
        
        # Add note from instructions
        if prescription.instructions:
            fhir_resource["note"] = [{"text": prescription.instructions}]
        
        return fhir_resource
    
    def _extract_timing_from_instructions(self, instructions: str) -> Optional[Dict[str, Any]]:
        """Extract timing information from dosage instructions.
        
        Looks for patterns like:
        - "three times daily" -> frequency: 3, period: 1, periodUnit: d
        - "twice a day" -> frequency: 2, period: 1, periodUnit: d
        - "once daily" -> frequency: 1, period: 1, periodUnit: d
        """
        instructions_lower = instructions.lower()
        
        timing: Dict[str, Any] = {"repeat": {}}
        
        # Check for frequency patterns
        if "three times" in instructions_lower or "3 times" in instructions_lower or "three" in instructions_lower:
            timing["repeat"] = {"frequency": 3, "period": 1, "periodUnit": "d"}
        elif "twice" in instructions_lower or "two times" in instructions_lower or "2 times" in instructions_lower:
            timing["repeat"] = {"frequency": 2, "period": 1, "periodUnit": "d"}
        elif "once" in instructions_lower or "one time" in instructions_lower or "1 time" in instructions_lower or "daily" in instructions_lower:
            timing["repeat"] = {"frequency": 1, "period": 1, "periodUnit": "d"}
        elif "every" in instructions_lower:
            # Handle "every X hours/days"
            match = re.search(r"every\s+(\d+)\s*(hour|hr|day|d)", instructions_lower)
            if match:
                period = int(match.group(1))
                unit = "h" if match.group(2) in ["hour", "hr"] else "d"
                timing["repeat"] = {"frequency": 1, "period": period, "periodUnit": unit}
        
        return timing if timing["repeat"] else None
    
    def fhir_to_prescription_data(self, fhir_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FHIR R4 MedicationRequest JSON to Prescription creation data.
        
        Args:
            fhir_resource: FHIR R4 MedicationRequest resource as dict
            
        Returns:
            Dict suitable for creating a Prescription model
        """
        data: Dict[str, Any] = {}
        
        # Extract medication info
        med_cc = fhir_resource.get("medicationCodeableConcept", {})
        if med_cc:
            data["medication_name"] = med_cc.get("text", "")
            
            # Extract from coding if available
            coding = med_cc.get("coding", [])
            if coding:
                data["medication_code"] = coding[0].get("code", "")
                if not data["medication_name"]:
                    data["medication_name"] = coding[0].get("display", "")
        
        # Extract dosage info
        dosage_instructions = fhir_resource.get("dosageInstruction", [])
        if dosage_instructions:
            dosage_data = dosage_instructions[0]
            
            # Get dosage text
            data["instructions"] = dosage_data.get("text", "")
            
            # Extract structured dosage
            dose_and_rate = dosage_data.get("doseAndRate", [])
            if dose_and_rate:
                dose_qty = dose_and_rate[0].get("doseQuantity", {})
                value = dose_qty.get("value")
                unit = dose_qty.get("unit", "")
                if value is not None:
                    data["dosage"] = f"{value}{unit}"
            
            # If no structured dosage, try to extract from text
            if "dosage" not in data and data.get("instructions"):
                # Look for patterns like "500mg", "10 mg" in instructions
                match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|ml|mcg|g|units?)", data["instructions"], re.IGNORECASE)
                if match:
                    data["dosage"] = f"{match.group(1)}{match.group(2)}"
        
        # Extract quantity from dispenseRequest
        dispense_request = fhir_resource.get("dispenseRequest", {})
        if dispense_request:
            quantity = dispense_request.get("quantity", {})
            if quantity:
                data["quantity"] = quantity.get("value", 0)
            
            # Extract repeat/refill info
            repeats = dispense_request.get("numberOfRepeatsAllowed", 0)
            data["is_repeat"] = repeats > 0
            data["repeat_count"] = repeats
            
            # Extract validity period
            validity = dispense_request.get("validityPeriod", {})
            if validity:
                if validity.get("end"):
                    end_date = validity["end"]
                    if isinstance(end_date, str):
                        data["date_expires"] = end_date
        
        # Extract patient reference
        subject = fhir_resource.get("subject", {})
        if subject:
            ref = subject.get("reference", "")
            if ref.startswith("Patient/"):
                try:
                    data["patient_id"] = int(ref.split("/")[-1])
                except ValueError:
                    pass
        
        # Extract requester (doctor) reference
        requester = fhir_resource.get("requester", {})
        if requester:
            ref = requester.get("reference", "")
            if ref.startswith("Practitioner/"):
                try:
                    data["doctor_id"] = int(ref.split("/")[-1])
                except ValueError:
                    pass
        
        # Extract status
        status = fhir_resource.get("status", "active")
        data["status"] = self.STATUS_MAP_REVERSE.get(status, "ACTIVE")
        
        # Extract authoredOn as date_issued
        authored = fhir_resource.get("authoredOn")
        if authored:
            data["date_issued"] = authored
        
        return data
    
    def validate_medication_request(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a FHIR R4 MedicationRequest resource.
        
        Args:
            resource: FHIR R4 MedicationRequest resource as dict
            
        Returns:
            {"valid": bool, "errors": [...]}
        """
        errors = []
        
        # Check resourceType
        if resource.get("resourceType") != "MedicationRequest":
            errors.append("resourceType must be 'MedicationRequest'")
        
        # Check required fields
        if not resource.get("status"):
            errors.append("status is required")
        elif resource.get("status") not in self.STATUS_MAP_REVERSE and resource.get("status") not in [
            "active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"
        ]:
            errors.append(f"invalid status: {resource.get('status')}")
        
        if not resource.get("intent"):
            errors.append("intent is required")
        
        # Check medication
        if not resource.get("medicationCodeableConcept") and not resource.get("medicationReference"):
            errors.append("medicationCodeableConcept or medicationReference is required")
        
        # Check subject (patient)
        subject = resource.get("subject", {})
        if not subject.get("reference"):
            errors.append("subject.reference is required")
        elif not subject.get("reference", "").startswith("Patient/"):
            errors.append("subject.reference must reference a Patient")
        
        # Check requester (doctor)
        requester = resource.get("requester", {})
        if not requester.get("reference"):
            errors.append("requester.reference is required")
        elif not requester.get("reference", "").startswith("Practitioner/"):
            errors.append("requester.reference must reference a Practitioner")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def create_from_fhir(self, fhir_resource: Dict[str, Any], requester_id: int) -> Dict[str, Any]:
        """Create a Prescription from FHIR MedicationRequest input.
        
        Args:
            fhir_resource: FHIR R4 MedicationRequest resource
            requester_id: ID of the requesting user (doctor)
            
        Returns:
            FHIR resource of created prescription
        """
        session = self._get_session()
        
        # Validate first
        validation = self.validate_medication_request(fhir_resource)
        if not validation["valid"]:
            return {
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "invalid",
                    "diagnostics": "; ".join(validation["errors"])
                }]
            }
        
        # Convert to prescription data
        data = self.fhir_to_prescription_data(fhir_resource)
        
        # Override doctor_id with authenticated user
        data["doctor_id"] = requester_id
        
        # Set defaults if missing
        if "date_issued" not in data:
            data["date_issued"] = datetime.utcnow()
        elif isinstance(data["date_issued"], str):
            try:
                data["date_issued"] = datetime.fromisoformat(data["date_issued"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                data["date_issued"] = datetime.utcnow()
        
        if "date_expires" not in data:
            # Default to 3 months from issue
            if isinstance(data["date_issued"], datetime):
                data["date_expires"] = data["date_issued"] + timedelta(days=90)
            else:
                data["date_expires"] = datetime.utcnow() + timedelta(days=90)
        elif isinstance(data["date_expires"], str):
            try:
                data["date_expires"] = datetime.fromisoformat(data["date_expires"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                data["date_expires"] = datetime.utcnow() + timedelta(days=90)
        
        # Create prescription
        prescription = Prescription(
            patient_id=data.get("patient_id"),
            doctor_id=data["doctor_id"],
            medication_name=data.get("medication_name", ""),
            medication_code=data.get("medication_code"),
            dosage=data.get("dosage", ""),
            quantity=data.get("quantity", 0),
            instructions=data.get("instructions", ""),
            date_issued=data["date_issued"] if isinstance(data["date_issued"], datetime) else datetime.utcnow(),
            date_expires=data["date_expires"] if isinstance(data["date_expires"], datetime) else datetime.utcnow() + timedelta(days=90),
            is_repeat=data.get("is_repeat", False),
            repeat_count=data.get("repeat_count", 0),
            status=data.get("status", "ACTIVE"),
        )
        
        prescription.tenant_id = self.tenant_id
        
        session.add(prescription)
        session.commit()
        session.refresh(prescription)
        
        return self.prescription_to_fhir(prescription)
    
    def get_as_fhir(self, prescription_id: int) -> Optional[Dict[str, Any]]:
        """Get a Prescription as FHIR MedicationRequest.
        
        Args:
            prescription_id: ID of the prescription
            
        Returns:
            FHIR R4 MedicationRequest resource or None if not found
        """
        session = self._get_session()
        
        prescription = (
            session.query(Prescription)
            .filter(Prescription.id == prescription_id)
            .filter(Prescription.tenant_id == self.tenant_id)
            .first()
        )
        
        if not prescription:
            return None
        
        return self.prescription_to_fhir(prescription)
    
    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """FHIR search - returns a Bundle of matching MedicationRequests.
        
        Supports:
        - patient: Patient ID
        - requester: Practitioner ID
        - status: FHIR status (active, cancelled, etc.)
        - authored-on: Date range (gt, lt, ge, le prefixes)
        - _count: Number of results per page
        - _offset: Pagination offset
        
        Args:
            params: Search parameters dict
            
        Returns:
            FHIR Bundle containing matching MedicationRequests
        """
        session = self._get_session()
        
        query = session.query(Prescription).filter(Prescription.tenant_id == self.tenant_id)
        
        # Filter by patient
        if "patient" in params:
            try:
                patient_id = int(params["patient"])
                query = query.filter(Prescription.patient_id == patient_id)
            except ValueError:
                pass
        
        # Filter by requester (doctor)
        if "requester" in params:
            try:
                requester_id = int(params["requester"])
                query = query.filter(Prescription.doctor_id == requester_id)
            except ValueError:
                pass
        
        # Filter by status
        if "status" in params:
            fhir_status = params["status"]
            internal_status = self.STATUS_MAP_REVERSE.get(fhir_status)
            if internal_status:
                query = query.filter(Prescription.status == internal_status)
        
        # Filter by authored-on (date)
        if "authored-on" in params:
            date_param = params["authored-on"]
            query = self._apply_date_filter(query, date_param)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        count = int(params.get("_count", 10))
        offset = int(params.get("_offset", 0))
        
        prescriptions = query.offset(offset).limit(count).all()
        
        # Convert to FHIR entries
        entries = []
        for rx in prescriptions:
            fhir_resource = self.prescription_to_fhir(rx)
            entries.append({
                "fullUrl": f"MedicationRequest/{fhir_resource['id']}",
                "resource": fhir_resource,
                "search": {
                    "mode": "match"
                }
            })
        
        return self.create_bundle(entries, bundle_type="searchset", total=total)
    
    def _apply_date_filter(self, query, date_param: str):
        """Apply date filter with FHIR prefix operators.
        
        Prefixes:
        - gt: greater than
        - lt: less than
        - ge: greater than or equal
        - le: less than or equal
        - eq: equal (default)
        """
        if date_param.startswith("gt"):
            date_str = date_param[2:]
            try:
                date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                query = query.filter(Prescription.date_issued > date_val)
            except (ValueError, AttributeError):
                pass
        elif date_param.startswith("lt"):
            date_str = date_param[2:]
            try:
                date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                query = query.filter(Prescription.date_issued < date_val)
            except (ValueError, AttributeError):
                pass
        elif date_param.startswith("ge"):
            date_str = date_param[2:]
            try:
                date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                query = query.filter(Prescription.date_issued >= date_val)
            except (ValueError, AttributeError):
                pass
        elif date_param.startswith("le"):
            date_str = date_param[2:]
            try:
                date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                query = query.filter(Prescription.date_issued <= date_val)
            except (ValueError, AttributeError):
                pass
        else:
            # Default: equal (eq)
            date_str = date_param.replace("eq", "", 1) if date_param.startswith("eq") else date_param
            try:
                date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                # For equality, use date range for the day
                next_day = date_val + timedelta(days=1)
                query = query.filter(Prescription.date_issued >= date_val)
                query = query.filter(Prescription.date_issued < next_day)
            except (ValueError, AttributeError):
                pass
        
        return query
    
    def create_bundle(
        self, 
        entries: List[Dict[str, Any]], 
        bundle_type: str = "searchset",
        total: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a FHIR Bundle resource.
        
        Args:
            entries: List of bundle entries
            bundle_type: Type of bundle (searchset, transaction, batch, etc.)
            total: Total number of results (for searchset)
            
        Returns:
            FHIR Bundle resource as dict
        """
        bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "meta": {
                "lastUpdated": self._format_timestamp(self._now_sast())
            },
            "type": bundle_type,
            "entry": entries
        }
        
        if total is not None:
            bundle["total"] = total
        
        return bundle
    
    def process_bundle(self, bundle: Dict[str, Any], requester_id: int) -> Dict[str, Any]:
        """Process a FHIR transaction/batch Bundle.
        
        Args:
            bundle: FHIR Bundle resource containing MedicationRequests
            requester_id: ID of the requesting user (doctor)
            
        Returns:
            FHIR Bundle containing operation results
        """
        bundle_type = bundle.get("type", "")
        
        if bundle_type not in ["transaction", "batch"]:
            return {
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "invalid",
                    "diagnostics": "Bundle type must be 'transaction' or 'batch'"
                }]
            }
        
        entries = bundle.get("entry", [])
        response_entries = []
        
        for entry in entries:
            resource = entry.get("resource", {})
            request = entry.get("request", {})
            method = request.get("method", "POST")
            
            if method == "POST" and resource.get("resourceType") == "MedicationRequest":
                result = self.create_from_fhir(resource, requester_id)
                
                if result.get("resourceType") == "OperationOutcome":
                    # Error occurred
                    response_entries.append({
                        "response": {
                            "status": "400",
                            "outcome": result
                        }
                    })
                else:
                    # Success
                    response_entries.append({
                        "response": {
                            "status": "201",
                            "location": f"MedicationRequest/{result['id']}",
                            "etag": result.get("meta", {}).get("versionId", "1")
                        },
                        "resource": result
                    })
            else:
                # Unsupported operation
                response_entries.append({
                    "response": {
                        "status": "400",
                        "outcome": {
                            "resourceType": "OperationOutcome",
                            "issue": [{
                                "severity": "error",
                                "code": "not-supported",
                                "diagnostics": f"Unsupported method or resource type: {method} {resource.get('resourceType')}"
                            }]
                        }
                    }
                })
        
        return self.create_bundle(response_entries, bundle_type="batch-response")
    
    def get_capability_statement(self) -> Dict[str, Any]:
        """Return FHIR CapabilityStatement (metadata endpoint).
        
        Returns:
            FHIR CapabilityStatement resource
        """
        now = self._now_sast()
        
        return {
            "resourceType": "CapabilityStatement",
            "id": "rxdistribute-fhir-server",
            "meta": {
                "versionId": "1",
                "lastUpdated": self._format_timestamp(now)
            },
            "status": "active",
            "experimental": False,
            "date": self._format_timestamp(now),
            "publisher": "RxDistribute Digital Prescription System",
            "kind": "instance",
            "software": {
                "name": "RxDistribute FHIR Server",
                "version": "0.1.0"
            },
            "implementation": {
                "description": "RxDistribute FHIR R4 Server for Digital Prescriptions",
                "url": "http://localhost:8000/fhir"
            },
            "fhirVersion": "4.0.1",
            "format": ["json", "xml"],
            "rest": [{
                "mode": "server",
                "security": {
                    "cors": True,
                    "service": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                            "code": "OAuth",
                            "display": "OAuth2 Token"
                        }]
                    }]
                },
                "resource": [{
                    "type": "MedicationRequest",
                    "supportedProfile": [f"{self.FHIR_BASE_URL}/StructureDefinition/MedicationRequest"],
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {
                            "name": "patient",
                            "type": "reference",
                            "documentation": "Search by patient ID"
                        },
                        {
                            "name": "requester",
                            "type": "reference",
                            "documentation": "Search by requesting practitioner ID"
                        },
                        {
                            "name": "status",
                            "type": "token",
                            "documentation": "Search by prescription status"
                        },
                        {
                            "name": "authored-on",
                            "type": "date",
                            "documentation": "Search by authored date"
                        }
                    ]
                }, {
                    "type": "Bundle",
                    "interaction": [
                        {"code": "create"}
                    ]
                }]
            }]
        }
    
    def export_prescriptions(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export prescriptions as a FHIR Bundle for interoperability.
        
        Args:
            filters: Optional filters (patient, status, start_date, end_date)
            
        Returns:
            FHIR Bundle containing all matching prescriptions
        """
        session = self._get_session()
        
        query = session.query(Prescription).filter(Prescription.tenant_id == self.tenant_id)
        
        if filters:
            if filters.get("patient"):
                try:
                    patient_id = int(filters["patient"])
                    query = query.filter(Prescription.patient_id == patient_id)
                except ValueError:
                    pass
            
            if filters.get("status"):
                internal_status = self.STATUS_MAP_REVERSE.get(filters["status"], filters["status"])
                query = query.filter(Prescription.status == internal_status)
            
            if filters.get("start_date"):
                try:
                    start = datetime.fromisoformat(filters["start_date"].replace("Z", "+00:00"))
                    query = query.filter(Prescription.date_issued >= start)
                except (ValueError, AttributeError):
                    pass
            
            if filters.get("end_date"):
                try:
                    end = datetime.fromisoformat(filters["end_date"].replace("Z", "+00:00"))
                    query = query.filter(Prescription.date_issued <= end)
                except (ValueError, AttributeError):
                    pass
        
        prescriptions = query.all()
        
        entries = []
        for rx in prescriptions:
            fhir_resource = self.prescription_to_fhir(rx)
            entries.append({
                "fullUrl": f"MedicationRequest/{fhir_resource['id']}",
                "resource": fhir_resource
            })
        
        return self.create_bundle(entries, bundle_type="collection", total=len(entries))
