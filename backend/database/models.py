import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    HR = "HR"
    FINANCE = "FINANCE"
    ADMIN = "ADMIN"
    SECURITY = "SECURITY"


class DataClassification(str, enum.Enum):
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    HIGHLY_RESTRICTED = "HIGHLY_RESTRICTED"


class DocumentStatus(str, enum.Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DRAFT = "draft"


class ACLDecision(str, enum.Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    PARTIAL = "PARTIAL"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.EMPLOYEE.value)
    department = Column(String(100), nullable=False, default="General")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, default="md")
    domain = Column(String(100), default="HR/Enterprise")
    classification = Column(String(50), default=DataClassification.INTERNAL.value, nullable=False)
    allowed_roles = Column(JSON, nullable=False)  # List of allowed roles
    version = Column(String(50), default="1.0", nullable=False)
    effective_date = Column(String(50), default="2026-01-01")
    status = Column(String(50), default=DocumentStatus.ACTIVE.value, nullable=False)
    chunk_count = Column(Integer, default=0)
    language = Column(String(20), default="en")
    checksum = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    effective_date = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default=DocumentStatus.ACTIVE.value, nullable=False)
    checksum = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="versions")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, default=0)
    allowed_roles = Column(JSON, nullable=False)
    classification = Column(String(50), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True, nullable=False)
    trace_id = Column(String(100), index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)  # LOGIN, SEARCH, QUERY, UPLOAD, ACL_DENIAL, INJECTION_DETECTED
    resource = Column(String(255), nullable=True)
    query = Column(Text, nullable=True)
    acl_decision = Column(String(50), nullable=False, default="ALLOWED")  # ALLOWED, DENIED
    reason = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    status_code = Column(Integer, default=200)
    latency_ms = Column(Float, default=0.0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(100), primary_key=True, index=True)
    run_name = Column(String(255), nullable=False)
    evaluator_type = Column(String(100), default="rag_and_acl")
    total_questions = Column(Integer, default=0)
    metrics_summary = Column(JSON, nullable=True)
    status = Column(String(50), default="COMPLETED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(100), nullable=True)
    query = Column(Text, nullable=False)
    user_role = Column(String(50), nullable=False)
    expected_decision = Column(String(50), nullable=True)
    actual_decision = Column(String(50), nullable=True)
    passed = Column(Boolean, default=True)
    retrieval_metrics = Column(JSON, nullable=True)
    generation_metrics = Column(JSON, nullable=True)
    acl_passed = Column(Boolean, default=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("EvaluationRun", back_populates="results")
