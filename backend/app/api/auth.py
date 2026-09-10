"""
Authentication and user management FastAPI endpoints.
Provides registration, login, and profile access with JWT tokens and RBAC.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limiter import check_rate_limit
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from app.db.models import UserModel
from app.db.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_ROLES = {"USER", "SECURITY_ANALYST", "ADMIN"}


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
def register(request: Request, req: UserRegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Registers a new user with secure password hashing and default USER role.
    Rejects duplicate usernames and emails.
    """
    check_rate_limit(request, "auth_register", settings.RATE_LIMIT_LOGIN_PER_MINUTE)
    # Check for existing username or email
    existing_user = db.query(UserModel).filter(
        (UserModel.username == req.username) | (UserModel.email == req.email)
    ).first()
    if existing_user:
        if existing_user.username == req.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{req.username}' is already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{req.email}' is already registered"
            )

    role = (req.role or "USER").upper()
    if role not in VALID_ROLES:
        role = "USER"

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    hashed_pwd = get_password_hash(req.password)

    new_user = UserModel(
        id=user_id,
        username=req.username,
        email=req.email,
        password_hash=hashed_pwd,
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token({
        "sub": new_user.username,
        "user_id": new_user.id,
        "role": new_user.role
    })

    user_resp = UserResponse.model_validate(new_user)
    
    # Phase 9: Record audit event for registration
    from app.audit.service import record_audit_event
    record_audit_event(
        db=db,
        action="AUTH_REGISTER",
        severity="INFO",
        outcome="SUCCESS",
        actor_user_id=new_user.id,
        actor_username=new_user.username,
        actor_role=new_user.role,
        resource_type="USER",
        resource_id=new_user.id,
        details={"username": new_user.username, "role": new_user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token"
)
async def login(request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticates user credentials and issues a JWT token.
    Supports both JSON body ({'username': ..., 'password': ...}) and OAuth2 Form data.
    """
    check_rate_limit(request, "auth_login", settings.RATE_LIMIT_LOGIN_PER_MINUTE)
    content_type = request.headers.get("content-type", "")
    username: Optional[str] = None
    password: Optional[str] = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON request body"
            )
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid form request data"
            )

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both username and password are required"
        )

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        from app.realtime.publisher import publish_security_event
        from app.realtime.events import SecurityEventType, SecurityEventSeverity
        from app.monitoring.metrics import metrics_collector
        from app.audit.service import record_audit_event

        metrics_collector.record_auth_failure()
        record_audit_event(
            db=db,
            action="AUTH_LOGIN_FAILURE",
            severity="WARNING",
            outcome="FAILURE",
            actor_user_id=user.id if user else None,
            actor_username=username,
            actor_role=user.role if user else None,
            resource_type="USER",
            resource_id=user.id if user else None,
            details={"attempted_username": username, "reason": "invalid_credentials"}
        )

        try:
            publish_security_event(
                db=db,
                event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                severity=SecurityEventSeverity.MEDIUM,
                session_id=None,
                user_id=user.id if user else None,
                message=f"Failed login attempt for username '{username}'",
                metadata={"username": username}
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token({
        "sub": user.username,
        "user_id": user.id,
        "role": user.role
    })

    from app.audit.service import record_audit_event
    record_audit_event(
        db=db,
        action="AUTH_LOGIN_SUCCESS",
        severity="INFO",
        outcome="SUCCESS",
        actor_user_id=user.id,
        actor_username=user.username,
        actor_role=user.role,
        resource_type="USER",
        resource_id=user.id,
        details={"username": user.username, "role": user.role}
    )

    user_resp = UserResponse.model_validate(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile"
)
def get_me(current_user: UserModel = Depends(get_current_user)) -> UserResponse:
    """
    Returns the authenticated user's profile information.
    Guarantees password hashes are never exposed.
    """
    return UserResponse.model_validate(current_user)
