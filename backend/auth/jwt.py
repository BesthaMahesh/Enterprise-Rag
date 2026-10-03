from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from backend.config.settings import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") and payload.get("type") != "access":
            return None
        return payload
    except (jwt.PyJWTError, Exception):
        return None


import uuid

_invalidated_reset_tokens = set()


def create_password_reset_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed short-lived JWT token for password resets."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    to_encode = {
        "sub": email,
        "jti": str(uuid.uuid4()),
        "type": "reset_password",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> Optional[str]:
    """Validate password reset token and return email if valid and not invalidated."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "reset_password":
            return None
        jti = payload.get("jti")
        if jti and jti in _invalidated_reset_tokens:
            return None
        return payload.get("sub")
    except (jwt.PyJWTError, Exception):
        return None


def invalidate_password_reset_token(token: str) -> None:
    """Mark a reset token as used/invalidated."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        if jti:
            _invalidated_reset_tokens.add(jti)
    except Exception:
        pass

