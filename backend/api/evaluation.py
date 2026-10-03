from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import User, EvaluationRun, EvaluationResult
from backend.auth.dependencies import require_role
from backend.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSummaryResponse
)
from backend.evaluation.rag_evaluator import RAGEvaluator

router = APIRouter(prefix="/api/evaluation", tags=["RAG Evaluation"])


@router.get("", response_model=EvaluationSummaryResponse)
def get_evaluation_summary(
    current_user: User = Depends(require_role(["HR", "ADMIN", "SECURITY"])),
    db: Session = Depends(get_db)
):
    runs_count = db.query(EvaluationRun).count()
    latest_run = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).first()

    # Default baseline if no runs
    default_retrieval = {"recall_at_5": 0.0, "precision_at_5": 0.0, "mrr": 0.0, "ndcg": 0.0}
    default_generation = {"faithfulness": 0.0, "answer_relevance": 0.0, "groundedness": 0.0}
    default_acl = {"acl_precision": 0.0, "unauthorized_retrieval_rate": 0.0, "unauthorized_answer_rate": 0.0, "acl_recall": 0.0}
    default_security = {"prompt_injection_block_rate": 0.0, "pii_leakage_rate": 0.0}
    default_operational = {"average_latency_ms": 0.0, "total_time_ms": 0.0, "error_rate": 0.0}

    if latest_run and latest_run.metrics_summary:
        summary = latest_run.metrics_summary
        return EvaluationSummaryResponse(
            runs_count=runs_count,
            latest_run=latest_run,
            retrieval_metrics=summary.get("retrieval", default_retrieval),
            generation_metrics=summary.get("generation", default_generation),
            acl_metrics=summary.get("acl", default_acl),
            security_metrics=summary.get("security", default_security),
            operational_metrics=summary.get("operational", default_operational)
        )

    return EvaluationSummaryResponse(
        runs_count=runs_count,
        latest_run=None,
        retrieval_metrics=default_retrieval,
        generation_metrics=default_generation,
        acl_metrics=default_acl,
        security_metrics=default_security,
        operational_metrics=default_operational
    )


@router.post("/run", response_model=EvaluationRunResponse)
def trigger_evaluation_run(
    req: EvaluationRunRequest = EvaluationRunRequest(),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    evaluator = RAGEvaluator(db=db)
    result = evaluator.run_full_evaluation(run_name=req.run_name)
    run_record = db.query(EvaluationRun).filter(EvaluationRun.id == result["run_id"]).first()
    return run_record


@router.get("/runs", response_model=List[EvaluationRunResponse])
def get_all_evaluation_runs(
    current_user: User = Depends(require_role(["HR", "ADMIN", "SECURITY"])),
    db: Session = Depends(get_db)
):
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(20).all()
    return runs


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation_run_details(
    run_id: str,
    current_user: User = Depends(require_role(["HR", "ADMIN", "SECURITY"])),
    db: Session = Depends(get_db)
):
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run
