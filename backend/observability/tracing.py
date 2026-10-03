import uuid
import contextvars
from typing import Optional

request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)


def get_current_request_id() -> str:
    rid = request_id_var.get()
    if not rid:
        rid = f"req-{uuid.uuid4().hex[:12]}"
        request_id_var.set(rid)
    return rid


def get_current_trace_id() -> str:
    tid = trace_id_var.get()
    if not tid:
        tid = f"trc-{uuid.uuid4().hex[:16]}"
        trace_id_var.set(tid)
    return tid
