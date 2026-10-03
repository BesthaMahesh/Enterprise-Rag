from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database.models import EvaluationRun, EvaluationResult


class EvaluationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_run(self) -> Optional[EvaluationRun]:
        return self.db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).first()

    def list_runs(self, limit: int = 20) -> List[EvaluationRun]:
        return self.db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit).all()

    def count_runs(self) -> int:
        return self.db.query(EvaluationRun).count()
