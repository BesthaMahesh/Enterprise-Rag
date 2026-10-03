import os
import glob
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import faiss
import numpy as np

from backend.ingestion.loaders.file_loader import FileLoader
from backend.ingestion.parsers.document_parser import DocumentParser
from backend.ingestion.cleaners.text_cleaner import TextCleaner
from backend.ingestion.validators.document_validator import DocumentValidator
from backend.metadata.extractor import MetadataExtractor
from backend.metadata.schema import DocumentMetadata
from backend.chunking.structural_chunker import StructuralChunker
from backend.chunking.chunk_validator import ChunkValidator
from backend.embeddings.generator import EmbeddingGenerator
from backend.retrieval.dense import DenseRetriever
from backend.retrieval.sparse import SparseRetriever
from backend.database.models import Document, DocumentChunk, DocumentVersion, DocumentStatus
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    End-to-end Enterprise RAG Document Ingestion Pipeline.
    """

    def __init__(self, db: Session = None):
        self.db = db
        self.dense_retriever = DenseRetriever()
        self.sparse_retriever = SparseRetriever()
        self.chunker = StructuralChunker(target_chunk_size=350, chunk_overlap=50)

    def ingest_single_file(
        self,
        file_path: str,
        override_classification: str = None,
        override_roles: List[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Ingest, validate, chunk, and embed a single file."""
        try:
            # 1. Load raw file
            raw_text, file_meta = FileLoader.load(file_path)

            # 2. Clean & Normalize Unicode
            cleaned_text = TextCleaner.clean_text(raw_text)

            # 3. Extract Metadata
            doc_meta: DocumentMetadata = MetadataExtractor.extract_from_file(file_path)
            if override_classification:
                doc_meta.classification = override_classification
            if override_roles:
                doc_meta.allowed_roles = override_roles

            # 4. Validate document
            valid_doc, doc_errors = DocumentValidator.validate_document(cleaned_text, doc_meta)
            if not valid_doc:
                return False, {"error": f"Document validation failed: {', '.join(doc_errors)}"}

            # 5. Parse into sections
            sections = DocumentParser.parse_markdown(cleaned_text)

            # 6. Chunk with structural & ACL preservation
            chunks = self.chunker.chunk_sections(doc_meta, sections)

            # 7. Validate chunks
            valid_chunks, chunk_errors = ChunkValidator.validate_all_chunks(chunks)
            if not valid_chunks:
                return False, {"error": f"Chunk validation failed: {', '.join(chunk_errors)}"}

            # 8. Persist to Database if DB session is provided
            if self.db:
                # Upsert Document
                existing_doc = self.db.query(Document).filter(Document.document_id == doc_meta.document_id).first()
                if existing_doc:
                    existing_doc.title = doc_meta.document
                    existing_doc.classification = doc_meta.classification
                    existing_doc.allowed_roles = doc_meta.allowed_roles
                    existing_doc.version = doc_meta.version
                    existing_doc.effective_date = doc_meta.effective_date
                    existing_doc.chunk_count = len(chunks)
                    existing_doc.status = DocumentStatus.ACTIVE.value
                    
                    # Remove old chunks for this doc
                    self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_meta.document_id).delete()
                else:
                    new_doc = Document(
                        document_id=doc_meta.document_id,
                        title=doc_meta.document,
                        file_name=file_meta["file_name"],
                        file_path=file_path,
                        file_type=file_meta.get("extension", "md").replace(".", ""),
                        domain=doc_meta.domain,
                        classification=doc_meta.classification,
                        allowed_roles=doc_meta.allowed_roles,
                        version=doc_meta.version,
                        effective_date=doc_meta.effective_date,
                        status=DocumentStatus.ACTIVE.value,
                        chunk_count=len(chunks),
                        language=doc_meta.language,
                        checksum=doc_meta.checksum
                    )
                    self.db.add(new_doc)

                # Add chunks
                for chk in chunks:
                    chunk_record = DocumentChunk(
                        chunk_id=chk["chunk_id"],
                        document_id=chk["document_id"],
                        chunk_index=chk["chunk_index"],
                        content=chk["content"],
                        section=chk["section"],
                        page_number=chk["page_number"],
                        token_count=chk["token_count"],
                        allowed_roles=chk["allowed_roles"],
                        classification=chk["classification"],
                        metadata_json=chk
                    )
                    self.db.add(chunk_record)

                # Add version record
                ver_record = DocumentVersion(
                    document_id=doc_meta.document_id,
                    version=doc_meta.version,
                    effective_date=doc_meta.effective_date,
                    file_path=file_path,
                    status=DocumentStatus.ACTIVE.value,
                    checksum=doc_meta.checksum
                )
                self.db.add(ver_record)
                self.db.commit()

            return True, {
                "document_id": doc_meta.document_id,
                "title": doc_meta.document,
                "chunks_count": len(chunks),
                "classification": doc_meta.classification,
                "allowed_roles": doc_meta.allowed_roles,
                "chunks": chunks
            }

        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            if self.db:
                self.db.rollback()
            return False, {"error": str(e)}

    def ingest_directory(self, base_dir: str = "data/documents") -> Dict[str, Any]:
        """Ingests all documents in directory tree and builds vector + BM25 indices."""
        files = glob.glob(os.path.join(base_dir, "**", "*.*"), recursive=True)
        valid_files = [f for f in files if f.endswith((".md", ".txt", ".pdf", ".docx"))]
        
        all_chunks = []
        ingested_docs = []
        failed_docs = []

        for fpath in valid_files:
            success, res = self.ingest_single_file(fpath)
            if success:
                ingested_docs.append(res)
                all_chunks.extend(res["chunks"])
            else:
                failed_docs.append({"file": fpath, "reason": res.get("error")})

        if all_chunks:
            logger.info(f"Building dense and sparse indices for {len(all_chunks)} total chunks...")
            # 1. Embeddings & Dense FAISS Index
            contents = [c["content"] for c in all_chunks]
            embeddings = EmbeddingGenerator.generate_embeddings(contents, use_cache=True)
            dim = embeddings.shape[1]

            # Inner Product (equivalent to cosine similarity with normalized vectors)
            faiss_index = faiss.IndexFlatIP(dim)
            faiss_index.add(embeddings)
            self.dense_retriever.save_index(faiss_index, all_chunks)

            # 2. Sparse BM25 Index
            self.sparse_retriever.save_index(all_chunks)

        return {
            "total_files": len(valid_files),
            "ingested_count": len(ingested_docs),
            "failed_count": len(failed_docs),
            "total_chunks": len(all_chunks),
            "ingested_docs": ingested_docs,
            "failed_docs": failed_docs
        }
