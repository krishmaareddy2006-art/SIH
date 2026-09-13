"""Central API v1 Router for ForensicShield."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, cases, evidence, jobs, devices, erasure, sanitization, forensic, recovery, carving, validation, audit, notarization, reports

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
api_v1_router.include_router(evidence.router, tags=["Evidence"])
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["Sensitive Jobs"])
api_v1_router.include_router(devices.router, prefix="/devices", tags=["Device Discovery"])
api_v1_router.include_router(erasure.router, prefix="/erasure", tags=["File Erasure"])
api_v1_router.include_router(sanitization.router, prefix="/sanitization", tags=["Storage Sanitization"])
api_v1_router.include_router(forensic.router, prefix="/forensic", tags=["Forensics"])
api_v1_router.include_router(recovery.router, tags=["Filesystem Recovery"])
api_v1_router.include_router(carving.router, tags=["File Carving"])
api_v1_router.include_router(validation.router, prefix="/validation", tags=["Recovery Validation"])
api_v1_router.include_router(audit.router, prefix="/audit", tags=["Tamper-Evident Audit Logging"])
api_v1_router.include_router(notarization.router, prefix="/notarization", tags=["Blockchain Integrity Notarization"])
api_v1_router.include_router(reports.router, tags=["Forensic Reporting"])






