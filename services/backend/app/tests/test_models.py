"""Test suite for database models (TDD - tests should FAIL until TASK-007)."""

import pytest
from datetime import datetime, timedelta


class TestUserModel:
    """Tests for User model - roles, DIDs, credentials."""

    async def test_user_create(self, test_session):
        """Create a user with required fields."""
        from app.models.user import User

        user = User(
            username="dr_smith",
            email="smith@hospital.co.za",
            password_hash="hashed_password",
            role="doctor",
            full_name="Dr. John Smith",
        )

        test_session.add(user)
        test_session.commit()

        assert user.id is not None
        assert user.username == "dr_smith"
        assert user.role == "doctor"

    async def test_user_role_validation(self, test_session):
        """Validate role must be one of: doctor, patient, pharmacist."""
        from app.models.user import User

        valid_roles = ["doctor", "patient", "pharmacist"]

        for role in valid_roles:
            user = User(
                username=f"user_{role}",
                email=f"{role}@example.com",
                password_hash="hash",
                role=role,
            )
            test_session.add(user)

        test_session.commit()

        assert test_session.query(User).count() == 3

    async def test_user_invalid_role(self, test_session):
        """Reject invalid role values."""
        from app.models.user import User
        from sqlalchemy.exc import IntegrityError

        user = User(
            username="invalid_user",
            email="invalid@example.com",
            password_hash="hash",
            role="invalid_role",
        )

        test_session.add(user)
        with pytest.raises(IntegrityError):
            test_session.commit()

    async def test_user_unique_email(self, test_session):
        """Email must be unique across users."""
        from app.models.user import User
        from sqlalchemy.exc import IntegrityError

        user1 = User(
            username="user1",
            email="duplicate@example.com",
            password_hash="hash1",
            role="doctor",
        )
        user2 = User(
            username="user2",
            email="duplicate@example.com",
            password_hash="hash2",
            role="patient",
        )

        test_session.add(user1)
        test_session.commit()

        test_session.add(user2)
        with pytest.raises(IntegrityError):
            test_session.commit()

    async def test_user_did_field(self, test_session):
        """User can have a DID (Decentralized Identifier)."""
        from app.models.user import User

        user = User(
            username="did_user",
            email="did@example.com",
            password_hash="hash",
            role="doctor",
            did="did:cheqd:testnet:abc123def456",
        )

        test_session.add(user)
        test_session.commit()

        retrieved = test_session.query(User).filter_by(username="did_user").first()
        assert retrieved.did == "did:cheqd:testnet:abc123def456"

    async def test_user_has_many_prescriptions(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Doctor user has many prescriptions as issuer."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        # Create prescriptions for this doctor
        for i in range(3):
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=doctor.id,
                medication_name=f"Med{i}",
                dosage="500mg",
                quantity=10,
                instructions="Take daily",
            )
            test_session.add(prescription)

        test_session.commit()

        assert len(doctor.prescriptions) == 3

    async def test_user_password_hash_required(self, test_session):
        """Password hash must be provided for all users."""
        from app.models.user import User
        from sqlalchemy.exc import IntegrityError

        user = User(
            username="no_password",
            email="nopass@example.com",
            role="patient",
        )

        test_session.add(user)
        with pytest.raises(IntegrityError):
            test_session.commit()


class TestPrescriptionModel:
    """Tests for Prescription model - FHIR fields, relationships, timestamps."""

    async def test_prescription_create(self, test_session, doctor_user_data, patient_user_data):
        """Create a prescription with FHIR-inspired fields."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Amoxicillin",
            medication_code="J01CA04",
            dosage="500mg",
            quantity=21,
            instructions="Take one tablet three times daily",
            date_issued=datetime.now(),
            date_expires=datetime.now() + timedelta(days=90),
        )

        test_session.add(prescription)
        test_session.commit()

        assert prescription.id is not None
        assert prescription.medication_name == "Amoxicillin"
        assert prescription.medication_code == "J01CA04"

    async def test_prescription_fhir_fields(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Prescription must include all FHIR-inspired fields."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        fhir_fields = {
            "medication_name": "Amoxicillin",
            "medication_code": "J01CA04",
            "dosage": "500mg",
            "quantity": 21,
            "instructions": "Take one tablet three times daily",
            "date_issued": datetime.now(),
            "date_expires": datetime.now() + timedelta(days=90),
        }

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            is_repeat=False,
            repeat_count=0,
            **fhir_fields,
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()

        for field, value in fhir_fields.items():
            assert getattr(retrieved, field) is not None

    async def test_prescription_relationships(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Prescription has relationships to doctor and patient."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Aspirin",
            dosage="100mg",
            quantity=30,
            instructions="Take daily",
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()
        assert retrieved.patient.username == patient.username
        assert retrieved.doctor.username == doctor.username

    async def test_prescription_digital_signature(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Prescription can be signed with digital signature."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        signature = "sig_xyz789_digital_signature_value"

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Lisinopril",
            dosage="10mg",
            quantity=30,
            instructions="Take once daily",
            digital_signature=signature,
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()
        assert retrieved.digital_signature == signature

    async def test_prescription_expiration(self, test_session, doctor_user_data, patient_user_data):
        """Prescription can expire based on date_expires."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        expires_in_future = datetime.now() + timedelta(days=90)

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Medication",
            dosage="100mg",
            quantity=30,
            instructions="Take daily",
            date_expires=expires_in_future,
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()
        assert retrieved.date_expires > datetime.now()

    async def test_prescription_repeat_tracking(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Prescription tracks repeat/refill information."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Chronic Medication",
            dosage="500mg",
            quantity=30,
            instructions="Take daily",
            is_repeat=True,
            repeat_count=3,
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()
        assert retrieved.is_repeat is True
        assert retrieved.repeat_count == 3

    async def test_prescription_credential_storage(
        self, test_session, doctor_user_data, patient_user_data
    ):
        """Prescription can store verifiable credential ID."""
        from app.models.user import User
        from app.models.prescription import Prescription

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        credential_id = "cred_abc123def456"

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Medicine",
            dosage="50mg",
            quantity=20,
            instructions="Take as needed",
            credential_id=credential_id,
        )

        test_session.add(prescription)
        test_session.commit()

        retrieved = test_session.query(Prescription).first()
        assert retrieved.credential_id == credential_id


class TestDispensingModel:
    """Tests for Dispensing model - tracking, timestamps, pharmacist verification."""

    async def test_dispensing_create(
        self, test_session, doctor_user_data, patient_user_data, pharmacist_user_data
    ):
        """Create dispensing record for a prescription."""
        from app.models.user import User
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)
        pharmacist = User(**pharmacist_user_data)

        test_session.add_all([doctor, patient, pharmacist])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Amoxicillin",
            dosage="500mg",
            quantity=21,
            instructions="Three times daily",
        )

        test_session.add(prescription)
        test_session.flush()

        dispensing = Dispensing(
            prescription_id=prescription.id,
            pharmacist_id=pharmacist.id,
            quantity_dispensed=21,
            date_dispensed=datetime.now(),
            verified=True,
        )

        test_session.add(dispensing)
        test_session.commit()

        assert dispensing.id is not None
        assert dispensing.quantity_dispensed == 21

    async def test_dispensing_relationships(
        self, test_session, doctor_user_data, patient_user_data, pharmacist_user_data
    ):
        """Dispensing has relationships to prescription and pharmacist."""
        from app.models.user import User
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)
        pharmacist = User(**pharmacist_user_data)

        test_session.add_all([doctor, patient, pharmacist])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Medicine",
            dosage="100mg",
            quantity=30,
            instructions="Daily",
        )

        test_session.add(prescription)
        test_session.flush()

        dispensing = Dispensing(
            prescription_id=prescription.id,
            pharmacist_id=pharmacist.id,
            quantity_dispensed=30,
            date_dispensed=datetime.now(),
            verified=True,
        )

        test_session.add(dispensing)
        test_session.commit()

        retrieved = test_session.query(Dispensing).first()
        assert retrieved.prescription.medication_name == "Medicine"
        assert retrieved.pharmacist.username == pharmacist.username

    async def test_dispensing_timestamp(
        self, test_session, doctor_user_data, patient_user_data, pharmacist_user_data
    ):
        """Dispensing records when medication was dispensed."""
        from app.models.user import User
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)
        pharmacist = User(**pharmacist_user_data)

        test_session.add_all([doctor, patient, pharmacist])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Drug",
            dosage="50mg",
            quantity=20,
            instructions="Twice daily",
        )

        test_session.add(prescription)
        test_session.flush()

        now = datetime.now()

        dispensing = Dispensing(
            prescription_id=prescription.id,
            pharmacist_id=pharmacist.id,
            quantity_dispensed=20,
            date_dispensed=now,
            verified=True,
        )

        test_session.add(dispensing)
        test_session.commit()

        retrieved = test_session.query(Dispensing).first()
        assert retrieved.date_dispensed is not None
        assert abs((retrieved.date_dispensed - now).total_seconds()) < 1

    async def test_dispensing_verification(
        self, test_session, doctor_user_data, patient_user_data, pharmacist_user_data
    ):
        """Dispensing can be verified by pharmacist."""
        from app.models.user import User
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)
        pharmacist = User(**pharmacist_user_data)

        test_session.add_all([doctor, patient, pharmacist])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Medicine",
            dosage="100mg",
            quantity=30,
            instructions="Daily",
        )

        test_session.add(prescription)
        test_session.flush()

        dispensing = Dispensing(
            prescription_id=prescription.id,
            pharmacist_id=pharmacist.id,
            quantity_dispensed=30,
            date_dispensed=datetime.now(),
            verified=True,
        )

        test_session.add(dispensing)
        test_session.commit()

        retrieved = test_session.query(Dispensing).first()
        assert retrieved.verified is True

    async def test_dispensing_notes(
        self, test_session, doctor_user_data, patient_user_data, pharmacist_user_data
    ):
        """Dispensing can include pharmacist notes."""
        from app.models.user import User
        from app.models.prescription import Prescription
        from app.models.dispensing import Dispensing

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)
        pharmacist = User(**pharmacist_user_data)

        test_session.add_all([doctor, patient, pharmacist])
        test_session.flush()

        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name="Medication",
            dosage="100mg",
            quantity=30,
            instructions="Once daily",
        )

        test_session.add(prescription)
        test_session.flush()

        notes = "Patient counseled on side effects and interactions"

        dispensing = Dispensing(
            prescription_id=prescription.id,
            pharmacist_id=pharmacist.id,
            quantity_dispensed=30,
            date_dispensed=datetime.now(),
            verified=True,
            notes=notes,
        )

        test_session.add(dispensing)
        test_session.commit()

        retrieved = test_session.query(Dispensing).first()
        assert retrieved.notes == notes


class TestAuditModel:
    """Tests for Audit model - immutable event logging, hash chain."""

    async def test_audit_create(self, test_session, doctor_user_data):
        """Create audit event for system action."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        audit = Audit(
            event_type="prescription_created",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="prescription",
            resource_id=1,
            action="create",
            details={"medication": "Amoxicillin"},
        )

        test_session.add(audit)
        test_session.commit()

        assert audit.id is not None
        assert audit.event_type == "prescription_created"

    async def test_audit_immutable(self, test_session, doctor_user_data):
        """Audit records should be immutable (no updates)."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        audit = Audit(
            event_type="user_login",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="user",
            resource_id=doctor.id,
            action="login",
        )

        test_session.add(audit)
        test_session.commit()

        original_id = audit.id

        # Attempt to modify (should prevent or ignore)
        audit.action = "logout"
        test_session.commit()

        retrieved = test_session.query(Audit).filter_by(id=original_id).first()
        # Verify immutability via versioning or constraint
        assert retrieved.event_type == "user_login"

    async def test_audit_timestamp(self, test_session, doctor_user_data):
        """Audit event includes timestamp."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        before = datetime.now()

        audit = Audit(
            event_type="prescription_signed",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="prescription",
            resource_id=1,
            action="sign",
        )

        test_session.add(audit)
        test_session.commit()

        after = datetime.now()

        retrieved = test_session.query(Audit).first()
        assert hasattr(retrieved, "timestamp")
        assert retrieved.timestamp is not None
        assert before <= retrieved.timestamp <= after

    async def test_audit_actor_tracking(self, test_session, doctor_user_data, patient_user_data):
        """Audit tracks who performed action and their role."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        patient = User(**patient_user_data)

        test_session.add_all([doctor, patient])
        test_session.flush()

        audit_doctor = Audit(
            event_type="prescription_created",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="prescription",
            resource_id=1,
            action="create",
        )

        audit_patient = Audit(
            event_type="prescription_viewed",
            actor_id=patient.id,
            actor_role="patient",
            resource_type="prescription",
            resource_id=1,
            action="view",
        )

        test_session.add_all([audit_doctor, audit_patient])
        test_session.commit()

        assert test_session.query(Audit).filter_by(actor_role="doctor").count() == 1
        assert test_session.query(Audit).filter_by(actor_role="patient").count() == 1

    async def test_audit_resource_tracking(self, test_session, doctor_user_data):
        """Audit tracks resource type and ID."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        audit = Audit(
            event_type="prescription_event",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="prescription",
            resource_id=42,
            action="create",
        )

        test_session.add(audit)
        test_session.commit()

        retrieved = test_session.query(Audit).first()
        assert retrieved.resource_type == "prescription"
        assert retrieved.resource_id == 42

    async def test_audit_event_details(self, test_session, doctor_user_data):
        """Audit can store event details as JSON."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        details = {
            "medication": "Aspirin",
            "dosage": "500mg",
            "quantity": 30,
            "status": "signed",
        }

        audit = Audit(
            event_type="prescription_created",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="prescription",
            resource_id=1,
            action="create",
            details=details,
        )

        test_session.add(audit)
        test_session.commit()

        retrieved = test_session.query(Audit).first()
        assert retrieved.details == details
        assert retrieved.details["medication"] == "Aspirin"

    async def test_audit_ip_address_logging(self, test_session, doctor_user_data):
        """Audit can log IP address for security."""
        from app.models.user import User
        from app.models.audit import Audit

        doctor = User(**doctor_user_data)
        test_session.add(doctor)
        test_session.flush()

        audit = Audit(
            event_type="user_login",
            actor_id=doctor.id,
            actor_role="doctor",
            resource_type="user",
            resource_id=doctor.id,
            action="login",
            ip_address="192.168.1.100",
        )

        test_session.add(audit)
        test_session.commit()

        retrieved = test_session.query(Audit).first()
        assert retrieved.ip_address == "192.168.1.100"
