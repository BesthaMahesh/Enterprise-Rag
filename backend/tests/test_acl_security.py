import pytest
from backend.acl.service import acl_service
from backend.context.builder import ContextBuilder


def test_acl_document_authorization():
    internal_doc = {
        "document_id": "leave_policy",
        "classification": "INTERNAL",
        "allowed_roles": ["EMPLOYEE", "HR", "FINANCE", "ADMIN"]
    }
    hr_private_doc = {
        "document_id": "hr_budget_2026",
        "classification": "CONFIDENTIAL",
        "allowed_roles": ["HR", "ADMIN"]
    }
    admin_doc = {
        "document_id": "executive_compensation",
        "classification": "HIGHLY_RESTRICTED",
        "allowed_roles": ["ADMIN"]
    }

    # EMPLOYEE checks
    assert acl_service.is_document_authorized("EMPLOYEE", internal_doc) is True
    assert acl_service.is_document_authorized("EMPLOYEE", hr_private_doc) is False
    assert acl_service.is_document_authorized("EMPLOYEE", admin_doc) is False

    # HR checks
    assert acl_service.is_document_authorized("HR", internal_doc) is True
    assert acl_service.is_document_authorized("HR", hr_private_doc) is True
    assert acl_service.is_document_authorized("HR", admin_doc) is False

    # ADMIN checks
    assert acl_service.is_document_authorized("ADMIN", internal_doc) is True
    assert acl_service.is_document_authorized("ADMIN", hr_private_doc) is True
    assert acl_service.is_document_authorized("ADMIN", admin_doc) is True


def test_acl_chunk_filtering():
    chunks = [
        {"chunk_id": "c1", "classification": "INTERNAL", "allowed_roles": ["EMPLOYEE", "HR"]},
        {"chunk_id": "c2", "classification": "CONFIDENTIAL", "allowed_roles": ["HR", "ADMIN"]},
        {"chunk_id": "c3", "classification": "HIGHLY_RESTRICTED", "allowed_roles": ["ADMIN"]}
    ]

    emp_filtered = acl_service.filter_authorized_chunks("EMPLOYEE", chunks)
    assert len(emp_filtered) == 1
    assert emp_filtered[0]["chunk_id"] == "c1"

    hr_filtered = acl_service.filter_authorized_chunks("HR", chunks)
    assert len(hr_filtered) == 2
    assert {c["chunk_id"] for c in hr_filtered} == {"c1", "c2"}

    admin_filtered = acl_service.filter_authorized_chunks("ADMIN", chunks)
    assert len(admin_filtered) == 3


def test_context_builder_security_barrier():
    mixed_chunks = [
        {"chunk_id": "c1", "document_title": "Handbook", "section": "General", "classification": "INTERNAL", "allowed_roles": ["EMPLOYEE", "HR"], "content": "Leave rules and time off guidelines."},
        {"chunk_id": "c2", "document_title": "Payroll", "section": "Salaries", "classification": "CONFIDENTIAL", "allowed_roles": ["HR"], "content": "Executive salary $500k"}
    ]

    context_str, authorized_chunks = ContextBuilder.build_context(
        query="What are the leave rules?",
        raw_candidates=mixed_chunks,
        user_role="EMPLOYEE"
    )

    assert len(authorized_chunks) == 1
    assert "Executive salary" not in context_str
    assert "Leave rules" in context_str


def test_acl_pre_retrieval_regression():
    """
    Phase 3 Regression Security Invariant:
    1. EMPLOYEE -> restricted HR document -> DENY
    2. EMPLOYEE -> ADMIN document -> DENY
    3. HR -> HR confidential document -> ALLOW
    4. HR -> ADMIN-only document -> DENY
    5. ADMIN -> authorized restricted document -> ALLOW
    """
    hr_confidential_doc = {
        "document_id": "workforce_attrition_report",
        "document_title": "Workforce Attrition Report",
        "classification": "CONFIDENTIAL",
        "allowed_roles": ["HR", "ADMIN"]
    }
    admin_only_doc = {
        "document_id": "executive_compensation_summary",
        "document_title": "Executive Compensation Summary",
        "classification": "HIGHLY_RESTRICTED",
        "allowed_roles": ["ADMIN"]
    }

    # 1. EMPLOYEE -> restricted HR document -> DENY
    is_auth, reason = acl_service.evaluate_chunk_access("EMPLOYEE", hr_confidential_doc)
    assert is_auth is False
    assert reason in ["ROLE_NOT_AUTHORIZED", "CLASSIFICATION_RESTRICTED"]

    # 2. EMPLOYEE -> ADMIN document -> DENY
    is_auth, reason = acl_service.evaluate_chunk_access("EMPLOYEE", admin_only_doc)
    assert is_auth is False
    assert reason in ["ROLE_NOT_AUTHORIZED", "CLASSIFICATION_RESTRICTED"]

    # 3. HR -> HR confidential document -> ALLOW
    is_auth, reason = acl_service.evaluate_chunk_access("HR", hr_confidential_doc)
    assert is_auth is True
    assert reason == "AUTHORIZED"

    # 4. HR -> ADMIN-only document -> DENY
    is_auth, reason = acl_service.evaluate_chunk_access("HR", admin_only_doc)
    assert is_auth is False
    assert reason in ["ROLE_NOT_AUTHORIZED", "CLASSIFICATION_RESTRICTED"]

    # 5. ADMIN -> authorized restricted document -> ALLOW
    is_auth, reason = acl_service.evaluate_chunk_access("ADMIN", admin_only_doc)
    assert is_auth is True
    assert reason == "AUTHORIZED"

