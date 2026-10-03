"""Rebuild the BM25 index without loading the embedding model.

Render uses this index in LOW_MEMORY_MODE, so keeping it in sync with the
versioned documents must not require downloading a Hugging Face model.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ingestion.pipeline import IngestionPipeline


def main() -> None:
    pipeline = IngestionPipeline(db=None)
    document_paths = sorted(
        path
        for path in glob.glob("data/documents/**/*.*", recursive=True)
        if path.endswith((".md", ".txt", ".pdf", ".docx"))
    )

    chunks = []
    failures = []
    for path in document_paths:
        success, result = pipeline.ingest_single_file(path)
        if success:
            chunks.extend(result["chunks"])
        else:
            failures.append(f"{path}: {result.get('error', 'unknown error')}")

    if failures:
        raise RuntimeError("Could not build sparse index:\n" + "\n".join(failures))
    if not chunks:
        raise RuntimeError("No documents were available to build the sparse index.")

    pipeline.sparse_retriever.save_index(chunks)
    print(f"Built BM25 index for {len(document_paths)} documents and {len(chunks)} chunks.")


if __name__ == "__main__":
    main()
