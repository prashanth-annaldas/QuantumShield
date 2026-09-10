"""
FastAPI application entrypoint for Quantum Digital Signature (QDS) Framework.
Integrates authentication, database persistence, QDS protocol, threat detection, and analytics.
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.qds import router as qds_router
from app.api.threats import router as threats_router
from app.api.analytics import router as analytics_router
from app.api.realtime import router as realtime_router
from app.api.incidents import router as incidents_router
from app.api.monitoring import router as monitoring_router
from app.api.audit import router as audit_router
from app.core.middleware import LatencyMetricsMiddleware
from app.core.request_id_middleware import RequestIdMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.exceptions import (
    QDSBaseException,
    qds_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

# Initialize database schema tables for development/test convenience
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    # Safely continue if database connection is deferred until request time
    pass

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-style REST backend for Quantum-Inspired Cyber Threat Detection and Digital Signature Security.",
    docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT != "production" else None
)

# Exception handlers
app.add_exception_handler(QDSBaseException, qds_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Configure Middleware stack (executed in reverse order of addition: RequestId -> Latency -> CORS -> SecurityHeaders)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LatencyMetricsMiddleware)
app.add_middleware(RequestIdMiddleware)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register versioned API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(qds_router, prefix=settings.API_V1_STR)
app.include_router(threats_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(realtime_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(monitoring_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root application status")
def root():
    return {
        "message": "Quantum-Inspired Cyber Threat Detection Framework API",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "OPERATIONAL",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", summary="Health check endpoint")
def health_check():
    """
    Production health check monitoring database availability safely without leaking credentials.
    Preserves backward compatibility with prior health check responses.
    """
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "application": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "version": settings.VERSION
    }


@app.get(f"{settings.API_V1_STR}/system/info", summary="System subsystems runtime status")
def system_info():
    """
    Returns public non-sensitive subsystem capabilities and operational parameters.
    """
    return {
        "application": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "quantum_engine": {
            "status": "OPERATIONAL",
            "implementation": "Mathematical Linear Algebra (NumPy)",
            "qubit_dimension": 256,
            "entanglement_resource": "Bell Phi-Plus EPR Pairs"
        },
        "threat_engine": {
            "status": "OPERATIONAL",
            "methodology": "Strictly Deterministic Rule Engine (Non-AI/ML)",
            "monitored_vectors": [
                "SIGNATURE_FORGERY",
                "IMPERSONATION_ATTACK",
                "REPLAY_ATTACK",
                "QUANTUM_CHANNEL_MANIPULATION",
                "UNAUTHORIZED_VERIFICATION"
            ]
        },
        "database": "SQLAlchemy ORM (PostgreSQL/SQLite)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
