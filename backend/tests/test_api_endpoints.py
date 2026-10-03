import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import init_db, SessionLocal
from backend.database.models import User, UserRole
from backend.auth.password import get_password_hash
from backend.config.settings import settings

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    init_db()
    db = SessionLocal()
    
    # Ensure test employee exists
    if not db.query(User).filter(User.email == "employee@acme.local").first():
        db.add(User(
            email="employee@acme.local",
            hashed_password=get_password_hash(settings.DEFAULT_EMPLOYEE_PASSWORD),
            full_name="Jane Employee",
            role=UserRole.EMPLOYEE.value,
            department="Engineering",
            is_active=True
        ))

    # Ensure test HR exists
    if not db.query(User).filter(User.email == "hr@acme.local").first():
        db.add(User(
            email="hr@acme.local",
            hashed_password=get_password_hash(settings.DEFAULT_HR_PASSWORD),
            full_name="Sarah HR Specialist",
            role=UserRole.HR.value,
            department="Human Resources",
            is_active=True
        ))

    db.commit()
    db.close()


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["online", "degraded"]


def test_auth_login_success():
    response = client.post("/api/auth/login", json={
        "email": "employee@acme.local",
        "password": settings.DEFAULT_EMPLOYEE_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "EMPLOYEE"


def test_auth_login_failure():
    response = client.post("/api/auth/login", json={
        "email": "employee@acme.local",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401


def test_chat_authorized_employee():
    # Login as employee
    login_res = client.post("/api/auth/login", json={
        "email": "employee@acme.local",
        "password": settings.DEFAULT_EMPLOYEE_PASSWORD
    })
    token = login_res.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "How do I apply for annual leave?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data


def test_auth_registration_and_lifecycle():
    import uuid
    new_email = f"newhire.{uuid.uuid4().hex[:8]}@acme.local"
    initial_password = "SecurePassword2026!"

    # 1. Register with weak password -> 422
    weak_res = client.post("/api/auth/register", json={
        "email": new_email,
        "full_name": "Alex Smith",
        "password": "weak",
        "department": "Engineering"
    })
    assert weak_res.status_code == 422

    # 2. Register valid user -> 201 & role strictly EMPLOYEE
    reg_res = client.post("/api/auth/register", json={
        "email": new_email,
        "full_name": "Alex Smith",
        "password": initial_password,
        "department": "Engineering"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["role"] == "EMPLOYEE"
    assert "access_token" in reg_data

    # 3. Duplicate registration -> 409 Conflict (or 400)
    dup_res = client.post("/api/auth/register", json={
        "email": new_email,
        "full_name": "Alex Smith Duplicate",
        "password": initial_password,
        "department": "Engineering"
    })
    assert dup_res.status_code in [400, 409]

    # 4. Verify /api/auth/me returns the server-side role
    token = reg_data["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == new_email
    assert me_data["role"] == "EMPLOYEE"

    # 5. Forgot password flow
    forgot_res = client.post("/api/auth/forgot-password", json={"email": new_email})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    reset_token = forgot_data.get("reset_token")
    assert reset_token is not None

    # 6. Reset password using token
    new_password = "UpdatedPassword2026!"
    reset_res = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": new_password
    })
    assert reset_res.status_code == 200

    # 7. Old password fails
    old_login_res = client.post("/api/auth/login", json={
        "email": new_email,
        "password": initial_password
    })
    assert old_login_res.status_code == 401

    # 8. New password succeeds
    new_login_res = client.post("/api/auth/login", json={
        "email": new_email,
        "password": new_password
    })
    assert new_login_res.status_code == 200
    assert new_login_res.json()["email"] == new_email

    # 9. Token cannot be reused
    reused_reset_res = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "AnotherPassword2026!"
    })
    assert reused_reset_res.status_code == 400

