#!/usr/bin/env python3
"""Enhanced demo data seed script for digital prescription system.

US-019: Demo Preparation & Test Data
Populates the database with realistic test data for doctors, patients, 
pharmacists, and prescriptions. Idempotent - can run multiple times safely.

Leverages all new features:
- FHIR R4 metadata
- Audit trail logging
- Revocation workflows
- Time validation
- Scheduled revocations
- Multi-tenant support

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --doctors 5 --patients 10 --pharmacists 3 --prescriptions 30

Environment:
    DATABASE_URL: Database connection string (default: sqlite:///./test.db)
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
import uuid
from pathlib import Path
from typing import List, Tuple, Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.user import User
from app.models.prescription import Prescription
from app.models.tenant import Tenant
from app.models.audit import Audit
from app.models.dispensing import Dispensing
from app.core.security import hash_password
from app.services.fhir import FHIRService


# =============================================================================
# DEMO DATA DEFINITIONS
# =============================================================================

# Extended doctor data (5+ doctors)
DEMO_DOCTORS = [
    {
        "email": "sarah.johnson@hospital.co.za",
        "full_name": "Dr. Sarah Johnson",
        "registration_number": "MP1234567",
        "password": "Demo@2024",
        "specialty": "General Practice",
    },
    {
        "email": "thabo.mokoena@clinic.co.za",
        "full_name": "Dr. Thabo Mokoena",
        "registration_number": "MP2345678",
        "password": "Demo@2024",
        "specialty": "Internal Medicine",
    },
    {
        "email": "ayesha.patel@pediatrics.co.za",
        "full_name": "Dr. Ayesha Patel",
        "registration_number": "MP3456789",
        "password": "Demo@2024",
        "specialty": "Pediatrics",
    },
    {
        "email": "michael.brown@surgery.co.za",
        "full_name": "Dr. Michael Brown",
        "registration_number": "MP4567890",
        "password": "Demo@2024",
        "specialty": "Surgery",
    },
    {
        "email": "linda.vanwyk@cardiology.co.za",
        "full_name": "Dr. Linda Van Wyk",
        "registration_number": "MP5678901",
        "password": "Demo@2024",
        "specialty": "Cardiology",
    },
]

# Extended patient data (10+ patients)
DEMO_PATIENTS = [
    {
        "email": "john.smith@example.com",
        "full_name": "John Smith",
        "password": "Demo@2024",
        "id_number": "8001015001001",
    },
    {
        "email": "mary.williams@example.com",
        "full_name": "Mary Williams",
        "password": "Demo@2024",
        "id_number": "8502025002002",
    },
    {
        "email": "sipho.dlamini@example.com",
        "full_name": "Sipho Dlamini",
        "password": "Demo@2024",
        "id_number": "9003035003003",
    },
    {
        "email": "fatima.hassan@example.com",
        "full_name": "Fatima Hassan",
        "password": "Demo@2024",
        "id_number": "8804045004004",
    },
    {
        "email": "james.brown@example.com",
        "full_name": "James Brown",
        "password": "Demo@2024",
        "id_number": "7505055005005",
    },
    {
        "email": "precious.ndlovu@example.com",
        "full_name": "Precious Ndlovu",
        "password": "Demo@2024",
        "id_number": "9206065006006",
    },
    {
        "email": "pieter.duplooy@example.com",
        "full_name": "Pieter Du Plooy",
        "password": "Demo@2024",
        "id_number": "7007075007007",
    },
    {
        "email": "grace.molefe@example.com",
        "full_name": "Grace Molefe",
        "password": "Demo@2024",
        "id_number": "8308085008008",
    },
    {
        "email": "david.patel@example.com",
        "full_name": "David Patel",
        "password": "Demo@2024",
        "id_number": "9109095009009",
    },
    {
        "email": "susan.vanwyk@example.com",
        "full_name": "Susan Van Wyk",
        "password": "Demo@2024",
        "id_number": "7810105010010",
    },
]

# Extended pharmacist data (3+ pharmacists)
DEMO_PHARMACISTS = [
    {
        "email": "lisa.chen@pharmacy.co.za",
        "full_name": "Lisa Chen",
        "registration_number": "P123456",
        "password": "Demo@2024",
        "pharmacy": "City Centre Pharmacy",
    },
    {
        "email": "david.nkosi@hospital.co.za",
        "full_name": "David Nkosi",
        "registration_number": "P234567",
        "password": "Demo@2024",
        "pharmacy": "Metro Hospital Pharmacy",
    },
    {
        "email": "emma.thompson@clinic.co.za",
        "full_name": "Emma Thompson",
        "registration_number": "P345678",
        "password": "Demo@2024",
        "pharmacy": "Westville Clinic Pharmacy",
    },
]

# Medication catalog with FHIR-compatible codes
MEDICATIONS = [
    {"name": "Amoxicillin", "dosage": "500mg", "quantity": 21, "code": "J01CA04", "instructions": "Take one capsule three times daily with food for 7 days"},
    {"name": "Metformin", "dosage": "850mg", "quantity": 60, "code": "A10BA02", "instructions": "Take one tablet twice daily with meals"},
    {"name": "Lisinopril", "dosage": "10mg", "quantity": 30, "code": "C09AA03", "instructions": "Take one tablet daily in the morning"},
    {"name": "Atorvastatin", "dosage": "20mg", "quantity": 30, "code": "C10AA05", "instructions": "Take one tablet daily at bedtime"},
    {"name": "Omeprazole", "dosage": "20mg", "quantity": 30, "code": "A02BC01", "instructions": "Take one capsule daily before breakfast"},
    {"name": "Paracetamol", "dosage": "500mg", "quantity": 24, "code": "N02BE01", "instructions": "Take 1-2 tablets every 4-6 hours as needed for pain"},
    {"name": "Ibuprofen", "dosage": "400mg", "quantity": 30, "code": "M01AE01", "instructions": "Take one tablet three times daily with food"},
    {"name": "Fluconazole", "dosage": "150mg", "quantity": 2, "code": "D01AC15", "instructions": "Take one capsule, repeat in 7 days if needed"},
    {"name": "Amlodipine", "dosage": "5mg", "quantity": 30, "code": "C08CA01", "instructions": "Take one tablet daily"},
    {"name": "Losartan", "dosage": "50mg", "quantity": 30, "code": "C09CA01", "instructions": "Take one tablet daily"},
]

# Demo scenarios for summary
DEMO_SCENARIOS = [
    {
        "id": 1,
        "name": "Happy Path",
        "description": "Complete workflow: Doctor creates prescription → digitally signs → patient receives → shares with pharmacist → verification → dispensing",
        "prescriptions": ["happy_path_rx"],
    },
    {
        "id": 2,
        "name": "Multi-Medication",
        "description": "Patient with 3+ concurrent medications prescribed together for complex condition management",
        "prescriptions": ["multi_med_1", "multi_med_2", "multi_med_3"],
    },
    {
        "id": 3,
        "name": "Repeat Prescription",
        "description": "Chronic medication with repeat authorization, partially dispensed over multiple pharmacy visits",
        "prescriptions": ["repeat_partial_rx"],
    },
    {
        "id": 4,
        "name": "Expired Prescription",
        "description": "Prescription that has passed its expiration date, demonstrating time-based validation",
        "prescriptions": ["expired_rx_1", "expired_rx_2", "expired_rx_3"],
    },
    {
        "id": 5,
        "name": "Revoked Prescription",
        "description": "Prescription revoked by doctor due to prescribing error, with audit trail documentation",
        "prescriptions": ["revoked_rx_1", "revoked_rx_2"],
    },
    {
        "id": 6,
        "name": "Doctor Verification",
        "description": "Demonstrates valid vs invalid HPCSA registration verification scenarios",
        "prescriptions": ["verification_rx"],
    },
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "sqlite:///./test.db")


def create_session(database_url: str) -> Tuple[Any, Any]:
    """Create database engine and session.
    
    Args:
        database_url: Connection string for database
        
    Returns:
        Tuple of (engine, SessionLocal class)
    """
    # Check if SQLite
    if "sqlite://" in database_url:
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal


def generate_mock_did() -> str:
    """Generate a mock DID for testing."""
    return f"did:cheqd:testnet:{uuid.uuid4().hex[:16]}"


def generate_credential_id() -> str:
    """Generate a mock credential ID."""
    return f"cred_{uuid.uuid4().hex[:16]}"


def generate_digital_signature() -> str:
    """Generate a mock digital signature."""
    return f"sig_{uuid.uuid4().hex[:32]}"


def user_exists(session: Session, email: str, tenant_id: str = "default") -> bool:
    """Check if a user with given email already exists."""
    return session.query(User).filter_by(email=email, tenant_id=tenant_id).first() is not None


def ensure_default_tenant(session: Session) -> Tenant:
    """Ensure the default tenant exists."""
    tenant = session.query(Tenant).filter_by(id="default").first()
    if not tenant:
        tenant = Tenant(
            id="default",
            name="Default Demo Tenant",
            is_active=True,
        )
        session.add(tenant)
        session.flush()
        print("✅ Created default tenant")
    return tenant


# =============================================================================
# SEED FUNCTIONS
# =============================================================================

def seed_doctors(session: Session, count: int = 5, tenant_id: str = "default") -> List[User]:
    """Create test doctors in database.
    
    Args:
        session: Database session
        count: Number of doctors to create (uses first N from DEMO_DOCTORS)
        tenant_id: Tenant identifier for multi-tenancy
        
    Returns:
        List of created User objects
    """
    created = []
    doctors_to_create = DEMO_DOCTORS[:count] if count <= len(DEMO_DOCTORS) else DEMO_DOCTORS
    
    for doctor_data in doctors_to_create:
        if user_exists(session, doctor_data["email"], tenant_id):
            print(f"⏭️  Doctor '{doctor_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                username=doctor_data["email"],
                email=doctor_data["email"],
                full_name=doctor_data["full_name"],
                password_hash=hash_password(doctor_data["password"]),
                role="doctor",
                registration_number=doctor_data["registration_number"],
                did=generate_mock_did(),
                tenant_id=tenant_id,
            )
            session.add(user)
            session.flush()
            created.append(user)
            print(f"✅ Created doctor: {doctor_data['full_name']} ({doctor_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating doctor '{doctor_data['email']}': {e}")
    
    return created


def seed_patients(session: Session, count: int = 10, tenant_id: str = "default") -> List[User]:
    """Create test patients in database.
    
    Args:
        session: Database session
        count: Number of patients to create (uses first N from DEMO_PATIENTS)
        tenant_id: Tenant identifier for multi-tenancy
        
    Returns:
        List of created User objects
    """
    created = []
    patients_to_create = DEMO_PATIENTS[:count] if count <= len(DEMO_PATIENTS) else DEMO_PATIENTS
    
    for patient_data in patients_to_create:
        if user_exists(session, patient_data["email"], tenant_id):
            print(f"⏭️  Patient '{patient_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                username=patient_data["email"],
                email=patient_data["email"],
                full_name=patient_data["full_name"],
                password_hash=hash_password(patient_data["password"]),
                role="patient",
                registration_number=None,
                did=generate_mock_did(),
                tenant_id=tenant_id,
            )
            session.add(user)
            session.flush()
            created.append(user)
            print(f"✅ Created patient: {patient_data['full_name']} ({patient_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating patient '{patient_data['email']}': {e}")
    
    return created


def seed_pharmacists(session: Session, count: int = 3, tenant_id: str = "default") -> List[User]:
    """Create test pharmacists in database.
    
    Args:
        session: Database session
        count: Number of pharmacists to create (uses first N from DEMO_PHARMACISTS)
        tenant_id: Tenant identifier for multi-tenancy
        
    Returns:
        List of created User objects
    """
    created = []
    pharmacists_to_create = DEMO_PHARMACISTS[:count] if count <= len(DEMO_PHARMACISTS) else DEMO_PHARMACISTS
    
    for pharmacist_data in pharmacists_to_create:
        if user_exists(session, pharmacist_data["email"], tenant_id):
            print(f"⏭️  Pharmacist '{pharmacist_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                username=pharmacist_data["email"],
                email=pharmacist_data["email"],
                full_name=pharmacist_data["full_name"],
                password_hash=hash_password(pharmacist_data["password"]),
                role="pharmacist",
                registration_number=pharmacist_data["registration_number"],
                did=generate_mock_did(),
                tenant_id=tenant_id,
            )
            session.add(user)
            session.flush()
            created.append(user)
            print(f"✅ Created pharmacist: {pharmacist_data['full_name']} ({pharmacist_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating pharmacist '{pharmacist_data['email']}': {e}")
    
    return created


def create_audit_entry(
    session: Session,
    event_type: str,
    actor_id: int,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: int,
    details: Optional[Dict] = None,
    tenant_id: str = "default",
    correlation_id: Optional[str] = None,
    result: str = "success"
) -> Audit:
    """Create an audit log entry.
    
    Args:
        session: Database session
        event_type: Type of event (e.g., "prescription.created")
        actor_id: User ID who performed action
        actor_role: Role of actor ("doctor", "pharmacist", "patient")
        action: Action taken ("create", "sign", "dispense", etc.)
        resource_type: Type of resource ("prescription", "user", etc.)
        resource_id: ID of resource acted upon
        details: Optional JSON details
        tenant_id: Tenant identifier
        correlation_id: Optional correlation ID for event chains
        result: Result of the action ("success", "failure")
        
    Returns:
        Created Audit object
    """
    from app.services.audit import AuditService
    
    audit = Audit(
        event_type=event_type,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        result=result,
        timestamp=datetime.utcnow()
    )
    session.add(audit)
    session.flush()
    return audit


def create_dispensing_record(
    session: Session,
    prescription_id: int,
    pharmacist_id: int,
    quantity_dispensed: int,
    verified: bool = True,
    notes: Optional[str] = None,
    tenant_id: str = "default"
) -> Dispensing:
    """Create a dispensing record.
    
    Args:
        session: Database session
        prescription_id: ID of prescription being dispensed
        pharmacist_id: ID of pharmacist dispensing
        quantity_dispensed: Quantity actually dispensed
        verified: Whether the prescription was verified
        notes: Optional dispensing notes
        tenant_id: Tenant identifier
        
    Returns:
        Created Dispensing object
    """
    dispensing = Dispensing(
        prescription_id=prescription_id,
        pharmacist_id=pharmacist_id,
        quantity_dispensed=quantity_dispensed,
        verified=verified,
        notes=notes,
        tenant_id=tenant_id,
    )
    session.add(dispensing)
    session.flush()
    return dispensing


def seed_prescriptions_with_states(
    session: Session,
    doctors: List[User],
    patients: List[User],
    pharmacists: List[User],
    tenant_id: str = "default"
) -> Dict[str, List[Prescription]]:
    """Create prescriptions in various states with full audit trails.
    
    Creates 30 prescriptions across 6 states:
    - DRAFT: 5
    - ACTIVE: 10
    - EXPIRED: 3
    - REVOKED: 2
    - DISPENSED: 5
    - PARTIAL_DISPENSED: 5
    
    Args:
        session: Database session
        doctors: List of doctor users
        patients: List of patient users
        pharmacists: List of pharmacist users
        tenant_id: Tenant identifier
        
    Returns:
        Dict mapping state names to lists of prescriptions
    """
    created_by_state = {
        "DRAFT": [],
        "ACTIVE": [],
        "EXPIRED": [],
        "REVOKED": [],
        "DISPENSED": [],
        "PARTIAL": [],
    }
    
    today = datetime.utcnow()
    
    # Helper to get doctor/patient for a prescription
    def get_users(idx: int) -> Tuple[User, User]:
        doctor = doctors[idx % len(doctors)]
        patient = patients[idx % len(patients)]
        return doctor, patient
    
    # =============================================================================
    # SCENARIO 1: Happy Path (1 prescription - ACTIVE, ready to dispense)
    # =============================================================================
    doctor, patient = get_users(0)
    med = MEDICATIONS[0]  # Amoxicillin
    
    rx = Prescription(
        patient_id=patient.id,
        doctor_id=doctor.id,
        medication_name=med["name"],
        medication_code=med["code"],
        dosage=med["dosage"],
        quantity=med["quantity"],
        instructions=med["instructions"],
        date_issued=today - timedelta(days=2),
        date_expires=today + timedelta(days=28),
        is_repeat=False,
        repeat_count=0,
        status="ACTIVE",
        digital_signature=generate_digital_signature(),
        credential_id=generate_credential_id(),
        tenant_id=tenant_id,
    )
    session.add(rx)
    session.flush()
    created_by_state["ACTIVE"].append(rx)
    
    # Audit: created, signed
    create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                       "prescription", rx.id, {"medication": med["name"]}, tenant_id)
    create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                       "prescription", rx.id, {"signature_type": "digital"}, tenant_id)
    create_audit_entry(session, "prescription.shared", patient.id, "patient", "share", 
                       "prescription", rx.id, {"shared_with": "pharmacist"}, tenant_id)
    print(f"✅ Created happy path prescription: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # SCENARIO 2: Multi-medication (3 prescriptions for same patient)
    # =============================================================================
    doctor, patient = get_users(1)  # Same patient for all 3
    multi_meds = [MEDICATIONS[1], MEDICATIONS[2], MEDICATIONS[3]]  # Metformin, Lisinopril, Atorvastatin
    
    for idx, med in enumerate(multi_meds):
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=idx),
            date_expires=today + timedelta(days=90),
            is_repeat=True,
            repeat_count=5,
            status="ACTIVE",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["ACTIVE"].append(rx)
        
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"], "scenario": "multi_medication"}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        print(f"✅ Created multi-med prescription {idx+1}/3: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # SCENARIO 3: Repeat prescription with partial dispensing
    # =============================================================================
    doctor, patient = get_users(2)
    med = MEDICATIONS[4]  # Omeprazole
    
    rx = Prescription(
        patient_id=patient.id,
        doctor_id=doctor.id,
        medication_name=med["name"],
        medication_code=med["code"],
        dosage=med["dosage"],
        quantity=med["quantity"],
        instructions=med["instructions"],
        date_issued=today - timedelta(days=30),
        date_expires=today + timedelta(days=60),
        is_repeat=True,
        repeat_count=3,
        status="ACTIVE",  # Still active, partially dispensed
        digital_signature=generate_digital_signature(),
        credential_id=generate_credential_id(),
        tenant_id=tenant_id,
    )
    session.add(rx)
    session.flush()
    created_by_state["PARTIAL"].append(rx)
    
    # Audit trail for repeat prescription
    create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                       "prescription", rx.id, {"medication": med["name"], "is_repeat": True, "repeat_count": 3}, tenant_id)
    create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                       "prescription", rx.id, {}, tenant_id)
    
    # First dispensing (10 of 30 tablets)
    pharmacist = pharmacists[0]
    dispensing = create_dispensing_record(session, rx.id, pharmacist.id, 10, True, 
                                          "First repeat - 10 tablets dispensed", tenant_id)
    create_audit_entry(session, "prescription.dispensed", pharmacist.id, "pharmacist", "dispense", 
                       "prescription", rx.id, {"quantity_dispensed": 10, "remaining": 20}, tenant_id)
    
    # Second dispensing (10 more tablets)
    dispensing2 = create_dispensing_record(session, rx.id, pharmacist.id, 10, True, 
                                           "Second repeat - 10 tablets dispensed", tenant_id)
    create_audit_entry(session, "prescription.dispensed", pharmacist.id, "pharmacist", "dispense", 
                       "prescription", rx.id, {"quantity_dispensed": 10, "remaining": 10}, tenant_id)
    
    print(f"✅ Created repeat prescription with partial dispensing: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # SCENARIO 4: Expired prescriptions (3)
    # =============================================================================
    for i in range(3):
        doctor, patient = get_users(3 + i)
        med = MEDICATIONS[5 + i]  # Paracetamol, Ibuprofen, Fluconazole
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=60),
            date_expires=today - timedelta(days=30),  # Expired 30 days ago
            is_repeat=False,
            repeat_count=0,
            status="EXPIRED",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["EXPIRED"].append(rx)
        
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"]}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        create_audit_entry(session, "prescription.expired", 0, "system", "expire", 
                           "prescription", rx.id, {"reason": "past_expiry_date"}, tenant_id)
        print(f"✅ Created expired prescription: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # SCENARIO 5: Revoked prescriptions (2)
    # =============================================================================
    for i in range(2):
        doctor, patient = get_users(6 + i)
        med = MEDICATIONS[7 + i] if i < 2 else MEDICATIONS[0]
        med = MEDICATIONS[i % len(MEDICATIONS)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=5),
            date_expires=today + timedelta(days=25),
            is_repeat=False,
            repeat_count=0,
            status="REVOKED",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["REVOKED"].append(rx)
        
        # Full audit trail for revoked prescription
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"]}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        
        reasons = ["prescribing_error", "adverse_reaction"]
        create_audit_entry(session, "prescription.revoked", doctor.id, "doctor", "revoke", 
                           "prescription", rx.id, {"reason": reasons[i], "notes": "Revoked during demo"}, tenant_id)
        print(f"✅ Created revoked prescription: {med['name']} for {patient.full_name} (reason: {reasons[i]})")
    
    # =============================================================================
    # SCENARIO 6: Doctor verification scenario + Additional ACTIVE prescriptions
    # =============================================================================
    # Create remaining ACTIVE prescriptions (need 10 total, have 4 so far)
    remaining_active = 10 - len(created_by_state["ACTIVE"])
    for i in range(remaining_active):
        doctor, patient = get_users(8 + i)
        med = MEDICATIONS[i % len(MEDICATIONS)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=i % 7),
            date_expires=today + timedelta(days=30 + (i % 60)),
            is_repeat=(i % 3 == 0),
            repeat_count=(2 if (i % 3 == 0) else 0),
            status="ACTIVE",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["ACTIVE"].append(rx)
        
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"]}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
    
    print(f"✅ Created {remaining_active} additional ACTIVE prescriptions")
    
    # =============================================================================
    # Create DRAFT prescriptions (5)
    # =============================================================================
    for i in range(5):
        doctor, patient = get_users(10 + i)
        med = MEDICATIONS[(i + 3) % len(MEDICATIONS)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today,
            date_expires=today + timedelta(days=30),
            is_repeat=False,
            repeat_count=0,
            status="DRAFT",  # Not yet signed
            digital_signature=None,
            credential_id=None,
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["DRAFT"].append(rx)
        
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"], "status": "draft"}, tenant_id)
        print(f"✅ Created DRAFT prescription: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # Create DISPENSED prescriptions (5 fully dispensed)
    # =============================================================================
    for i in range(5):
        doctor, patient = get_users(15 + i)
        med = MEDICATIONS[(i + 5) % len(MEDICATIONS)]
        pharmacist = pharmacists[i % len(pharmacists)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=14),
            date_expires=today + timedelta(days=16),
            is_repeat=(i % 2 == 0),
            repeat_count=(1 if (i % 2 == 0) else 0),
            status="DISPENSED",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["DISPENSED"].append(rx)
        
        # Audit trail
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"]}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        create_audit_entry(session, "prescription.shared", patient.id, "patient", "share", 
                           "prescription", rx.id, {}, tenant_id)
        create_audit_entry(session, "prescription.verified", pharmacist.id, "pharmacist", "verify", 
                           "prescription", rx.id, {"verification_result": "valid"}, tenant_id)
        
        # Dispensing record
        dispensing = create_dispensing_record(session, rx.id, pharmacist.id, med["quantity"], True, 
                                              "Fully dispensed", tenant_id)
        create_audit_entry(session, "prescription.dispensed", pharmacist.id, "pharmacist", "dispense", 
                           "prescription", rx.id, {"quantity_dispensed": med["quantity"], "fully_dispensed": True}, tenant_id)
        
        print(f"✅ Created DISPENSED prescription: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # Create PARTIAL_DISPENSED prescriptions (5 more, need 5 total, have 1)
    # Create 4 more partial prescriptions
    # =============================================================================
    for i in range(4):
        doctor, patient = get_users(20 + i)
        med = MEDICATIONS[(i + 7) % len(MEDICATIONS)]
        pharmacist = pharmacists[i % len(pharmacists)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=20),
            date_expires=today + timedelta(days=40),
            is_repeat=True,
            repeat_count=3,
            status="ACTIVE",  # Still active, partially dispensed
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        created_by_state["PARTIAL"].append(rx)
        
        # Audit trail
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"], "is_repeat": True}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        
        # Partial dispensing (half the quantity)
        partial_qty = med["quantity"] // 2
        dispensing = create_dispensing_record(session, rx.id, pharmacist.id, partial_qty, True, 
                                              f"Partial dispense - {partial_qty} of {med['quantity']}", tenant_id)
        create_audit_entry(session, "prescription.dispensed", pharmacist.id, "pharmacist", "dispense", 
                           "prescription", rx.id, {"quantity_dispensed": partial_qty, "partial": True}, tenant_id)
        
        print(f"✅ Created PARTIAL dispensed prescription: {med['name']} for {patient.full_name}")
    
    # =============================================================================
    # Create scheduled revocations (2-3 prescriptions with future revocation dates)
    # =============================================================================
    for i in range(3):
        doctor, patient = get_users(24 + i)
        med = MEDICATIONS[i % len(MEDICATIONS)]
        
        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            medication_name=med["name"],
            medication_code=med["code"],
            dosage=med["dosage"],
            quantity=med["quantity"],
            instructions=med["instructions"],
            date_issued=today - timedelta(days=3),
            date_expires=today + timedelta(days=27),
            is_repeat=False,
            repeat_count=0,
            status="ACTIVE",
            digital_signature=generate_digital_signature(),
            credential_id=generate_credential_id(),
            tenant_id=tenant_id,
        )
        session.add(rx)
        session.flush()
        
        # Create audit entries
        create_audit_entry(session, "prescription.created", doctor.id, "doctor", "create", 
                           "prescription", rx.id, {"medication": med["name"]}, tenant_id)
        create_audit_entry(session, "prescription.signed", doctor.id, "doctor", "sign", 
                           "prescription", rx.id, {}, tenant_id)
        
        # Schedule revocation for future date
        schedule_id = str(uuid.uuid4())
        scheduled_date = today + timedelta(days=7 + i * 3)  # 7, 10, 13 days from now
        
        create_audit_entry(
            session, 
            "revocation_scheduled", 
            doctor.id, 
            "doctor", 
            "schedule_revocation", 
            "prescription", 
            rx.id, 
            {
                "schedule_id": schedule_id,
                "scheduled_at": scheduled_date.isoformat(),
                "reason": "temporary_prescription",
                "status": "scheduled"
            },
            tenant_id,
            correlation_id=schedule_id
        )
        
        print(f"✅ Created scheduled revocation: {med['name']} scheduled for {scheduled_date.date()}")
    
    return created_by_state


def get_demo_stats(session: Session, tenant_id: str = "default") -> Dict[str, Any]:
    """Get statistics about demo data.
    
    Args:
        session: Database session
        tenant_id: Tenant identifier
        
    Returns:
        Dict with statistics
    """
    stats = {
        "users": {
            "doctors": session.query(User).filter_by(role="doctor", tenant_id=tenant_id).count(),
            "patients": session.query(User).filter_by(role="patient", tenant_id=tenant_id).count(),
            "pharmacists": session.query(User).filter_by(role="pharmacist", tenant_id=tenant_id).count(),
            "total": session.query(User).filter_by(tenant_id=tenant_id).count(),
        },
        "prescriptions": {
            "total": session.query(Prescription).filter_by(tenant_id=tenant_id).count(),
            "draft": session.query(Prescription).filter_by(status="DRAFT", tenant_id=tenant_id).count(),
            "active": session.query(Prescription).filter_by(status="ACTIVE", tenant_id=tenant_id).count(),
            "expired": session.query(Prescription).filter_by(status="EXPIRED", tenant_id=tenant_id).count(),
            "revoked": session.query(Prescription).filter_by(status="REVOKED", tenant_id=tenant_id).count(),
            "dispensed": session.query(Prescription).filter_by(status="DISPENSED", tenant_id=tenant_id).count(),
        },
        "dispensings": session.query(Dispensing).filter_by(tenant_id=tenant_id).count(),
        "audit_logs": session.query(Audit).filter_by(tenant_id=tenant_id).count(),
    }
    return stats


def print_summary(stats: Dict[str, Any]) -> None:
    """Print a formatted summary of demo data.
    
    Args:
        stats: Statistics dictionary from get_demo_stats
    """
    print("\n" + "=" * 70)
    print("✅ DEMO DATA SEEDED SUCCESSFULLY")
    print("=" * 70)
    
    print("\n📊 USER COUNTS:")
    print(f"   Doctors:      {stats['users']['doctors']}")
    print(f"   Patients:     {stats['users']['patients']}")
    print(f"   Pharmacists:  {stats['users']['pharmacists']}")
    print(f"   Total Users:  {stats['users']['total']}")
    
    print("\n📋 PRESCRIPTION COUNTS:")
    print(f"   Total:        {stats['prescriptions']['total']}")
    print(f"   DRAFT:        {stats['prescriptions']['draft']}")
    print(f"   ACTIVE:       {stats['prescriptions']['active']}")
    print(f"   EXPIRED:      {stats['prescriptions']['expired']}")
    print(f"   REVOKED:      {stats['prescriptions']['revoked']}")
    print(f"   DISPENSED:    {stats['prescriptions']['dispensed']}")
    
    print(f"\n💊 DISPENSING RECORDS: {stats['dispensings']}")
    print(f"📜 AUDIT LOG ENTRIES:  {stats['audit_logs']}")
    
    print("\n" + "-" * 70)
    print("🎭 DEMO SCENARIOS AVAILABLE:")
    print("-" * 70)
    
    for scenario in DEMO_SCENARIOS:
        print(f"\n   Scenario {scenario['id']}: {scenario['name']}")
        print(f"   {'─' * 60}")
        print(f"   {scenario['description']}")
    
    print("\n" + "=" * 70)
    print("💡 CREDENTIALS:")
    print("   All users have password: Demo@2024")
    print("\n   Example logins:")
    print("   • Doctor:     sarah.johnson@hospital.co.za")
    print("   • Patient:    john.smith@example.com")
    print("   • Pharmacist: lisa.chen@pharmacy.co.za")
    print("=" * 70 + "\n")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for seed script."""
    parser = argparse.ArgumentParser(
        description="Seed demo data for digital prescription system (US-019)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed_demo_data.py                           # Use defaults
  python scripts/seed_demo_data.py --doctors 5 --patients 10 # Custom counts
  python scripts/seed_demo_data.py --reset                   # Clear and reseed

This script creates:
  - 5+ doctors with HPCSA registration numbers
  - 10+ patients with mock ID numbers
  - 3+ pharmacists with SAPC registration numbers
  - 30 prescriptions in various states (DRAFT, ACTIVE, EXPIRED, REVOKED, DISPENSED)
  - Audit trail entries for all prescription lifecycle events
  - Dispensing records for dispensed prescriptions
  - FHIR R4 compatible metadata
  - Scheduled revocation examples
        """,
    )
    
    parser.add_argument(
        "--doctors",
        type=int,
        default=5,
        help="Number of doctors to create (default: 5)",
    )
    parser.add_argument(
        "--patients",
        type=int,
        default=10,
        help="Number of patients to create (default: 10)",
    )
    parser.add_argument(
        "--pharmacists",
        type=int,
        default=3,
        help="Number of pharmacists to create (default: 3)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database URL (default: from DATABASE_URL env var or sqlite:///./test.db)",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="default",
        help="Tenant ID for multi-tenancy (default: default)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all demo data before seeding (WARNING: deletes existing data)",
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or get_database_url()
    print(f"📦 Seeding demo data...")
    print(f"📊 Database: {database_url}")
    print(f"🏢 Tenant: {args.tenant_id}")
    print()
    
    try:
        # Create engine and session
        engine, SessionLocal = create_session(database_url)
        session = SessionLocal()
        
        try:
            # Handle reset if requested
            if args.reset:
                print("⚠️  Reset requested - clearing existing demo data...")
                # Only delete demo data, not the tenant
                session.query(Dispensing).filter_by(tenant_id=args.tenant_id).delete()
                session.query(Audit).filter_by(tenant_id=args.tenant_id).delete()
                session.query(Prescription).filter_by(tenant_id=args.tenant_id).delete()
                session.query(User).filter_by(tenant_id=args.tenant_id).delete()
                session.commit()
                print("✅ Existing demo data cleared\n")
            
            # Ensure default tenant exists
            ensure_default_tenant(session)
            
            print("👥 Creating doctors...")
            doctors = seed_doctors(session, args.doctors, args.tenant_id)
            print(f"   Created: {len(doctors)} doctors\n")
            
            print("👨‍🦱 Creating patients...")
            patients = seed_patients(session, args.patients, args.tenant_id)
            print(f"   Created: {len(patients)} patients\n")
            
            print("💊 Creating pharmacists...")
            pharmacists = seed_pharmacists(session, args.pharmacists, args.tenant_id)
            print(f"   Created: {len(pharmacists)} pharmacists\n")
            
            # Only create prescriptions if we have users
            if doctors and patients and pharmacists:
                print("📋 Creating prescriptions with full audit trails...")
                prescriptions_by_state = seed_prescriptions_with_states(
                    session, doctors, patients, pharmacists, args.tenant_id
                )
                total_rx = sum(len(rx_list) for rx_list in prescriptions_by_state.values())
                print(f"   Created: {total_rx} prescriptions\n")
            else:
                print("⚠️  Cannot create prescriptions - missing doctors, patients, or pharmacists\n")
            
            # Commit all changes
            session.commit()
            
            # Get and print statistics
            stats = get_demo_stats(session, args.tenant_id)
            print_summary(stats)
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error seeding data: {e}", file=sys.stderr)
            raise
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Failed to seed database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
