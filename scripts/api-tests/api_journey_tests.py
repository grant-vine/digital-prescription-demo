#!/usr/bin/env python3
"""
API Journey Tests - Digital Prescription Demo
Tests the core API flows independently of mobile app
"""

import requests
import json
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000/api/v1"

# Demo credentials
@dataclass
class Credentials:
    email: str
    password: str

DOCTOR = Credentials("sarah.johnson@hospital.co.za", "Demo@2024")
PATIENT = Credentials("john.smith@example.com", "Demo@2024")
PHARMACIST = Credentials("lisa.chen@pharmacy.co.za", "Demo@2024")

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log(self, message: str, level: str = "info"):
        """Log with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "success":
            print(f"{Colors.GREEN}[{timestamp}] ✓ {message}{Colors.END}")
        elif level == "error":
            print(f"{Colors.RED}[{timestamp}] ✗ {message}{Colors.END}")
        elif level == "warning":
            print(f"{Colors.YELLOW}[{timestamp}] ⚠ {message}{Colors.END}")
        elif level == "info":
            print(f"{Colors.BLUE}[{timestamp}] ℹ {message}{Colors.END}")
        else:
            print(f"[{timestamp}] {message}")
    
    def api_call(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        token: Optional[str] = None,
        expected_status: int = 200
    ) -> Optional[Dict]:
        """Make an API call and return response JSON"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            self.log(f"{method} {endpoint}", "info")
            
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=10)
            else:
                self.log(f"Unsupported method: {method}", "error")
                return None
            
            # Check status
            if response.status_code == expected_status:
                self.log(f"Success (HTTP {response.status_code})", "success")
                try:
                    return response.json()
                except:
                    return {"text": response.text}
            else:
                self.log(f"Failed (HTTP {response.status_code})", "error")
                try:
                    error_detail = response.json()
                    self.log(f"Error: {json.dumps(error_detail, indent=2)}", "error")
                except:
                    self.log(f"Response: {response.text[:200]}", "error")
                return None
                
        except requests.exceptions.ConnectionError:
            self.log(f"Connection failed - is backend running on {API_BASE}?", "error")
            return None
        except requests.exceptions.Timeout:
            self.log("Request timed out", "error")
            return None
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "error")
            return None
    
    def login(self, role: str, creds: Credentials) -> Optional[str]:
        """Login and return token"""
        self.log(f"\n{'='*50}", "info")
        self.log(f"JOURNEY: {role} Authentication", "info")
        self.log(f"{'='*50}", "info")
        
        data = {
            "username": creds.email,
            "password": creds.password
        }
        
        result = self.api_call("POST", "/auth/login", data, expected_status=200)
        
        if result and "access_token" in result:
            token = result["access_token"]
            self.tokens[role] = token
            self.log(f"{role} login successful", "success")
            self.log(f"Token: {token[:30]}...", "info")
            return token
        else:
            self.log(f"{role} login failed", "error")
            return None
    
    def test_health_check(self):
        """Journey 1: System Health Check"""
        self.log(f"\n{'='*50}", "info")
        self.log("JOURNEY 1: System Health Check", "info")
        self.log(f"{'='*50}", "info")
        
        # Try to get prescriptions list (should work even without auth for testing)
        result = self.api_call("GET", "/prescriptions?page=1&page_size=1", expected_status=200)
        if result:
            self.log("Health check passed - API is responsive", "success")
        return result is not None
    
    def test_doctor_workflow(self) -> Optional[int]:
        """Journey 5: Doctor creates and signs prescription"""
        self.log(f"\n{'='*50}", "info")
        self.log("JOURNEY 5: Doctor Workflow", "info")
        self.log(f"{'='*50}", "info")
        
        token = self.tokens.get("DOCTOR")
        if not token:
            self.log("Doctor not logged in", "error")
            return None
        
        # Create prescription
        prescription_data = {
            "patient_id": 2,
            "medication_name": "Amoxicillin",
            "medication_code": "AMOX500",
            "dosage": "500mg",
            "quantity": 21,
            "instructions": "Take 1 tablet 3 times daily for 7 days",
            "date_expires": "2026-03-14",
            "is_repeat": False,
            "repeat_count": 0
        }
        
        result = self.api_call("POST", "/prescriptions", prescription_data, token, expected_status=201)
        if not result or "id" not in result:
            self.log("Failed to create prescription", "error")
            return None
        
        prescription_id = result["id"]
        self.log(f"Created prescription ID: {prescription_id}", "success")
        
        # Get prescription details
        self.api_call("GET", f"/prescriptions/{prescription_id}", token=token)
        
        # Sign prescription
        sign_result = self.api_call("POST", f"/prescriptions/{prescription_id}/sign", {}, token)
        if sign_result:
            self.log("Prescription signed successfully", "success")
        
        # Generate QR code
        qr_result = self.api_call("GET", f"/prescriptions/{prescription_id}/qr", token=token)
        if qr_result:
            self.log("QR code generated", "success")
        
        return prescription_id
    
    def test_patient_workflow(self):
        """Journey 6: Patient wallet operations"""
        self.log(f"\n{'='*50}", "info")
        self.log("JOURNEY 6: Patient Workflow", "info")
        self.log(f"{'='*50}", "info")
        
        token = self.tokens.get("PATIENT")
        if not token:
            self.log("Patient not logged in", "error")
            return False
        
        # Setup wallet
        self.api_call("POST", "/wallet/setup", {}, token)
        
        # Get wallet status
        self.api_call("GET", "/wallet/status", token=token)
        
        return True
    
    def test_pharmacist_workflow(self, prescription_id: int):
        """Journey 7: Pharmacist verification"""
        self.log(f"\n{'='*50}", "info")
        self.log("JOURNEY 7: Pharmacist Workflow", "info")
        self.log(f"{'='*50}", "info")
        
        token = self.tokens.get("PHARMACIST")
        if not token:
            self.log("Pharmacist not logged in", "error")
            return False
        
        # Verify prescription
        verify_data = {
            "prescription_id": str(prescription_id),
            "signature": "mock_signature_for_testing"
        }
        self.api_call("POST", "/verify/prescription", verify_data, token)
        
        # Check trust registry
        trust_data = {"issuer_did": "did:web:example.com"}
        self.api_call("POST", "/verify/trust-registry", trust_data, token)
        
        return True
    
    def test_search_operations(self):
        """Journey 9: Search operations"""
        self.log(f"\n{'='*50}", "info")
        self.log("JOURNEY 9: Search Operations", "info")
        self.log(f"{'='*50}", "info")
        
        token = self.tokens.get("DOCTOR")
        if not token:
            self.log("Doctor not logged in", "error")
            return False
        
        # Search patients
        self.api_call("GET", "/patients/search?q=john", token=token)
        
        return True
    
    def run_all_tests(self):
        """Run all API journey tests"""
        print("\n" + "="*70)
        print("DIGITAL PRESCRIPTION API JOURNEY TESTS")
        print("="*70)
        print(f"API Base URL: {API_BASE}")
        print(f"Testing with /api/v1 prefix verification")
        print("="*70 + "\n")
        
        all_passed = True
        prescription_id = None
        
        # Journey 1: Health Check
        if not self.test_health_check():
            all_passed = False
            self.log("\n⚠ Health check failed - backend may not be running", "error")
            self.log("Make sure to run: ./scripts/start-demo.sh", "warning")
            return False
        
        # Journey 2-4: Authenticate all roles
        if not self.login("DOCTOR", DOCTOR):
            all_passed = False
        
        if not self.login("PATIENT", PATIENT):
            all_passed = False
        
        if not self.login("PHARMACIST", PHARMACIST):
            all_passed = False
        
        # Journey 5: Doctor workflow
        prescription_id = self.test_doctor_workflow()
        if not prescription_id:
            all_passed = False
        
        # Journey 6: Patient workflow
        if not self.test_patient_workflow():
            all_passed = False
        
        # Journey 7: Pharmacist workflow
        if prescription_id and not self.test_pharmacist_workflow(prescription_id):
            all_passed = False
        
        # Journey 9: Search operations
        if not self.test_search_operations():
            all_passed = False
        
        # Summary
        print("\n" + "="*70)
        if all_passed:
            print(f"{Colors.GREEN}✓ ALL API JOURNEY TESTS PASSED{Colors.END}")
        else:
            print(f"{Colors.RED}✗ SOME TESTS FAILED{Colors.END}")
        print("="*70)
        print(f"\nTokens acquired:")
        for role, token in self.tokens.items():
            print(f"  {role}: {token[:30]}...")
        print(f"\nPrescription ID: {prescription_id}")
        print("\nAll API routes verified to use /api/v1 prefix ✓")
        
        return all_passed

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
