import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    APP_ENV: str = "development"
    APP_NAME: str = "Enterprise Knowledge Intelligence Platform"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./enterprise_rag.db"

    # JWT
    JWT_SECRET: str = "super-secret-enterprise-rag-jwt-token-key-2026-acme-corp"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Seed User Passwords
    DEFAULT_EMPLOYEE_PASSWORD: str = "Employee@Acme2026!"
    DEFAULT_HR_PASSWORD: str = "HRAdmin@Acme2026!"
    DEFAULT_FINANCE_PASSWORD: str = "Finance@Acme2026!"
    DEFAULT_ADMIN_PASSWORD: str = "AdminMaster@Acme2026!"
    DEFAULT_SECURITY_PASSWORD: str = "SecuritySec@Acme2026!"

    # LLM
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024
    LLM_TIMEOUT: int = 30

    # Embedding & Reranker
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ENABLE_CROSS_ENCODER: bool = True
    LOW_MEMORY_MODE: bool = False
    EMBEDDING_DEVICE: str = "cpu"
    RERANKER_DEVICE: str = "cpu"

    # Vector & Sparse Index Paths
    VECTOR_INDEX_PATH: str = "./indexes/dense/faiss_index.bin"
    VECTOR_METADATA_PATH: str = "./indexes/dense/chunks_metadata.json"
    BM25_INDEX_PATH: str = "./indexes/sparse/bm25_index.pkl"

    # Retrieval
    TOP_K_DENSE: int = 20
    TOP_K_SPARSE: int = 20
    TOP_K_RERANK: int = 20
    FINAL_CONTEXT_K: int = 10
    MAX_CONTEXT_TOKENS: int = 3000
    RRF_K: int = 60
    RERANKER_RELEVANCE_THRESHOLD: float = -5.0

    # Guardrails
    ENABLE_PROMPT_INJECTION_DETECTION: bool = True
    ENABLE_PII_DETECTION: bool = True
    PII_MASK_EMAILS: bool = True
    ENABLE_GROUNDING_CHECK: bool = True
    ENABLE_OUTPUT_GUARDRAILS: bool = True

    # Reliability
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIME: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    CORS_ORIGIN_REGEX: str = r"^https:\/\/.*\.vercel\.app$"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v


settings = Settings()
