from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class EvaluationRunRequest(BaseModel):
    run_name: Optional[str] = None
    evaluator_type: str = "rag_and_acl"
    limit: Optional[int] = None


class EvaluationResultItem(BaseModel):
    id: int
    question_id: Optional[str] = None
    query: str
    user_role: str
    expected_decision: Optional[str] = None
    actual_decision: Optional[str] = None
    passed: bool
    retrieval_metrics: Optional[Dict[str, Any]] = None
    generation_metrics: Optional[Dict[str, Any]] = None
    acl_passed: bool
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationRunResponse(BaseModel):
    id: str
    run_name: str
    evaluator_type: str
    total_questions: int
    metrics_summary: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[List[EvaluationResultItem]] = []

    class Config:
        from_attributes = True


class EvaluationSummaryResponse(BaseModel):
    runs_count: int
    latest_run: Optional[EvaluationRunResponse] = None
    retrieval_metrics: Dict[str, float]
    generation_metrics: Dict[str, float]
    acl_metrics: Dict[str, float]
    security_metrics: Dict[str, float]
    operational_metrics: Dict[str, float]
