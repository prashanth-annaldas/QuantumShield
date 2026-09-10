"""
Phase 9: Structured JSON Security Audit Logger.
Formats audit events as structured JSON and guarantees sanitization of sensitive
fields (passwords, JWTs, secrets, cryptographic private materials).
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.request_context import get_request_id, get_actor_user_id, get_actor_role

logger = logging.getLogger("qds.security.audit")

SENSITIVE_KEYS = {
    "password", "password_hash", "pass", "token", "access_token", "jwt",
    "secret", "secret_key", "authorization", "private_key", "jwt_secret_key",
    "api_key", "apikey", "credential", "auth"
}


def sanitize_audit_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Recursively sanitizes dictionary removing all sensitive credential keys.
    """
    if not metadata:
        return {}

    sanitized = {}
    for key, value in metadata.items():
        lower_key = str(key).lower()
        if any(s in lower_key for s in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_audit_metadata(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def log_security_audit(
    action: str,
    outcome: str = "SUCCESS",
    severity: str = "INFO",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Emits a structured JSON audit log entry to the security logger.
    Auto-populates request_id, actor_user_id, and actor_role from ContextVar if omitted.
    """
    req_id = request_id or get_request_id()
    user_id = actor_user_id or get_actor_user_id()
    role = actor_role or get_actor_role()
    clean_meta = sanitize_audit_metadata(metadata)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": req_id,
        "actor_user_id": user_id,
        "actor_role": role,
        "action": action,
        "outcome": outcome,
        "severity": severity,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "metadata": clean_meta,
    }

    # Emit as structured JSON string
    log_level = logging.WARNING if severity in ("HIGH", "CRITICAL") or outcome != "SUCCESS" else logging.INFO
    logger.log(log_level, json.dumps(log_entry))

    return log_entry
