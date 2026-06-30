import json
from typing import Any

from app.core.errors import AppError

TOKEN_FIELD_NAMES = {"access_token", "page_access_token", "user_access_token", "fb_exchange_token", "input_token"}


def build_meta_graph_app_error(data: dict[str, Any]) -> AppError:
    meta_error = extract_meta_error(data)
    detail = meta_error.get("message") or "Meta Graph API request failed."
    return AppError(detail, "META_GRAPH_API_ERROR", 502, extra={"meta_error": meta_error})


def extract_meta_error(data: dict[str, Any]) -> dict[str, Any]:
    raw_error = data.get("error")
    if not isinstance(raw_error, dict):
        return {"message": "Meta Graph API request failed.", "type": None, "code": None, "fbtrace_id": None}
    return {
        "code": raw_error.get("code"),
        "type": raw_error.get("type"),
        "message": raw_error.get("message") or "Meta Graph API request failed.",
        "fbtrace_id": raw_error.get("fbtrace_id"),
    }


def to_safe_log_json(value: Any) -> str:
    return json.dumps(sanitize_meta_payload(value), sort_keys=True, ensure_ascii=False)


def sanitize_meta_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key in TOKEN_FIELD_NAMES else sanitize_meta_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_meta_payload(item) for item in value]
    return value
