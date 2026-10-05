import pytest
from rank_bm25 import BM25Okapi
from backend.acl.service import acl_service
from backend.context.builder import ContextBuilder
from backend.retrieval.sparse import SparseRetriever, tokenize_text


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


def test_retrieval_reports_private_denial_signal_for_restricted_match():
    retriever = SparseRetriever(index_path="missing-test-index.pkl")
    retriever.corpus_chunks = [
        {
            "chunk_id": "leave-1",
            "document_id": "documents_employee_accessible_leave_policy",
            "content": "Employees can submit an annual leave request through the portal.",
            "classification": "INTERNAL",
            "allowed_roles": ["EMPLOYEE", "HR", "FINANCE", "ADMIN"],
        },
        {
            "chunk_id": "payroll-1",
            "document_id": "documents_hr_private_payroll_summary_2026",
            "content": "Monthly payroll cost and compensation breakdown for the current year.",
            "classification": "CONFIDENTIAL",
            "allowed_roles": ["HR", "FINANCE", "ADMIN"],
        },
        {
            "chunk_id": "admin-1",
            "document_id": "documents_admin_restricted_executive_compensation",
            "content": "Executive compensation governance and board committee oversight details.",
            "classification": "HIGHLY_RESTRICTED",
            "allowed_roles": ["ADMIN"],
        },
    ]
    retriever.bm25 = BM25Okapi([tokenize_text(chunk["content"]) for chunk in retriever.corpus_chunks])

    denied, contact = retriever.check_unauthorized_match("What is the monthly payroll cost?", "EMPLOYEE")
    assert denied is True
    assert contact == "Finance"

    denied, contact = retriever.check_unauthorized_match("What is executive compensation governance?", "EMPLOYEE")
    assert denied is True
    assert contact == "Admin"

    assert retriever.has_unauthorized_match("What is the monthly payroll cost?", "EMPLOYEE") is True
    assert retriever.has_unauthorized_match("What is the monthly payroll cost?", "FINANCE") is False
    assert retriever.has_unauthorized_match("How do I submit annual leave?", "EMPLOYEE") is False

