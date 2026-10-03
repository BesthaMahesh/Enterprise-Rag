import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Document, DocumentChunk, User
from backend.auth.dependencies import get_current_user, require_role
from backend.auth.rbac import has_permission
from backend.schemas.documents import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentReindexResponse
)
from backend.ingestion.pipeline import IngestionPipeline
from backend.observability.audit import AuditLogger
from backend.acl.service import acl_service

router = APIRouter(prefix="/api/documents", tags=["Document Management"])


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    classification: Optional[str] = None,
    domain: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document)

    if classification:
        query = query.filter(Document.classification == classification)
    if domain:
        query = query.filter(Document.domain == domain)
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))

    docs = query.order_by(Document.created_at.desc()).all()

    # Apply strict role filter
    authorized_docs = []
    for doc in docs:
        doc_meta = {
            "allowed_roles": doc.allowed_roles,
            "classification": doc.classification
        }
        if acl_service.is_document_authorized(current_user.role, doc_meta):
            authorized_docs.append(doc)

    return authorized_docs


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_meta = {"allowed_roles": doc.allowed_roles, "classification": doc.classification}
    if not acl_service.is_document_authorized(current_user.role, doc_meta):
        raise HTTPException(status_code=403, detail="Access denied. You do not have permissions to view this document.")

    return doc


@router.get("/{doc_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_meta = {"allowed_roles": doc.allowed_roles, "classification": doc.classification}
    if not acl_service.is_document_authorized(current_user.role, doc_meta):
        raise HTTPException(status_code=403, detail="Access denied.")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).order_by(DocumentChunk.chunk_index).all()
    return chunks


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    classification: str = Form("INTERNAL"),
    allowed_roles: str = Form("EMPLOYEE,HR,FINANCE,ADMIN"),
    current_user: User = Depends(require_role(["HR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    # Save uploaded file
    target_dir = os.path.join("data", "documents", "uploads")
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    roles_list = [r.strip().upper() for r in allowed_roles.split(",") if r.strip()]

    pipeline = IngestionPipeline(db=db)
    success, res = pipeline.ingest_single_file(
        file_path=file_path,
        override_classification=classification,
        override_roles=roles_list
    )

    if not success:
        raise HTTPException(status_code=400, detail=res.get("error", "Ingestion failed"))

    # Re-sync FAISS & BM25 indices across all chunks in DB
    all_db_chunks = db.query(DocumentChunk).all()
    chunk_dicts = [c.metadata_json for c in all_db_chunks if c.metadata_json]
    if chunk_dicts:
        pipeline.sparse_retriever.save_index(chunk_dicts)
        # Update dense embeddings
        from backend.embeddings.generator import EmbeddingGenerator
        import faiss
        contents = [c["content"] for c in chunk_dicts]
        embeddings = EmbeddingGenerator.generate_embeddings(contents, use_cache=True)
        faiss_index = faiss.IndexFlatIP(embeddings.shape[1])
        faiss_index.add(embeddings)
        pipeline.dense_retriever.save_index(faiss_index, chunk_dicts)

    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="DOCUMENT_UPLOAD",
        resource=res.get("document_id"),
        reason="Uploaded and indexed document"
    )

    doc = db.query(Document).filter(Document.document_id == res["document_id"]).first()
    return doc


@router.post("/{doc_id}/reindex", response_model=DocumentReindexResponse)
def reindex_document(
    doc_id: str,
    current_user: User = Depends(require_role(["HR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pipeline = IngestionPipeline(db=db)
    success, res = pipeline.ingest_single_file(doc.file_path)
    if not success:
        raise HTTPException(status_code=400, detail=res.get("error", "Reindex failed"))

    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="DOCUMENT_REINDEX",
        resource=doc_id,
        reason="Document reindexed manually"
    )

    return DocumentReindexResponse(
        success=True,
        document_id=doc_id,
        chunks_indexed=res.get("chunks_count", 0),
        message=f"Successfully reindexed {doc.title}"
    )


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()

    AuditLogger.log_event(
        db=db,
        user_email=current_user.email,
        role=current_user.role,
        action="DOCUMENT_DELETE",
        resource=doc_id,
        reason="Document deleted by admin"
    )

    return {"message": f"Document {doc_id} deleted successfully"}
