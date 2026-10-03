from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    document_id: str
    title: str
    file_name: str
    domain: str = "HR/Enterprise"
    classification: str = "INTERNAL"
    allowed_roles: List[str]
    version: str = "1.0"
    effective_date: Optional[str] = "2026-01-01"
    status: str = "active"
    language: str = "en"


class DocumentCreate(DocumentBase):
    content: Optional[str] = None
    file_path: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    file_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int
    allowed_roles: List[str]
    classification: str

    class Config:
        from_attributes = True


class DocumentFilter(BaseModel):
    domain: Optional[str] = None
    classification: Optional[str] = None
    allowed_role: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None


class DocumentReindexResponse(BaseModel):
    success: bool
    document_id: str
    chunks_indexed: int
    message: str
