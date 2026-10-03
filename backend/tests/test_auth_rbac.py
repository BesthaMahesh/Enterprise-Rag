import pytest
from backend.auth.password import get_password_hash, verify_password
from backend.auth.jwt import create_access_token, decode_access_token
from backend.auth.rbac import has_permission, get_allowed_classifications_for_role


def test_password_hashing():
    pw = "SecretPass123!"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_jwt_token_cycle():
    payload = {"sub": "employee@acme.local", "role": "EMPLOYEE"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "employee@acme.local"
    assert decoded["role"] == "EMPLOYEE"


def test_password_reset_token_cycle():
    from backend.auth.jwt import create_password_reset_token, decode_password_reset_token
    email = "test.employee@acme.local"
    token = create_password_reset_token(email)
    assert isinstance(token, str)

    decoded_email = decode_password_reset_token(token)
    assert decoded_email == email

    # Access tokens should not decode as reset tokens
    access_token = create_access_token({"sub": email, "role": "EMPLOYEE"})
    assert decode_password_reset_token(access_token) is None


def test_rbac_permissions():
    assert has_permission("EMPLOYEE", "chat:ask") is True
    assert has_permission("EMPLOYEE", "documents:upload") is False
    assert has_permission("HR", "documents:upload") is True
    assert has_permission("ADMIN", "system:manage") is True


def test_role_classifications():
    emp_classes = get_allowed_classifications_for_role("EMPLOYEE")
    assert "INTERNAL" in emp_classes
    assert "CONFIDENTIAL" not in emp_classes
    assert "HIGHLY_RESTRICTED" not in emp_classes

    hr_classes = get_allowed_classifications_for_role("HR")
    assert "INTERNAL" in hr_classes
    assert "CONFIDENTIAL" in hr_classes
    assert "HIGHLY_RESTRICTED" not in hr_classes

    admin_classes = get_allowed_classifications_for_role("ADMIN")
    assert "HIGHLY_RESTRICTED" in admin_classes

