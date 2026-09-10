"""
Phase 9: Request Context Management.
Provides ContextVar-based request-scoped state for distributed request correlation
and actor tracking without thread-safety or async race condition issues.
"""
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variables scoped per async request execution
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
_actor_user_id_ctx: ContextVar[Optional[str]] = ContextVar("actor_user_id", default=None)
_actor_role_ctx: ContextVar[Optional[str]] = ContextVar("actor_role", default=None)

# Public aliases
request_id_ctx = _request_id_ctx
actor_user_id_ctx = _actor_user_id_ctx
actor_role_ctx = _actor_role_ctx


def get_request_id() -> str:
    """Retrieve the current request correlation ID, or generate a fallback if unset."""
    req_id = _request_id_ctx.get()
    if not req_id:
        req_id = f"req-{uuid.uuid4().hex[:12]}"
        _request_id_ctx.set(req_id)
    return req_id


def set_request_id(request_id: str) -> None:
    """Set the request correlation ID for the current request context."""
    _request_id_ctx.set(request_id)


def get_actor_user_id() -> Optional[str]:
    """Retrieve the authenticated actor user ID for the current request."""
    return _actor_user_id_ctx.get()


def set_actor_user_id(user_id: Optional[str]) -> None:
    """Set the authenticated actor user ID in the current request context."""
    _actor_user_id_ctx.set(user_id)


def get_actor_role() -> Optional[str]:
    """Retrieve the authenticated actor role for the current request."""
    return _actor_role_ctx.get()


def set_actor_role(role: Optional[str]) -> None:
    """Set the authenticated actor role in the current request context."""
    _actor_role_ctx.set(role)


def set_actor(user_id: Optional[str], role: Optional[str]) -> None:
    """Convenience helper to set both actor user ID and role."""
    set_actor_user_id(user_id)
    set_actor_role(role)


def get_context_dict() -> Dict[str, Any]:
    """Return a dictionary snapshot of current request context."""
    return {
        "request_id": get_request_id(),
        "actor_user_id": get_actor_user_id(),
        "actor_role": get_actor_role(),
    }


def clear_context() -> None:
    """Reset context variables for test isolation."""
    _request_id_ctx.set("")
    _actor_user_id_ctx.set(None)
    _actor_role_ctx.set(None)
