import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import SessionLocal, init_db
from backend.ingestion.pipeline import IngestionPipeline


def run_ingestion():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()

    print("Starting full document ingestion from data/documents/...")
    pipeline = IngestionPipeline(db=db)
    result = pipeline.ingest_directory("data/documents")

    print(f"\nIngestion Summary:")
    print(f"Total files discovered: {result['total_files']}")
    print(f"Successfully ingested : {result['ingested_count']}")
    print(f"Failed ingestions     : {result['failed_count']}")
    print(f"Total chunks created  : {result['total_chunks']}")

    if result["failed_docs"]:
        print("\nFailed files:")
        for fd in result["failed_docs"]:
            print(f"  - {fd['file']}: {fd['reason']}")

    db.close()
    print("\nIngestion & Indexing completed successfully.")


if __name__ == "__main__":
    run_ingestion()
