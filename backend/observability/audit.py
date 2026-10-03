import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database.models import AuditLog
from backend.observability.tracing import get_current_request_id, get_current_trace_id

logger = logging.getLogger(__name__)


class AuditLogger:
    """Records audit logs for compliance, security access attempts, and RAG interactions."""

    @staticmethod
    def log_event(
        db: Session,
        user_email: str,
        role: str,
        action: str,
        resource: Optional[str] = None,
        query: Optional[str] = None,
        acl_decision: str = "ALLOWED",
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        status_code: int = 200,
        latency_ms: float = 0.0,
        metadata_json: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> AuditLog:
        req_id = request_id or get_current_request_id()
        trc_id = trace_id or get_current_trace_id()

        audit_entry = AuditLog(
            request_id=req_id,
            trace_id=trc_id,
            user_email=user_email,
            role=role,
            action=action,
            resource=resource,
            query=query,
            acl_decision=acl_decision,
            reason=reason,
            ip_address=ip_address,
            status_code=status_code,
            latency_ms=latency_ms,
            metadata_json=metadata_json,
            created_at=datetime.now(timezone.utc)
        )

        try:
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to write audit log: {e}")

        return audit_entry
