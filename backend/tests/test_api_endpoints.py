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


def test_public_registration_is_unavailable():
    response = client.post("/api/auth/register", json={
        "email": "newhire@acme.local",
        "full_name": "Alex Smith",
        "password": "SecurePassword2026!"
    })
    assert response.status_code == 404
