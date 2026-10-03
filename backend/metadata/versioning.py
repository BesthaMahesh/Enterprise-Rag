from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models import Document, DocumentVersion, DocumentStatus


class VersionManager:
    """Handles document version increments and status transitions (active vs superseded)."""

    @staticmethod
    def register_new_version(
        db: Session,
        document_id: str,
        new_version: str,
        file_path: str,
        effective_date: Optional[str] = None,
        checksum: Optional[str] = None
    ) -> DocumentVersion:
        # Check existing versions and mark them superseded
        existing_versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).all()
        for ev in existing_versions:
            ev.status = DocumentStatus.SUPERSEDED.value

        # Create new version record
        doc_ver = DocumentVersion(
            document_id=document_id,
            version=new_version,
            effective_date=effective_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            file_path=file_path,
            status=DocumentStatus.ACTIVE.value,
            checksum=checksum,
            created_at=datetime.now(timezone.utc)
        )
        db.add(doc_ver)

        # Update parent document version
        parent_doc = db.query(Document).filter(Document.document_id == document_id).first()
        if parent_doc:
            parent_doc.version = new_version
            parent_doc.effective_date = doc_ver.effective_date
            parent_doc.file_path = file_path
            parent_doc.status = DocumentStatus.ACTIVE.value
            parent_doc.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(doc_ver)
        return doc_ver
