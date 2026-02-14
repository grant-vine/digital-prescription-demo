from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, require_role, get_db
from app.models.user import User
from app.services.fhir import FHIRService


router = APIRouter()

FHIR_JSON_MEDIA_TYPE = "application/fhir+json"


def get_fhir_service(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FHIRService:
    tenant_id = getattr(current_user, "_jwt_tenant_id", "default")
    return FHIRService(db_session=db, tenant_id=tenant_id)


def fhir_json_response(data: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=data, media_type=FHIR_JSON_MEDIA_TYPE, status_code=status_code)


def operation_outcome(severity: str, code: str, diagnostics: str) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": severity,
            "code": code,
            "diagnostics": diagnostics
        }]
    }


@router.post("/fhir/MedicationRequest")
async def create_medication_request(
    fhir_resource: dict,
    current_user: User = Depends(require_role(["doctor"])),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    result = fhir_service.create_from_fhir(fhir_resource, current_user.id)
    
    if result.get("resourceType") == "OperationOutcome":
        return fhir_json_response(result, status_code=status.HTTP_400_BAD_REQUEST)
    
    return fhir_json_response(result, status_code=status.HTTP_201_CREATED)


@router.get("/fhir/MedicationRequest/{id}")
async def get_medication_request(
    id: str,
    current_user: User = Depends(get_current_user),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    prescription_id = id
    if id.startswith("rx-"):
        prescription_id = id[3:]
    
    try:
        prescription_id = int(prescription_id)
    except ValueError:
        return fhir_json_response(
            operation_outcome("error", "not-found", f"Invalid prescription ID: {id}"),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    result = fhir_service.get_as_fhir(prescription_id)
    
    if result is None:
        return fhir_json_response(
            operation_outcome("error", "not-found", f"MedicationRequest with id '{id}' not found"),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return fhir_json_response(result)


@router.get("/fhir/MedicationRequest")
async def search_medication_requests(
    patient: Optional[str] = Query(None, description="Patient ID"),
    requester: Optional[str] = Query(None, description="Requesting practitioner ID"),
    status: Optional[str] = Query(None, description="Prescription status"),
    authored_on: Optional[str] = Query(None, alias="authored-on", description="Authored date"),
    count: int = Query(10, alias="_count", ge=1, le=100),
    offset: int = Query(0, alias="_offset", ge=0),
    current_user: User = Depends(get_current_user),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    params = {
        "_count": count,
        "_offset": offset,
    }
    
    if patient:
        params["patient"] = patient
    if requester:
        params["requester"] = requester
    if status:
        params["status"] = status
    if authored_on:
        params["authored-on"] = authored_on
    
    result = fhir_service.search(params)
    return fhir_json_response(result)


@router.post("/fhir/Bundle")
async def process_bundle(
    bundle: dict,
    current_user: User = Depends(require_role(["doctor"])),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    if bundle.get("resourceType") != "Bundle":
        return fhir_json_response(
            operation_outcome("error", "invalid", "Resource must be a Bundle"),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    result = fhir_service.process_bundle(bundle, current_user.id)
    return fhir_json_response(result)


@router.get("/fhir/metadata")
async def get_capability_statement(
    db: Session = Depends(get_db),
):
    fhir_service = FHIRService(db_session=db, tenant_id="default")
    result = fhir_service.get_capability_statement()
    return fhir_json_response(result)


@router.get("/fhir/MedicationRequest/{id}/$export")
async def export_medication_request(
    id: str,
    current_user: User = Depends(get_current_user),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    prescription_id = id
    if id.startswith("rx-"):
        prescription_id = id[3:]
    
    try:
        prescription_id = int(prescription_id)
    except ValueError:
        return fhir_json_response(
            operation_outcome("error", "not-found", f"Invalid prescription ID: {id}"),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    result = fhir_service.get_as_fhir(prescription_id)
    
    if result is None:
        return fhir_json_response(
            operation_outcome("error", "not-found", f"MedicationRequest with id '{id}' not found"),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    bundle = fhir_service.create_bundle([{"resource": result}], bundle_type="collection")
    return fhir_json_response(bundle)


@router.post("/fhir/MedicationRequest/$export")
async def export_medication_requests(
    filters: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    fhir_service: FHIRService = Depends(get_fhir_service),
):
    filter_dict = filters or {}
    result = fhir_service.export_prescriptions(filter_dict)
    return fhir_json_response(result)
