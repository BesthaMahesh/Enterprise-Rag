import json
import logging
import sys
from datetime import datetime, timezone
from backend.observability.tracing import get_current_request_id, get_current_trace_id


class StructuredJsonFormatter(logging.Formatter):
    """Formats logs into clean structured JSON omitting any sensitive credentials."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", None) or get_current_request_id(),
            "trace_id": getattr(record, "trace_id", None) or get_current_trace_id(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_structured_logging(log_level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
