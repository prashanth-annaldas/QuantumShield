"""
Application configuration settings module.
Loads configuration from environment variables with safe defaults.
Supports DEVELOPMENT, TESTING, and PRODUCTION environments.
"""
import os
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = os.getenv("APP_NAME", "Quantum-Inspired Cyber Threat Detection (QDS-Framework)")
    PROJECT_NAME: str = os.getenv("APP_NAME", "Quantum-Inspired Cyber Threat Detection (QDS-Framework)")
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./qds_framework.db")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("SECRET_KEY", "qds_super_secret_jwt_signing_key_2026_academic_major_project")
    )
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("SECRET_KEY", "qds_super_secret_jwt_signing_key_2026_academic_major_project")
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", os.getenv("ALGORITHM", "HS256"))
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS Configuration
    CORS_ORIGINS_RAW: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    @property
    def cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS_RAW == "*" or self.ENVIRONMENT == "development":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]

    # Phase 8: Real-Time Security Operations & Rate Limiting
    INCIDENT_CORRELATION_WINDOW_SECONDS: int = int(os.getenv("INCIDENT_CORRELATION_WINDOW_SECONDS", "300"))
    INCIDENT_REJECTION_THRESHOLD: int = int(os.getenv("INCIDENT_REJECTION_THRESHOLD", "3"))
    RATE_LIMIT_LOGIN_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "20"))
    RATE_LIMIT_VERIFY_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_VERIFY_PER_MINUTE", "30"))
    RATE_LIMIT_THREAT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_THREAT_PER_MINUTE", "20"))


settings = Settings()
