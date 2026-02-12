#!/usr/bin/env python3
"""Demo data seed script for digital prescription system.

Populates the database with realistic test data for doctors, patients, 
pharmacists, and prescriptions. Idempotent - can run multiple times safely.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --doctors 5 --patients 10 --pharmacists 3 --prescriptions 20

Environment:
    DATABASE_URL: Database connection string (default: sqlite:///./test.db)
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
import uuid
from pathlib import Path
from typing import List, Tuple, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.user import User
from app.models.prescription import Prescription
from app.core.security import hash_password


# Test data definitions
DEMO_DOCTORS = [
    {
        "email": "sarah.johnson@hospital.co.za",
        "full_name": "Dr. Sarah Johnson",
        "registration_number": "MP1234567",
        "password": "Demo@2024",
    },
    {
        "email": "thabo.mokoena@clinic.co.za",
        "full_name": "Dr. Thabo Mokoena",
        "registration_number": "MP2345678",
        "password": "Demo@2024",
    },
    {
        "email": "ayesha.patel@pediatrics.co.za",
        "full_name": "Dr. Ayesha Patel",
        "registration_number": "MP3456789",
        "password": "Demo@2024",
    },
]

DEMO_PATIENTS = [
    {
        "email": "john.smith@example.com",
        "full_name": "John Smith",
        "password": "Demo@2024",
    },
    {
        "email": "mary.williams@example.com",
        "full_name": "Mary Williams",
        "password": "Demo@2024",
    },
    {
        "email": "sipho.dlamini@example.com",
        "full_name": "Sipho Dlamini",
        "password": "Demo@2024",
    },
    {
        "email": "fatima.hassan@example.com",
        "full_name": "Fatima Hassan",
        "password": "Demo@2024",
    },
    {
        "email": "james.brown@example.com",
        "full_name": "James Brown",
        "password": "Demo@2024",
    },
]

DEMO_PHARMACISTS = [
    {
        "email": "lisa.chen@pharmacy.co.za",
        "full_name": "Lisa Chen",
        "registration_number": "P123456",
        "password": "Demo@2024",
    },
    {
        "email": "david.nkosi@hospital.co.za",
        "full_name": "David Nkosi",
        "registration_number": "P234567",
        "password": "Demo@2024",
    },
]

MEDICATIONS = [
    {"name": "Amoxicillin", "dosage": "500mg", "quantity": 21},
    {"name": "Metformin", "dosage": "850mg", "quantity": 60},
    {"name": "Lisinopril", "dosage": "10mg", "quantity": 30},
    {"name": "Atorvastatin", "dosage": "20mg", "quantity": 30},
    {"name": "Omeprazole", "dosage": "20mg", "quantity": 30},
    {"name": "Paracetamol", "dosage": "500mg", "quantity": 12},
    {"name": "Ibuprofen", "dosage": "400mg", "quantity": 20},
    {"name": "Fluconazole", "dosage": "150mg", "quantity": 2},
]


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


def user_exists(session: Session, email: str) -> bool:
    """Check if a user with given email already exists."""
    return session.query(User).filter_by(email=email).first() is not None


def seed_doctors(session: Session, count: int = 3) -> List[User]:
    """Create test doctors in database.
    
    Args:
        session: Database session
        count: Number of doctors to create (uses first N from DEMO_DOCTORS)
        
    Returns:
        List of created User objects
    """
    created = []
    doctors_to_create = DEMO_DOCTORS[:count] if count < len(DEMO_DOCTORS) else DEMO_DOCTORS
    
    for doctor_data in doctors_to_create:
        if user_exists(session, doctor_data["email"]):
            print(f"⏭️  Doctor '{doctor_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                email=doctor_data["email"],
                full_name=doctor_data["full_name"],
                password_hash=hash_password(doctor_data["password"]),
                role="doctor",
                registration_number=doctor_data["registration_number"],
                did=generate_mock_did(),
            )
            session.add(user)
            session.flush()  # Flush to get the ID
            created.append(user)
            print(f"✅ Created doctor: {doctor_data['full_name']} ({doctor_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating doctor '{doctor_data['email']}': {e}")
    
    return created


def seed_patients(session: Session, count: int = 5) -> List[User]:
    """Create test patients in database.
    
    Args:
        session: Database session
        count: Number of patients to create (uses first N from DEMO_PATIENTS)
        
    Returns:
        List of created User objects
    """
    created = []
    patients_to_create = DEMO_PATIENTS[:count] if count < len(DEMO_PATIENTS) else DEMO_PATIENTS
    
    for patient_data in patients_to_create:
        if user_exists(session, patient_data["email"]):
            print(f"⏭️  Patient '{patient_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                email=patient_data["email"],
                full_name=patient_data["full_name"],
                password_hash=hash_password(patient_data["password"]),
                role="patient",
                registration_number=None,
                did=generate_mock_did(),
            )
            session.add(user)
            session.flush()
            created.append(user)
            print(f"✅ Created patient: {patient_data['full_name']} ({patient_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating patient '{patient_data['email']}': {e}")
    
    return created


def seed_pharmacists(session: Session, count: int = 2) -> List[User]:
    """Create test pharmacists in database.
    
    Args:
        session: Database session
        count: Number of pharmacists to create (uses first N from DEMO_PHARMACISTS)
        
    Returns:
        List of created User objects
    """
    created = []
    pharmacists_to_create = DEMO_PHARMACISTS[:count] if count < len(DEMO_PHARMACISTS) else DEMO_PHARMACISTS
    
    for pharmacist_data in pharmacists_to_create:
        if user_exists(session, pharmacist_data["email"]):
            print(f"⏭️  Pharmacist '{pharmacist_data['email']}' already exists - skipping")
            continue
        
        try:
            user = User(
                email=pharmacist_data["email"],
                full_name=pharmacist_data["full_name"],
                password_hash=hash_password(pharmacist_data["password"]),
                role="pharmacist",
                registration_number=pharmacist_data["registration_number"],
                did=generate_mock_did(),
            )
            session.add(user)
            session.flush()
            created.append(user)
            print(f"✅ Created pharmacist: {pharmacist_data['full_name']} ({pharmacist_data['email']})")
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  Error creating pharmacist '{pharmacist_data['email']}': {e}")
    
    return created


def seed_prescriptions(session: Session, count: int = 10) -> List[Prescription]:
    """Create test prescriptions linking doctors to patients.
    
    Args:
        session: Database session
        count: Number of prescriptions to create
        
    Returns:
        List of created Prescription objects
    """
    # Get all doctors and patients
    doctors = session.query(User).filter_by(role="doctor").all()
    patients = session.query(User).filter_by(role="patient").all()
    
    if not doctors or not patients:
        print("⚠️  No doctors or patients found - cannot create prescriptions")
        return []
    
    created = []
    statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "DISPENSED", "DISPENSED", "EXPIRED", "REVOKED"]
    
    for i in range(count):
        doctor = doctors[i % len(doctors)]
        patient = patients[i % len(patients)]
        medication = MEDICATIONS[i % len(MEDICATIONS)]
        status = statuses[i % len(statuses)]
        
        # Generate dates
        today = datetime.utcnow()
        date_issued = today - timedelta(days=(i % 7))  # Issued in past 7 days
        
        # Expiry: 30-90 days in future, or in past if EXPIRED
        if status == "EXPIRED":
            date_expires = today - timedelta(days=30)
        else:
            date_expires = today + timedelta(days=30 + (i % 60))
        
        try:
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=doctor.id,
                medication_name=medication["name"],
                medication_code=f"MED_{i:04d}",
                dosage=medication["dosage"],
                quantity=medication["quantity"],
                instructions=f"Take as directed. Standard course of treatment.",
                date_issued=date_issued,
                date_expires=date_expires,
                is_repeat=(i % 3 == 0),  # Every 3rd prescription is a repeat
                repeat_count=(2 if (i % 3 == 0) else 0),
                status=status,
                digital_signature=f"sig_{uuid.uuid4().hex[:16]}",
                credential_id=f"cred_{uuid.uuid4().hex[:16]}",
            )
            session.add(prescription)
            session.flush()
            created.append(prescription)
            print(f"✅ Created prescription: {medication['name']} for {patient.full_name} by {doctor.full_name} (Status: {status})")
        except Exception as e:
            session.rollback()
            print(f"⚠️  Error creating prescription: {e}")
    
    return created


def main():
    """Main entry point for seed script."""
    parser = argparse.ArgumentParser(
        description="Seed demo data for digital prescription system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed_demo_data.py                           # Use defaults (3 doctors, 5 patients, 2 pharmacists, 10 prescriptions)
  python scripts/seed_demo_data.py --doctors 5 --patients 10 # Custom counts
  python scripts/seed_demo_data.py --prescriptions 20        # Create more prescriptions
        """,
    )
    
    parser.add_argument(
        "--doctors",
        type=int,
        default=3,
        help="Number of doctors to create (default: 3)",
    )
    parser.add_argument(
        "--patients",
        type=int,
        default=5,
        help="Number of patients to create (default: 5)",
    )
    parser.add_argument(
        "--pharmacists",
        type=int,
        default=2,
        help="Number of pharmacists to create (default: 2)",
    )
    parser.add_argument(
        "--prescriptions",
        type=int,
        default=10,
        help="Number of prescriptions to create (default: 10)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database URL (default: from DATABASE_URL env var or sqlite:///./test.db)",
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or get_database_url()
    print(f"📦 Seeding demo data...")
    print(f"📊 Database: {database_url}")
    print()
    
    try:
        # Create engine and session
        engine, SessionLocal = create_session(database_url)
        session = SessionLocal()
        
        try:
            print("👥 Creating doctors...")
            doctors = seed_doctors(session, args.doctors)
            print(f"   Created: {len(doctors)} doctors\n")
            
            print("👨‍🦱 Creating patients...")
            patients = seed_patients(session, args.patients)
            print(f"   Created: {len(patients)} patients\n")
            
            print("💊 Creating pharmacists...")
            pharmacists = seed_pharmacists(session, args.pharmacists)
            print(f"   Created: {len(pharmacists)} pharmacists\n")
            
            print("📋 Creating prescriptions...")
            prescriptions = seed_prescriptions(session, args.prescriptions)
            print(f"   Created: {len(prescriptions)} prescriptions\n")
            
            # Commit all changes
            session.commit()
            
            # Print summary
            print("=" * 60)
            print("✅ DEMO DATA SEEDED SUCCESSFULLY")
            print("=" * 60)
            print(f"Doctors:       {len(doctors)} created")
            print(f"Patients:      {len(patients)} created")
            print(f"Pharmacists:   {len(pharmacists)} created")
            print(f"Prescriptions: {len(prescriptions)} created")
            print()
            print("💡 You can now run the app and test with this demo data!")
            print("   Demo password for all users: Demo@2024")
            print()
            
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
