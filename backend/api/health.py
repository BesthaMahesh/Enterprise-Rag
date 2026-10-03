import os
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.session import get_db
from backend.config.settings import settings

router = APIRouter(tags=["Health & Status"])


@router.get("/health")
@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Basic health check indicating process is alive and responding."""
    return {
        "status": "online",
        "service": "enterprise-rag-platform",
        "environment": settings.APP_ENV
    }


@router.get("/health/live")
@router.get("/api/health/live")
def liveness_probe():
    """Kubernetes / Docker liveness probe: returns 200 if container process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
@router.get("/api/health/ready")
def readiness_probe(response: Response, db: Session = Depends(get_db)):
    """
    Readiness probe verifying all core dependencies:
    - Database connectivity
    - FAISS Vector index file
    - BM25 Sparse index file
    - Core configuration
    Returns 200 when ready to receive traffic, 503 when degraded.
    """
    checks = {}
    is_ready = True

    # 1. Database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = "unavailable"
        is_ready = False

    # 2. Vector Index
    if os.path.exists(settings.VECTOR_INDEX_PATH) and os.path.exists(settings.VECTOR_METADATA_PATH):
        checks["vector_index"] = "ready"
    else:
        checks["vector_index"] = "missing"
        is_ready = False

    # 3. BM25 Index
    if os.path.exists(settings.BM25_INDEX_PATH):
        checks["bm25_index"] = "ready"
    else:
        checks["bm25_index"] = "missing"
        is_ready = False

    # 4. LLM Config
    checks["llm_provider"] = settings.LLM_PROVIDER
    checks["embedding_model"] = settings.EMBEDDING_MODEL

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks
    }

