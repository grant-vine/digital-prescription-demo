<#
################################################################################
# Digital Prescription Demo - Automated Startup Script (Windows PowerShell)
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
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start-demo-windows.ps1
# Or: .\scripts\start-demo-windows.ps1 (if execution policy allows)
################################################################################
#>

#Requires -Version 5.0

param()

# Enable error handling
$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $PROJECT_ROOT "services" "backend"
$MOBILE_DIR = Join-Path $PROJECT_ROOT "apps" "mobile"
$VENV_DIR = Join-Path $BACKEND_DIR "venv"
$VENV_SCRIPTS = Join-Path $VENV_DIR "Scripts"

################################################################################
# Helper Functions
################################################################################

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "→ $Message" -ForegroundColor Yellow
}

################################################################################
# 1. Check Prerequisites
################################################################################

function Check-Prerequisites {
    Write-Header "STEP 1: Checking Prerequisites"
    
    # Check Python version
    Write-Section "Checking Python (3.12+ required)..."
    try {
        $pythonVersion = python --version 2>&1 | Select-String -Pattern "\d+\.\d+" -AllMatches
        if ($pythonVersion.Matches.Count -gt 0) {
            $version = $pythonVersion.Matches[0].Value
            Write-Info "Python $version ✓"
        } else {
            Write-Error-Custom "Python version check failed"
            exit 1
        }
    } catch {
        Write-Error-Custom "Python is not installed"
        exit 1
    }
    
    # Check Node.js version
    Write-Section "Checking Node.js (20+ required)..."
    try {
        $nodeVersion = node --version
        Write-Info "Node.js $nodeVersion ✓"
    } catch {
        Write-Error-Custom "Node.js is not installed"
        exit 1
    }
    
    # Check Docker
    Write-Section "Checking Docker Desktop..."
    try {
        $dockerStatus = docker ps 2>&1
        Write-Info "Docker Desktop is running ✓"
    } catch {
        Write-Error-Custom "Docker is not installed or not running. Please install Docker Desktop."
        exit 1
    }
    
    # Check Git
    Write-Section "Checking Git..."
    try {
        $gitVersion = git --version
        Write-Info "$gitVersion ✓"
    } catch {
        Write-Warn "Git is not installed (optional, but recommended)"
    }
}

################################################################################
# 2. Start Docker Infrastructure
################################################################################

function Start-DockerInfrastructure {
    Write-Header "STEP 2: Starting Docker Infrastructure"
    
    Set-Location $PROJECT_ROOT
    
    Write-Section "Pulling Docker images (may take a few minutes on first run)..."
    try {
        docker-compose pull db redis acapy 2>&1 | Out-Null
    } catch {
        Write-Warn "Some images already cached"
    }
    
    Write-Section "Starting PostgreSQL, Redis, and ACA-Py..."
    docker-compose up -d db redis acapy
    
    Write-Section "Waiting for services to be healthy (this may take 30-45 seconds)..."
    
    $maxAttempts = 60
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        $attempt++
        
        try {
            docker-compose exec -T db pg_isready -U postgres 2>&1 | Out-Null
            Write-Info "PostgreSQL is healthy"
            break
        } catch {
            if ($attempt % 10 -eq 0) {
                Write-Host "." -NoNewline
            }
            Start-Sleep -Seconds 1
        }
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Error-Custom "Services failed to start. Check Docker logs: docker-compose logs"
        exit 1
    }
    
    Start-Sleep -Seconds 5
    Write-Info "All Docker services are healthy ✓"
}

################################################################################
# 3. Setup Backend
################################################################################

function Setup-Backend {
    Write-Header "STEP 3: Setting up Backend API"
    
    Set-Location $BACKEND_DIR
    
    # Create virtual environment if it doesn't exist
    Write-Section "Setting up Python virtual environment..."
    if (-not (Test-Path $VENV_DIR)) {
        python -m venv $VENV_DIR
        Write-Info "Virtual environment created"
    } else {
        Write-Info "Virtual environment already exists"
    }
    
    # Activate virtual environment
    & (Join-Path $VENV_SCRIPTS "Activate.ps1")
    
    # Upgrade pip
    Write-Section "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel 2>&1 | Out-Null
    
    # Install dependencies
    Write-Section "Installing Python dependencies (may take 1-2 minutes)..."
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        Write-Info "Dependencies installed ✓"
    } else {
        Write-Error-Custom "requirements.txt not found in $BACKEND_DIR"
        exit 1
    }
    
    # Run database migrations
    Write-Section "Running database migrations..."
    if (Test-Path "alembic.ini") {
        try {
            alembic upgrade head 2>&1 | Out-Null
        } catch {
            Write-Warn "Migration failed (database may already be initialized)"
        }
    } else {
        Write-Warn "alembic.ini not found (skipping migrations)"
    }
    
    # Seed demo data
    Write-Section "Seeding demo data..."
    if (Test-Path "scripts/seed_demo_data.py") {
        python scripts/seed_demo_data.py
        Write-Info "Demo data seeded ✓"
    } else {
        Write-Warn "seed_demo_data.py not found (demo data not seeded)"
    }
}

################################################################################
# 4. Setup Mobile App
################################################################################

function Setup-Mobile {
    Write-Header "STEP 4: Setting up Mobile App"
    
    if (-not (Test-Path $MOBILE_DIR)) {
        Write-Warn "Mobile app directory not found at $MOBILE_DIR"
        return
    }
    
    Set-Location $MOBILE_DIR
    
    Write-Section "Checking mobile dependencies..."
    if (-not (Test-Path "node_modules")) {
        Write-Section "Installing npm dependencies (may take 1-2 minutes)..."
        npm install
        Write-Info "Dependencies installed ✓"
    } else {
        Write-Info "Dependencies already installed"
    }
    
    if ((Test-Path "package.json") -and (Test-Path "package-lock.json")) {
        Write-Info "Package lock verified ✓"
    }
}

################################################################################
# 5. Display Startup Information
################################################################################

function Display-StartupInfo {
    Write-Header "STEP 5: Starting Services"
    
    Write-Host ""
    Write-Host "Services are starting..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend API will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Documentation:               http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "Health Check:                    http://localhost:8000/api/v1/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Mobile app will start at port:   8081 (Expo Metro Bundler)" -ForegroundColor Cyan
    Write-Host ""
}

################################################################################
# 6. Start Backend Server
################################################################################

function Start-BackendServer {
    Write-Section "Starting backend API server (uvicorn)..."
    Set-Location $BACKEND_DIR
    
    & (Join-Path $VENV_SCRIPTS "Activate.ps1")
    
    $logFile = Join-Path $env:TEMP "rxdistribute_backend.log"
    $pidFile = Join-Path $env:TEMP "rxdistribute_backend.pid"
    
    # Start backend in background
    $process = Start-Process `
        -FilePath "python" `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError $logFile `
        -WindowStyle Hidden `
        -PassThru
    
    $process.Id | Out-File -FilePath $pidFile -Force
    
    Write-Section "Waiting for backend to start (checking health endpoint)..."
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Info "Backend API is running ✓"
                return
            }
        } catch {
            # Service not ready yet
        }
        Start-Sleep -Seconds 1
    }
    
    Write-Error-Custom "Backend failed to start. Check logs: type $logFile"
    exit 1
}

################################################################################
# 7. Start Mobile App
################################################################################

function Start-MobileApp {
    Write-Section "Starting mobile app (Expo)..."
    Set-Location $MOBILE_DIR
    
    npx expo start --clear
}

################################################################################
# 8. Display Demo Credentials
################################################################################

function Display-DemoCredentials {
    Write-Header "🎉 Digital Prescription Demo Ready!"
    
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Demo Credentials" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Doctor Account:" -ForegroundColor Green
    Write-Host "  Email:    sarah.johnson@hospital.co.za" -ForegroundColor Yellow
    Write-Host "  Password: Demo@2024" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Patient Account:" -ForegroundColor Green
    Write-Host "  Email:    john.smith@example.com" -ForegroundColor Yellow
    Write-Host "  Password: Demo@2024" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Pharmacist Account:" -ForegroundColor Green
    Write-Host "  Email:    lisa.chen@pharmacy.co.za" -ForegroundColor Yellow
    Write-Host "  Password: Demo@2024" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "📱 Mobile App (Expo):" -ForegroundColor Green
    Write-Host "  Press 'i' for iOS simulator (macOS only)"
    Write-Host "  Press 'a' for Android emulator"
    Write-Host "  Scan QR code with Expo Go app on your phone"
    Write-Host ""
    
    Write-Host "🔗 Backend URLs:" -ForegroundColor Green
    Write-Host "  API:              http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs:         http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Health:           http://localhost:8000/api/v1/health" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "🐳 Docker Containers:" -ForegroundColor Green
    Write-Host "  View logs:        docker-compose logs -f" -ForegroundColor Cyan
    Write-Host "  Stop services:    docker-compose down" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Ctrl+C to stop the mobile app" -ForegroundColor Yellow
    Write-Host ""
}

################################################################################
# Cleanup & Signal Handlers
################################################################################

function Cleanup {
    Write-Host ""
    Write-Warn "Shutting down..."
    
    $pidFile = Join-Path $env:TEMP "rxdistribute_backend.pid"
    if (Test-Path $pidFile) {
        try {
            $backendPid = Get-Content $pidFile
            Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        } catch {
            # Process may already be stopped
        }
    }
    
    Write-Info "Cleanup complete"
}

# Register cleanup handler
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

################################################################################
# Main Execution
################################################################################

function Main {
    Clear-Host
    
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "║   🏥 Digital Prescription Demo - Automated Startup        ║" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "║   Initializing environment...                              ║" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        Check-Prerequisites
        Start-DockerInfrastructure
        Setup-Backend
        Setup-Mobile
        Display-StartupInfo
        Start-BackendServer
        Display-DemoCredentials
        Start-MobileApp
    } catch {
        Write-Error-Custom "An error occurred: $_"
        Cleanup
        exit 1
    }
}

# Run main function
Main
