import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.models import User
from backend.auth.password import verify_password, get_password_hash
from backend.auth.jwt import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    invalidate_password_reset_token
)
from backend.auth.dependencies import get_current_user
from backend.schemas.auth import (
    UserLogin,
    Token,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    AuthMessageResponse
)
from backend.observability.audit import AuditLogger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def validate_password_complexity(password: str) -> None:
    """Validate password against enterprise complexity policy."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter."
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter."
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number."
        )
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character."
        )


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    clean_email = login_data.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        # Audit login failure
        AuditLogger.log_event(
            db=db,
            user_email=clean_email,
            role="UNKNOWN",
            action="LOGIN_FAILED",
            acl_decision="DENIED",
            reason="Invalid email or password",
            status_code=401
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        AuditLogger.log_event(
            db=db,
            user_email=user.email,
            role=user.role,
            action="LOGIN_BLOCKED",
            acl_decision="DENIED",
            reason="Inactive account",
            status_code=403
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is currently unavailable. Please contact your administrator."
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )

    AuditLogger.log_event(
        db=db,
        user_email=user.email,
        role=user.role,
        action="LOGIN_SUCCESS",
        acl_decision="ALLOWED",
        reason="Successful authentication"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        department=user.department
    )


@router.post("/forgot-password", response_model=AuthMessageResponse)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    reset_token = None
    if user and user.is_active:
        reset_token = create_password_reset_token(user.email)
        AuditLogger.log_event(
            db=db,
            user_email=user.email,
            role=user.role,
            action="PASSWORD_RESET_REQUESTED",
            acl_decision="ALLOWED",
            reason="Password reset requested"
        )

    # Always return uniform response to prevent user enumeration
    return AuthMessageResponse(
        message="If an account exists for this email address, password reset instructions will be sent.",
        reset_token=reset_token  # Provided for local/dev flow verification
    )


@router.post("/reset-password", response_model=AuthMessageResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = decode_password_reset_token(req.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link. Please request a new one."
        )

    validate_password_complexity(req.new_password)

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not found or inactive."
        )

    user.hashed_password = get_password_hash(req.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Invalidate reset token after successful reset
    invalidate_password_reset_token(req.token)

    AuditLogger.log_event(
        db=db,
        user_email=user.email,
        role=user.role,
        action="PASSWORD_RESET_COMPLETED",
        acl_decision="ALLOWED",
        reason="Password successfully reset"
    )

    return AuthMessageResponse(
        message="Password has been reset successfully. You can now sign in with your new password."
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="LOGOUT",
        acl_decision="ALLOWED"
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
