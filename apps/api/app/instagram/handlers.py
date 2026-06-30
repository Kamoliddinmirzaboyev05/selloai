import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_instagram_dm_event(event: dict[str, Any]) -> dict[str, str]:
    logger.info("Accepted Instagram DM event skeleton", extra={"event_keys": list(event.keys())})
    return {"status": "accepted", "type": "instagram_dm"}


async def handle_instagram_comment_event(event: dict[str, Any]) -> dict[str, str]:
    logger.info("Accepted Instagram comment event skeleton", extra={"event_keys": list(event.keys())})
    return {"status": "accepted", "type": "instagram_comment"}


async def dispatch_instagram_webhook(payload: dict[str, Any]) -> dict[str, int]:
    dm_events = 0
    comment_events = 0

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            await handle_instagram_dm_event(messaging_event)
            dm_events += 1

        for change in entry.get("changes", []):
            field = change.get("field")
            if field in {"comments", "mentions", "feed"}:
                await handle_instagram_comment_event(change)
                comment_events += 1

    return {"dm_events": dm_events, "comment_events": comment_events}

