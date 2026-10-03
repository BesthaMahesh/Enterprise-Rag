from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    document: str  # Document Title
    organization: Optional[str] = "Acme Technologies"
    domain: Optional[str] = "HR/Enterprise"
    classification: str = "INTERNAL"
    allowed_roles: List[str] = ["EMPLOYEE", "HR", "FINANCE", "ADMIN"]
    version: str = "1.0"
    effective_date: Optional[str] = "2026-01-01"
    status: str = "active"
    language: str = "en"
    checksum: Optional[str] = None


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    section: Optional[str] = "General"
    page_number: Optional[int] = 1
    token_count: int = 0
    allowed_roles: List[str]
    classification: str
    version: str = "1.0"
    effective_date: Optional[str] = "2026-01-01"
    status: str = "active"
    language: str = "en"
    domain: str = "HR/Enterprise"
    extra_metadata: Optional[Dict[str, Any]] = None
