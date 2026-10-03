from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.database.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_logs(
        self,
        role: Optional[str] = None,
        action: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        q = self.db.query(AuditLog)
        if role:
            q = q.filter(AuditLog.role == role)
        if action:
            q = q.filter(AuditLog.action == action)
        if decision:
            q = q.filter(AuditLog.acl_decision == decision)

        total = q.count()
        records = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        return records, total
