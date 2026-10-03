from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.models import User, AuditLog
from backend.auth.dependencies import require_role

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])


@router.get("")
def get_audit_logs(
    role: Optional[str] = None,
    action: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(["HR", "ADMIN", "SECURITY"])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)

    if role:
        query = query.filter(AuditLog.role == role)
    if action:
        query = query.filter(AuditLog.action == action)
    if decision:
        query = query.filter(AuditLog.acl_decision == decision)

    total_count = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "logs": [
            {
                "id": l.id,
                "request_id": l.request_id,
                "trace_id": l.trace_id,
                "user_email": l.user_email,
                "role": l.role,
                "action": l.action,
                "resource": l.resource,
                "query": l.query,
                "acl_decision": l.acl_decision,
                "reason": l.reason,
                "latency_ms": l.latency_ms,
                "status_code": l.status_code,
                "metadata": l.metadata_json,
                "created_at": l.created_at.isoformat()
            } for l in logs
        ]
    }
