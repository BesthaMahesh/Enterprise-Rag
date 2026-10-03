from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from backend.database.models import User
from backend.auth.dependencies import get_current_user
from backend.retrieval.retriever import enterprise_retriever

router = APIRouter(prefix="/api/search", tags=["Direct Search"])


@router.get("")
def search_knowledge(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    results = enterprise_retriever.retrieve_authorized_context(
        query=q,
        user_role=current_user.role
    )
    return {
        "query": q,
        "role": current_user.role,
        "results": results.get("final_candidates", [])[:top_k]
    }
