import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("app.oauth.audit")
_SENSITIVE_KEYS = {"access_token", "token", "page_access_token", "user_access_token", "client_secret"}


def log_oauth_event(event: str, *, provider: str, organization_id: str | None = None, **details: Any) -> None:
    payload = {
        "event": event,
        "provider": provider,
        "organization_id": organization_id,
        "occurred_at": datetime.now(UTC).isoformat(),
        **_redact(details),
    }
    logger.info(json.dumps(payload, sort_keys=True))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key in _SENSITIVE_KEYS else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
