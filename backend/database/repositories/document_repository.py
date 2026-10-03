from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database.models import Document, DocumentChunk, DocumentVersion


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_document_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.document_id == document_id).first()

    def list_all(self, classification: Optional[str] = None, domain: Optional[str] = None) -> List[Document]:
        q = self.db.query(Document)
        if classification:
            q = q.filter(Document.classification == classification)
        if domain:
            q = q.filter(Document.domain == domain)
        return q.all()

    def get_chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

    def delete(self, document_id: str) -> bool:
        doc = self.get_by_document_id(document_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False
