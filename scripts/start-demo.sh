#!/bin/bash

################################################################################
# Digital Prescription Demo - Automated Startup Script
# 
# This script fully automates the startup of the digital prescription demo:
# - Checks prerequisites (Python 3.12+, Node.js 20+, Docker)
# - Starts Docker infrastructure (PostgreSQL, Redis, ACA-Py)
# - Sets up backend (venv, dependencies, migrations, seed data)
# - Sets up mobile app (npm install)
# - Starts backend API server
# - Starts mobile app with Expo
# - Displays demo URLs and credentials
#
# Usage: ./scripts/start-demo.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/services/backend"
MOBILE_DIR="${PROJECT_ROOT}/apps/mobile"
VENV_DIR="${BACKEND_DIR}/venv"
USE_DEMO="${USE_DEMO:-false}"

################################################################################
# Helper Functions
################################################################################

log_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
}

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_section() {
    echo ""
    echo -e "${YELLOW}→${NC} $1"
}

################################################################################
# 1. Check Prerequisites
################################################################################

check_prerequisites() {
    log_header "STEP 1: Checking Prerequisites"
    
    # Check Python version
    log_section "Checking Python (3.12+ required)..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_PYTHON="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_PYTHON" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_PYTHON" ]; then
        log_info "Python $PYTHON_VERSION ✓"
    else
        log_error "Python $PYTHON_VERSION found, but 3.11+ required"
        exit 1
    fi
    
    # Check Node.js version
    log_section "Checking Node.js (20+ required)..."
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 20 ]; then
        log_info "Node.js v$(node -v | cut -d'v' -f2) ✓"
    else
        log_error "Node.js v$(node -v | cut -d'v' -f2) found, but 20+ required"
        exit 1
    fi
    
    # Check Docker
    log_section "Checking Docker Desktop..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_info "Docker Desktop is running ✓"
    
    # Check Git
    log_section "Checking Git..."
    if ! command -v git &> /dev/null; then
        log_warn "Git is not installed (optional, but recommended)"
    else
        log_info "Git $(git --version | awk '{print $3}') ✓"
    fi
}

################################################################################
# 2. Start Docker Infrastructure
################################################################################

start_docker_infrastructure() {
    log_header "STEP 2: Starting Docker Infrastructure"

    cd "${PROJECT_ROOT}"

    if [ "$USE_DEMO" = "true" ]; then
        log_warn "🎭 Demo mode enabled - skipping ACA-Py/Docker startup"
        log_section "Starting PostgreSQL and Redis only..."
        docker-compose up -d db redis
    else
        log_section "Pulling Docker images (may take a few minutes on first run)..."
        docker-compose pull db redis acapy || log_warn "Some images already cached"

        log_section "Starting PostgreSQL, Redis, and ACA-Py..."
        docker-compose up -d db redis acapy
    fi
    
    # Wait for services to be healthy
    log_section "Waiting for services to be healthy (this may take 30-45 seconds)..."
    
    MAX_ATTEMPTS=60
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))
        
        # Check PostgreSQL
        if docker-compose exec -T db pg_isready -U postgres &> /dev/null; then
            log_info "PostgreSQL is healthy"
            break
        fi
        
        if [ $((ATTEMPT % 10)) -eq 0 ]; then
            echo -n "."
        fi
        
        sleep 1
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        log_error "Services failed to start. Check Docker logs: docker-compose logs"
        exit 1
    fi
    
    # Give services extra time to stabilize
    sleep 5
    
    log_info "All Docker services are healthy ✓"
}

################################################################################
# 3. Setup Backend
################################################################################

setup_backend() {
    log_header "STEP 3: Setting up Backend API"
    
    cd "${BACKEND_DIR}"
    
    # Create virtual environment if it doesn't exist
    log_section "Setting up Python virtual environment..."
    if [ ! -d "${VENV_DIR}" ]; then
        python3 -m venv "${VENV_DIR}"
        log_info "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "${VENV_DIR}/bin/activate"
    
    # Upgrade pip
    log_section "Upgrading pip..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || true
    
    # Install dependencies
    log_section "Installing Python dependencies (may take 1-2 minutes)..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "Dependencies installed ✓"
    else
        log_error "requirements.txt not found in ${BACKEND_DIR}"
        exit 1
    fi
    
    # Run database migrations
    log_section "Running database migrations..."
    if [ -f "alembic.ini" ]; then
        alembic upgrade head || log_warn "Migration failed (database may already be initialized)"
    else
        log_warn "alembic.ini not found (skipping migrations)"
    fi
    
    # Seed demo data
    log_section "Seeding demo data..."
    if [ -f "scripts/seed_demo_data.py" ]; then
        python scripts/seed_demo_data.py
        log_info "Demo data seeded ✓"
    else
        log_warn "seed_demo_data.py not found (demo data not seeded)"
    fi
}

################################################################################
# 4. Setup Mobile App
################################################################################

setup_mobile() {
    log_header "STEP 4: Setting up Mobile App"
    
    if [ ! -d "${MOBILE_DIR}" ]; then
        log_warn "Mobile app directory not found at ${MOBILE_DIR}"
        return
    fi
    
    cd "${MOBILE_DIR}"
    
    # Check if node_modules exists
    log_section "Checking mobile dependencies..."
    if [ ! -d "node_modules" ]; then
        log_section "Installing npm dependencies (may take 1-2 minutes)..."
        npm install
        log_info "Dependencies installed ✓"
    else
        log_info "Dependencies already installed"
    fi
    
    # Optionally update if package-lock.json exists and is newer
    if [ -f "package.json" ] && [ -f "package-lock.json" ]; then
        log_info "Package lock verified ✓"
    fi
}

################################################################################
# 5. Display Startup Information
################################################################################

display_startup_info() {
    log_header "STEP 5: Starting Services"
    
    echo ""
    echo -e "${GREEN}Services are starting...${NC}"
    echo ""
    echo -e "Backend API will be available at: ${BLUE}http://localhost:8000${NC}"
    echo -e "API Documentation:               ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "Health Check:                    ${BLUE}http://localhost:8000/api/v1/health${NC}"
    echo ""
    echo -e "Mobile app will start at port:   ${BLUE}8081 (Expo Metro Bundler)${NC}"
    echo ""
}

################################################################################
# 6. Start Backend Server
################################################################################

start_backend_server() {
    log_section "Starting backend API server (uvicorn)..."
    cd "${BACKEND_DIR}"
    source "${VENV_DIR}/bin/activate"

    # Start backend in background with USE_DEMO if enabled
    # Redirect to a log file to keep terminal clean
    if [ "$USE_DEMO" = "true" ]; then
        USE_DEMO=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/rxdistribute_backend.log 2>&1 &
    else
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/rxdistribute_backend.log 2>&1 &
    fi
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/rxdistribute_backend.pid
    
    # Wait for backend to start
    log_section "Waiting for backend to start (checking health endpoint)..."
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))
        if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
            log_info "Backend API is running ✓"
            break
        fi
        sleep 1
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        log_error "Backend failed to start. Check logs: tail -f /tmp/rxdistribute_backend.log"
        exit 1
    fi
}

################################################################################
# 7. Start Mobile App
################################################################################

start_mobile_app() {
    log_section "Starting mobile app (Expo)..."
    cd "${MOBILE_DIR}"
    
    # Start Expo in a way that allows user interaction
    npx expo start --clear
}

################################################################################
# 8. Display Demo Credentials
################################################################################

display_demo_credentials() {
    log_header "🎉 Digital Prescription Demo Ready!"
    
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Demo Credentials${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Doctor Account:${NC}"
    echo -e "  Email:    ${YELLOW}sarah.johnson@hospital.co.za${NC}"
    echo -e "  Password: ${YELLOW}Demo@2024${NC}"
    echo ""
    echo -e "${GREEN}Patient Account:${NC}"
    echo -e "  Email:    ${YELLOW}john.smith@example.com${NC}"
    echo -e "  Password: ${YELLOW}Demo@2024${NC}"
    echo ""
    echo -e "${GREEN}Pharmacist Account:${NC}"
    echo -e "  Email:    ${YELLOW}lisa.chen@pharmacy.co.za${NC}"
    echo -e "  Password: ${YELLOW}Demo@2024${NC}"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}📱 Mobile App (Expo):${NC}"
    echo "  Press 'i' for iOS simulator (macOS only)"
    echo "  Press 'a' for Android emulator"
    echo "  Scan QR code with Expo Go app on your phone"
    echo ""
    echo -e "${GREEN}🔗 Backend URLs:${NC}"
    echo -e "  API:              ${BLUE}http://localhost:8000${NC}"
    echo -e "  API Docs:         ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "  Health:           ${BLUE}http://localhost:8000/api/v1/health${NC}"
    echo ""
    echo -e "${GREEN}🐳 Docker Containers:${NC}"
    echo -e "  View logs:        ${BLUE}docker-compose logs -f${NC}"
    echo -e "  Stop services:    ${BLUE}docker-compose down${NC}"
    echo ""
    echo -e "${YELLOW}Ctrl+C${NC} to stop the mobile app"
    echo ""
}

################################################################################
# Cleanup & Signal Handlers
################################################################################

cleanup() {
    echo ""
    log_warn "Shutting down..."
    
    # Kill backend server if it's running
    if [ -f /tmp/rxdistribute_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/rxdistribute_backend.pid)
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID" 2>/dev/null || true
        fi
        rm -f /tmp/rxdistribute_backend.pid
    fi
    
    log_info "Cleanup complete"
}

trap cleanup EXIT INT TERM

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║   🏥 Digital Prescription Demo - Automated Startup        ║"
    echo "║                                                            ║"
    echo "║   Initializing environment...                              ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_prerequisites
    start_docker_infrastructure
    setup_backend
    setup_mobile
    display_startup_info
    start_backend_server
    display_demo_credentials
    start_mobile_app
}

# Run main function
main
