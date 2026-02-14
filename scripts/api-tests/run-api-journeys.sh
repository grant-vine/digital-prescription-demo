#!/bin/bash
# API Journey Tests - Digital Prescription Demo
# Tests the core API flows independently of mobile app
# Usage: ./scripts/api-tests/run-api-journeys.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000/api/v1"
DOCTOR_EMAIL="sarah.johnson@hospital.co.za"
DOCTOR_PASSWORD="Demo@2024"
PATIENT_EMAIL="john.smith@example.com"
PATIENT_PASSWORD="Demo@2024"
PHARMACIST_EMAIL="lisa.chen@pharmacy.co.za"
PHARMACIST_PASSWORD="Demo@2024"

# Storage for tokens
DOCTOR_TOKEN=""
PATIENT_TOKEN=""
PHARMACIST_TOKEN=""
PRESCRIPTION_ID=""

echo "=========================================="
echo "Digital Prescription API Journey Tests"
echo "=========================================="
echo ""

# Helper function for API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    local description=$5
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "  $method $endpoint"
    
    local curl_cmd="curl -s -w '\nHTTP_CODE:%{http_code}' -X $method \"${API_BASE}${endpoint}\""
    
    if [ -n "$token" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $token\""
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    
    local response=$(eval $curl_cmd)
    local http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d':' -f2)
    local body=$(echo "$response" | grep -v "HTTP_CODE:")
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo "$body"
        return 1
    fi
}

# ============================================
# JOURNEY 1: Health Check
# ============================================
echo ""
echo "JOURNEY 1: System Health Check"
echo "--------------------------------"
api_call "GET" "/prescriptions?page=1&page_size=1" "" "" "List prescriptions (public endpoint)"

# ============================================
# JOURNEY 2: Doctor Authentication Flow
# ============================================
echo ""
echo "JOURNEY 2: Doctor Authentication"
echo "--------------------------------"

# Doctor login
login_response=$(curl -s -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${DOCTOR_EMAIL}\",\"password\":\"${DOCTOR_PASSWORD}\"}")

if echo "$login_response" | grep -q "access_token"; then
    DOCTOR_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Doctor login successful${NC}"
    echo "  Token: ${DOCTOR_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Doctor login failed${NC}"
    echo "$login_response"
    exit 1
fi

# Validate token
api_call "GET" "/auth/validate" "" "$DOCTOR_TOKEN" "Validate doctor token"

# ============================================
# JOURNEY 3: Patient Authentication Flow
# ============================================
echo ""
echo "JOURNEY 3: Patient Authentication"
echo "----------------------------------"

login_response=$(curl -s -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${PATIENT_EMAIL}\",\"password\":\"${PATIENT_PASSWORD}\"}")

if echo "$login_response" | grep -q "access_token"; then
    PATIENT_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Patient login successful${NC}"
    echo "  Token: ${PATIENT_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Patient login failed${NC}"
    echo "$login_response"
    exit 1
fi

# ============================================
# JOURNEY 4: Pharmacist Authentication Flow
# ============================================
echo ""
echo "JOURNEY 4: Pharmacist Authentication"
echo "-------------------------------------"

login_response=$(curl -s -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${PHARMACIST_EMAIL}\",\"password\":\"${PHARMACIST_PASSWORD}\"}")

if echo "$login_response" | grep -q "access_token"; then
    PHARMACIST_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Pharmacist login successful${NC}"
    echo "  Token: ${PHARMACIST_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Pharmacist login failed${NC}"
    echo "$login_response"
    exit 1
fi

# ============================================
# JOURNEY 5: Doctor - Create Prescription
# ============================================
echo ""
echo "JOURNEY 5: Create Prescription (Doctor)"
echo "----------------------------------------"

# Create a prescription
prescription_data='{
    "patient_id": 2,
    "medication_name": "Amoxicillin",
    "medication_code": "AMOX500",
    "dosage": "500mg",
    "quantity": 21,
    "instructions": "Take 1 tablet 3 times daily for 7 days",
    "date_expires": "2026-03-14",
    "is_repeat": false,
    "repeat_count": 0
}'

create_response=$(curl -s -X POST "${API_BASE}/prescriptions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $DOCTOR_TOKEN" \
    -d "$prescription_data")

if echo "$create_response" | grep -q '"id"'; then
    PRESCRIPTION_ID=$(echo "$create_response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo -e "${GREEN}✓ Prescription created successfully${NC}"
    echo "  Prescription ID: $PRESCRIPTION_ID"
else
    echo -e "${RED}✗ Prescription creation failed${NC}"
    echo "$create_response"
    exit 1
fi

# Get prescription details
api_call "GET" "/prescriptions/${PRESCRIPTION_ID}" "" "$DOCTOR_TOKEN" "Get prescription details"

# Sign prescription
api_call "POST" "/prescriptions/${PRESCRIPTION_ID}/sign" '{}' "$DOCTOR_TOKEN" "Sign prescription"

# Generate QR code
api_call "GET" "/prescriptions/${PRESCRIPTION_ID}/qr" "" "$DOCTOR_TOKEN" "Generate QR code for prescription"

# ============================================
# JOURNEY 6: Patient - Wallet Operations
# ============================================
echo ""
echo "JOURNEY 6: Patient Wallet Operations"
echo "-------------------------------------"

# Setup wallet
api_call "POST" "/wallet/setup" '{}' "$PATIENT_TOKEN" "Setup patient wallet"

# Get wallet status
api_call "GET" "/wallet/status" "" "$PATIENT_TOKEN" "Get wallet status"

# ============================================
# JOURNEY 7: Pharmacist - Verify Operations
# ============================================
echo ""
echo "JOURNEY 7: Pharmacist Verification"
echo "-----------------------------------"

# Verify prescription (mock QR data)
verify_data='{
    "prescription_id": "'"$PRESCRIPTION_ID"'",
    "signature": "mock_signature_for_testing"
}'

api_call "POST" "/verify/prescription" "$verify_data" "$PHARMACIST_TOKEN" "Verify prescription"

# Check trust registry
api_call "POST" "/verify/trust-registry" '{"issuer_did": "did:web:example.com"}' "$PHARMACIST_TOKEN" "Check trust registry"

# ============================================
# JOURNEY 8: Audit & Reporting
# ============================================
echo ""
echo "JOURNEY 8: Audit & Reporting"
echo "-----------------------------"

# List audit events (admin endpoint)
# Note: This might fail if doctor doesn't have admin rights, which is expected
api_call "GET" "/admin/audit/events?page=1&page_size=10" "" "$DOCTOR_TOKEN" "List audit events (admin)" || true

# Get compliance dashboard (admin endpoint)
api_call "GET" "/admin/dashboard/compliance" "" "$DOCTOR_TOKEN" "Get compliance dashboard (admin)" || true

# ============================================
# JOURNEY 9: Search Operations
# ============================================
echo ""
echo "JOURNEY 9: Search Operations"
echo "-----------------------------"

# Search patients
api_call "GET" "/patients/search?q=john" "" "$DOCTOR_TOKEN" "Search patients"

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "API Journey Tests Complete"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - All authentication flows: ✓ Working"
echo "  - Prescription creation: ✓ Working"
echo "  - Prescription signing: ✓ Working"
echo "  - QR generation: ✓ Working"
echo "  - Wallet operations: ✓ Working"
echo "  - Verification operations: ✓ Working"
echo ""
echo "All API routes verified to use /api/v1 prefix"
echo ""
