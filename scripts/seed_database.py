import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import SessionLocal, init_db
from backend.database.models import User, UserRole
from backend.auth.password import get_password_hash
from backend.config.settings import settings


def seed_demo_users():
    init_db()
    db = SessionLocal()

    existing_count = db.query(User).count()
    if existing_count >= 5:
        # Demo users already present, skip re-hashing to ensure instant startup
        db.close()
        return

    demo_users = [
        {
            "email": "employee@acme.local",
            "password": settings.DEFAULT_EMPLOYEE_PASSWORD,
            "full_name": "Jane Employee",
            "role": UserRole.EMPLOYEE.value,
            "department": "Engineering"
        },
        {
            "email": "hr@acme.local",
            "password": settings.DEFAULT_HR_PASSWORD,
            "full_name": "Sarah HR Specialist",
            "role": UserRole.HR.value,
            "department": "Human Resources"
        },
        {
            "email": "finance@acme.local",
            "password": settings.DEFAULT_FINANCE_PASSWORD,
            "full_name": "David Financial Analyst",
            "role": UserRole.FINANCE.value,
            "department": "Finance"
        },
        {
            "email": "admin@acme.local",
            "password": settings.DEFAULT_ADMIN_PASSWORD,
            "full_name": "Alexander Admin",
            "role": UserRole.ADMIN.value,
            "department": "Executive Office"
        },
        {
            "email": "security@acme.local",
            "password": settings.DEFAULT_SECURITY_PASSWORD,
            "full_name": "Elena Security Lead",
            "role": UserRole.SECURITY.value,
            "department": "InfoSec"
        },
    ]

    for u in demo_users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_u = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                department=u["department"],
                is_active=True
            )
            db.add(new_u)
            print(f"Created demo user: {u['email']} (Role: {u['role']})")
        else:
            # Update password hash
            existing.hashed_password = get_password_hash(u["password"])
            existing.full_name = u["full_name"]
            existing.role = u["role"]
            existing.department = u["department"]
            print(f"Updated demo user: {u['email']} (Role: {u['role']})")

    db.commit()
    db.close()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_demo_users()
