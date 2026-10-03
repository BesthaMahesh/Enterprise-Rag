import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config.settings import settings
from backend.database.session import init_db
from backend.observability.logger import setup_structured_logging
from backend.observability.tracing import request_id_var, trace_id_var

# Import Routers
from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.search import router as search_router
from backend.api.users import router as users_router
from backend.api.evaluation import router as evaluation_router
from backend.api.analytics import router as analytics_router
from backend.api.audit import router as audit_router
from backend.api.health import router as health_router

setup_structured_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    init_db()
    try:
        from scripts.seed_database import seed_demo_users
        seed_demo_users()
    except Exception:
        pass

    # Pre-warm embedding model in background thread so server starts in milliseconds
    # and user queries run instantly without 30s cold-start model load delay
    import threading
    def _warmup():
        try:
            from backend.embeddings.model import get_embedding_model
            get_embedding_model()
        except Exception:
            pass

    threading.Thread(target=_warmup, daemon=True, name="model-warmup").start()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise Knowledge Intelligence Platform with strict Role-Based Access Control, Hybrid Retrieval, Reranking, and Grounded Generation.",
    lifespan=lifespan
)

# CORS Middleware with Vercel & custom domain support
cors_kwargs = {
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if "*" in settings.CORS_ORIGINS:
    cors_kwargs["allow_origins"] = ["*"]
    cors_kwargs["allow_credentials"] = False
else:
    cors_kwargs["allow_origins"] = list(settings.CORS_ORIGINS)
    cors_kwargs["allow_credentials"] = True
    if getattr(settings, "CORS_ORIGIN_REGEX", None):
        cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

app.add_middleware(CORSMiddleware, **cors_kwargs)


@app.middleware("http")
async def context_and_tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
    trc_id = request.headers.get("X-Trace-ID", f"trc-{uuid.uuid4().hex[:16]}")
    request_id_var.set(req_id)
    trace_id_var.set(trc_id)

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Trace-ID"] = trc_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Include Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(users_router)
app.include_router(evaluation_router)
app.include_router(analytics_router)
app.include_router(audit_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }
