import pytest
from datetime import datetime, timedelta, timezone
from app.services.fhir import FHIRService
from app.models.prescription import Prescription

SAST = timezone(timedelta(hours=2))


class TestFHIRConversion:
    def test_prescription_to_fhir_basic(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            id=123,
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Amoxicillin",
            medication_code="J01CA04",
            dosage="500mg",
            quantity=21,
            instructions="Take one tablet three times daily with food",
            date_issued=datetime(2026, 2, 11, 10, 30, 0),
            date_expires=datetime(2026, 5, 11, 23, 59, 59),
            is_repeat=False,
            repeat_count=0,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        assert fhir["resourceType"] == "MedicationRequest"
        assert fhir["id"] == "rx-123"
        assert fhir["status"] == "active"
        assert fhir["intent"] == "order"
        assert fhir["medicationCodeableConcept"]["text"] == "Amoxicillin"
        assert fhir["subject"]["reference"] == f"Patient/{patient_user.id}"
        assert fhir["requester"]["reference"] == f"Practitioner/{doctor_user.id}"
    
    def test_prescription_to_fhir_with_medication_code(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            id=124,
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Ibuprofen",
            medication_code="M01AE01",
            dosage="400mg",
            quantity=30,
            instructions="Take as needed for pain",
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        coding = fhir["medicationCodeableConcept"]["coding"][0]
        assert coding["system"] == "http://www.whocc.no/atc"
        assert coding["code"] == "M01AE01"
        assert coding["display"] == "Ibuprofen"
    
    def test_prescription_to_fhir_status_mappings(self, test_session, doctor_user, patient_user):
        service = FHIRService(db_session=test_session, tenant_id="default")
        
        status_mappings = [
            ("ACTIVE", "active"),
            ("REVOKED", "cancelled"),
            ("EXPIRED", "stopped"),
            ("DISPENSED", "completed"),
            ("DRAFT", "draft"),
        ]
        
        for internal_status, expected_fhir_status in status_mappings:
            prescription = Prescription(
                id=200,
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                medication_name="Test Drug",
                dosage="100mg",
                quantity=10,
                status=internal_status,
            )
            prescription.tenant_id = "default"
            
            fhir = service.prescription_to_fhir(prescription)
            assert fhir["status"] == expected_fhir_status, f"Failed for {internal_status}"
    
    def test_prescription_to_fhir_dosage_parsing(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            id=125,
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Paracetamol",
            dosage="1000mg",
            quantity=20,
            instructions="Take two tablets every 6 hours",
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        dosage = fhir["dosageInstruction"][0]
        assert dosage["doseAndRate"][0]["doseQuantity"]["value"] == 1000
        assert dosage["doseAndRate"][0]["doseQuantity"]["unit"] == "mg"
    
    def test_prescription_to_fhir_repeat_count(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            id=126,
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Chronic Med",
            dosage="5mg",
            quantity=90,
            is_repeat=True,
            repeat_count=5,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        assert fhir["dispenseRequest"]["numberOfRepeatsAllowed"] == 5
    
    def test_prescription_to_fhir_validity_period(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            id=127,
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Test Med",
            dosage="10mg",
            quantity=30,
            date_issued=datetime(2026, 1, 1, 10, 0, 0),
            date_expires=datetime(2026, 4, 1, 23, 59, 59),
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        validity = fhir["dispenseRequest"]["validityPeriod"]
        assert "2026-01-01" in validity["start"]
        assert "2026-04-01" in validity["end"]


class TestFHIRReverseConversion:
    def test_fhir_to_prescription_basic(self, test_session):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": "Aspirin",
                "coding": [{
                    "system": "http://www.whocc.no/atc",
                    "code": "N02BA01",
                    "display": "Aspirin"
                }]
            },
            "subject": {"reference": "Patient/42"},
            "requester": {"reference": "Practitioner/99"},
            "dosageInstruction": [{
                "text": "Take one tablet daily",
                "doseAndRate": [{
                    "doseQuantity": {"value": 100, "unit": "mg"}
                }]
            }],
            "dispenseRequest": {
                "quantity": {"value": 30},
                "numberOfRepeatsAllowed": 2
            }
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        data = service.fhir_to_prescription_data(fhir_resource)
        
        assert data["medication_name"] == "Aspirin"
        assert data["medication_code"] == "N02BA01"
        assert data["patient_id"] == 42
        assert data["doctor_id"] == 99
        assert data["dosage"] == "100mg"
        assert data["quantity"] == 30
        assert data["is_repeat"] is True
        assert data["repeat_count"] == 2
        assert data["status"] == "ACTIVE"
    
    def test_fhir_to_prescription_status_mapping(self, test_session):
        service = FHIRService(db_session=test_session, tenant_id="default")
        
        fhir_statuses = [
            ("active", "ACTIVE"),
            ("cancelled", "REVOKED"),
            ("stopped", "EXPIRED"),
            ("completed", "DISPENSED"),
            ("draft", "DRAFT"),
        ]
        
        for fhir_status, expected_internal in fhir_statuses:
            fhir_resource = {
                "resourceType": "MedicationRequest",
                "status": fhir_status,
                "medicationCodeableConcept": {"text": "Test"},
                "subject": {"reference": "Patient/1"},
                "requester": {"reference": "Practitioner/1"},
            }
            
            data = service.fhir_to_prescription_data(fhir_resource)
            assert data["status"] == expected_internal, f"Failed for {fhir_status}"


class TestFHIRValidation:
    def test_validate_valid_medication_request(self, test_session):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Test Med"},
            "subject": {"reference": "Patient/1"},
            "requester": {"reference": "Practitioner/1"},
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.validate_medication_request(fhir_resource)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_missing_resource_type(self, test_session):
        fhir_resource = {
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Test Med"},
            "subject": {"reference": "Patient/1"},
            "requester": {"reference": "Practitioner/1"},
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.validate_medication_request(fhir_resource)
        
        assert result["valid"] is False
        assert any("resourceType" in e for e in result["errors"])
    
    def test_validate_missing_status(self, test_session):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Test Med"},
            "subject": {"reference": "Patient/1"},
            "requester": {"reference": "Practitioner/1"},
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.validate_medication_request(fhir_resource)
        
        assert result["valid"] is False
        assert any("status" in e.lower() for e in result["errors"])
    
    def test_validate_missing_subject(self, test_session):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Test Med"},
            "requester": {"reference": "Practitioner/1"},
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.validate_medication_request(fhir_resource)
        
        assert result["valid"] is False
        assert any("subject" in e.lower() for e in result["errors"])
    
    def test_validate_invalid_subject_reference(self, test_session):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Test Med"},
            "subject": {"reference": "Organization/1"},
            "requester": {"reference": "Practitioner/1"},
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.validate_medication_request(fhir_resource)
        
        assert result["valid"] is False
        assert any("Patient" in e for e in result["errors"])


class TestFHIRCRUD:
    def test_create_from_fhir(self, test_session, doctor_user, patient_user):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": "New Medication",
                "coding": [{"code": "TEST001"}]
            },
            "subject": {"reference": f"Patient/{patient_user.id}"},
            "requester": {"reference": f"Practitioner/{doctor_user.id}"},
            "dosageInstruction": [{
                "text": "Take twice daily",
                "doseAndRate": [{"doseQuantity": {"value": 250, "unit": "mg"}}]
            }],
            "dispenseRequest": {
                "quantity": {"value": 60},
                "numberOfRepeatsAllowed": 0
            }
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.create_from_fhir(fhir_resource, doctor_user.id)
        
        assert result["resourceType"] == "MedicationRequest"
        assert result["medicationCodeableConcept"]["text"] == "New Medication"
        assert result["requester"]["reference"] == f"Practitioner/{doctor_user.id}"
        assert result["subject"]["reference"] == f"Patient/{patient_user.id}"
    
    def test_create_from_fhir_invalid_resource(self, test_session, doctor_user):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.create_from_fhir(fhir_resource, doctor_user.id)
        
        assert result["resourceType"] == "OperationOutcome"
        assert len(result["issue"]) > 0
    
    def test_get_as_fhir_found(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Existing Med",
            dosage="50mg",
            quantity=10,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        test_session.refresh(prescription)
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.get_as_fhir(prescription.id)
        
        assert result is not None
        assert result["resourceType"] == "MedicationRequest"
        assert result["medicationCodeableConcept"]["text"] == "Existing Med"
    
    def test_get_as_fhir_not_found(self, test_session):
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.get_as_fhir(99999)
        
        assert result is None


class TestFHIRSearch:
    def test_search_by_patient(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Patient Search Test",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.search({"patient": str(patient_user.id)})
        
        assert result["resourceType"] == "Bundle"
        assert result["type"] == "searchset"
        assert len(result["entry"]) >= 1
    
    def test_search_by_status(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Status Test",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.search({"status": "active"})
        
        assert result["resourceType"] == "Bundle"
        assert all(e["resource"]["status"] == "active" for e in result.get("entry", []))
    
    def test_search_pagination(self, test_session, doctor_user, patient_user):
        for i in range(5):
            prescription = Prescription(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                medication_name=f"Paginated Med {i}",
                dosage="100mg",
                quantity=30,
                status="ACTIVE",
            )
            prescription.tenant_id = "default"
            test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.search({"_count": 2, "_offset": 0})
        
        assert result["resourceType"] == "Bundle"
        assert len(result["entry"]) <= 2
    
    def test_search_date_range(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Date Range Test",
            dosage="100mg",
            quantity=30,
            date_issued=datetime(2026, 2, 1, 10, 0, 0),
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.search({"authored-on": "ge2026-01-01", "_count": 100})
        
        assert result["resourceType"] == "Bundle"


class TestFHIRBundle:
    def test_create_bundle(self, test_session):
        service = FHIRService(db_session=test_session, tenant_id="default")
        
        entries = [
            {"resource": {"resourceType": "MedicationRequest", "id": "1"}},
            {"resource": {"resourceType": "MedicationRequest", "id": "2"}},
        ]
        
        bundle = service.create_bundle(entries, bundle_type="searchset", total=2)
        
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert bundle["total"] == 2
        assert len(bundle["entry"]) == 2
    
    def test_process_batch_bundle(self, test_session, doctor_user, patient_user):
        bundle = {
            "resourceType": "Bundle",
            "type": "batch",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {"text": "Bundle Med 1"},
                        "subject": {"reference": f"Patient/{patient_user.id}"},
                        "requester": {"reference": f"Practitioner/{doctor_user.id}"},
                    },
                    "request": {"method": "POST"}
                }
            ]
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.process_bundle(bundle, doctor_user.id)
        
        assert result["resourceType"] == "Bundle"
        assert result["type"] == "batch-response"
        assert len(result["entry"]) == 1
        assert result["entry"][0]["response"]["status"] == "201"
    
    def test_process_bundle_invalid_type(self, test_session, doctor_user):
        bundle = {
            "resourceType": "Bundle",
            "type": "message",
        }
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.process_bundle(bundle, doctor_user.id)
        
        assert result["resourceType"] == "OperationOutcome"


class TestFHIRCapability:
    def test_get_capability_statement(self, test_session):
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.get_capability_statement()
        
        assert result["resourceType"] == "CapabilityStatement"
        assert result["fhirVersion"] == "4.0.1"
        assert result["status"] == "active"
        assert len(result["rest"]) > 0
        
        resources = result["rest"][0]["resource"]
        medication_request = next(r for r in resources if r["type"] == "MedicationRequest")
        assert "read" in [i["code"] for i in medication_request["interaction"]]
        assert "create" in [i["code"] for i in medication_request["interaction"]]


class TestFHIRExport:
    def test_export_prescriptions(self, test_session, doctor_user, patient_user):
        for i in range(3):
            prescription = Prescription(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                medication_name=f"Export Med {i}",
                dosage="100mg",
                quantity=30,
                status="ACTIVE",
            )
            prescription.tenant_id = "default"
            test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.export_prescriptions()
        
        assert result["resourceType"] == "Bundle"
        assert result["type"] == "collection"
        assert len(result["entry"]) >= 3
    
    def test_export_with_filters(self, test_session, doctor_user, patient_user):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Filtered Export",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        result = service.export_prescriptions({"patient": patient_user.id})
        
        assert result["resourceType"] == "Bundle"
        assert all(
            e["resource"]["subject"]["reference"] == f"Patient/{patient_user.id}"
            for e in result["entry"]
        )


class TestFHIRAPIEndpoints:
    async def test_create_medication_request_endpoint(self, async_client, doctor_user, valid_jwt_token, patient_user):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "API Test Med"},
            "subject": {"reference": f"Patient/{patient_user.id}"},
            "requester": {"reference": f"Practitioner/{doctor_user.id}"},
        }
        
        response = await async_client.post(
            "/fhir/MedicationRequest",
            json=fhir_resource,
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["resourceType"] == "MedicationRequest"
        assert data["medicationCodeableConcept"]["text"] == "API Test Med"
    
    async def test_get_medication_request_endpoint(self, async_client, doctor_user, valid_jwt_token, patient_user, test_session):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Endpoint Test Med",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        test_session.refresh(prescription)
        
        response = await async_client.get(
            f"/fhir/MedicationRequest/rx-{prescription.id}",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "MedicationRequest"
        assert data["medicationCodeableConcept"]["text"] == "Endpoint Test Med"
    
    async def test_search_medication_requests_endpoint(self, async_client, valid_jwt_token, doctor_user, patient_user, test_session):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Search Test Med",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        
        response = await async_client.get(
            f"/fhir/MedicationRequest?patient={patient_user.id}",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
    
    async def test_capability_statement_endpoint(self, async_client, valid_jwt_token):
        response = await async_client.get("/fhir/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "CapabilityStatement"
        assert data["fhirVersion"] == "4.0.1"
    
    async def test_export_endpoint(self, async_client, valid_jwt_token, doctor_user, patient_user, test_session):
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Export Test Med",
            dosage="100mg",
            quantity=30,
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        test_session.refresh(prescription)
        
        response = await async_client.get(
            f"/fhir/MedicationRequest/{prescription.id}/$export",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "collection"
    
    async def test_unauthorized_access(self, async_client):
        response = await async_client.get("/fhir/MedicationRequest/123")
        assert response.status_code == 401
    
    async def test_patient_cannot_create_prescription(self, async_client, valid_patient_jwt_token):
        fhir_resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Unauthorized Med"},
            "subject": {"reference": "Patient/1"},
        }
        
        response = await async_client.post(
            "/fhir/MedicationRequest",
            json=fhir_resource,
            headers={"Authorization": f"Bearer {valid_patient_jwt_token}"}
        )
        
        assert response.status_code == 403


class TestDualModeCompatibility:
    def test_simplified_prescriptions_still_work(self, test_session, doctor_user, patient_user):
        from app.services.fhir import FHIRService
        
        prescription = Prescription(
            patient_id=patient_user.id,
            doctor_id=doctor_user.id,
            medication_name="Simplified Prescription",
            dosage="200mg",
            quantity=60,
            instructions="Take as directed",
            status="ACTIVE",
        )
        prescription.tenant_id = "default"
        test_session.add(prescription)
        test_session.commit()
        test_session.refresh(prescription)
        
        service = FHIRService(db_session=test_session, tenant_id="default")
        fhir = service.prescription_to_fhir(prescription)
        
        assert fhir["resourceType"] == "MedicationRequest"
        assert fhir["medicationCodeableConcept"]["text"] == "Simplified Prescription"
        
        prescriptions = test_session.query(Prescription).all()
        assert len(prescriptions) >= 1
        
        for p in prescriptions:
            assert hasattr(p, 'medication_name')
            assert hasattr(p, 'dosage')
            assert hasattr(p, 'quantity')
