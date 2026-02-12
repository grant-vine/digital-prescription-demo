"""FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.prescriptions import router as prescriptions_router
from app.api.v1.dids import router as dids_router
from app.api.v1.signing import router as signing_router
from app.api.v1.qr import router as qr_router
from app.api.v1.verify import router as verify_router
from app.api.v1.admin import router as admin_router
from app.api.v1.audit import router as audit_router
from app.api.v1.time_validation import router as time_validation_router

app = FastAPI(
    title="Digital Prescription API",
    description="Backend API for digital prescription demo using Self-Sovereign Identity",
    version="0.1.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(prescriptions_router, prefix="/api/v1", tags=["prescriptions"])
app.include_router(dids_router, tags=["dids"])
app.include_router(signing_router, tags=["signing"])
app.include_router(qr_router, tags=["qr"])
app.include_router(verify_router, tags=["verification"])
app.include_router(admin_router, prefix="/api/v1", tags=["admin"])
app.include_router(audit_router, prefix="/api/v1")
app.include_router(time_validation_router, prefix="/api/v1", tags=["time-validation"])


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Digital Prescription API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        }
    }
