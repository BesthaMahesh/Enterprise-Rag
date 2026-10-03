import json
from typing import Dict, Any, Tuple


class APILoader:
    """Loads unstructured and structured enterprise knowledge from external APIs / SaaS apps."""

    @staticmethod
    def load_api_payload(app_name: str, endpoint: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        formatted_json = json.dumps(payload, indent=2, ensure_ascii=False)
        content = f"# Source Application: {app_name}\nEndpoint: {endpoint}\n\n```json\n{formatted_json}\n```"
        metadata = {
            "source_type": "api",
            "app_name": app_name,
            "endpoint": endpoint
        }
        return content, metadata
