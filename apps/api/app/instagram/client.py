import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.instagram.graph_errors import build_meta_graph_app_error, to_safe_log_json

logger = logging.getLogger(__name__)


class MetaGraphClient:
    def __init__(self, access_token: str, api_version: str | None = None) -> None:
        self.access_token = access_token
        self.api_version = api_version or settings.meta_graph_api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def send_instagram_message(self, recipient_id: str, text: str) -> dict[str, Any]:
        return await self._post(
            "/me/messages",
            {
                "recipient": {"id": recipient_id},
                "message": {"text": text},
                "messaging_type": "RESPONSE",
            },
        )

    async def reply_to_comment(self, comment_id: str, text: str) -> dict[str, Any]:
        return await self._post(f"/{comment_id}/replies", {"message": text})

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                params={"access_token": self.access_token},
                json=payload,
            )
        try:
            data = response.json()
        except ValueError as exc:
            logger.warning(
                "Meta Graph API returned non-JSON response path=%s status_code=%s body=%s",
                path,
                response.status_code,
                response.text,
            )
            raise AppError(
                "Meta Graph API returned an invalid response.", "META_GRAPH_API_INVALID_RESPONSE", 502
            ) from exc
        if not isinstance(data, dict):
            logger.warning(
                "Meta Graph API returned invalid JSON shape path=%s status_code=%s body=%s",
                path,
                response.status_code,
                to_safe_log_json(data),
            )
            raise AppError("Meta Graph API returned an invalid response.", "META_GRAPH_API_INVALID_RESPONSE", 502)
        log_message = (
            "Meta Graph API request failed path=%s status_code=%s body=%s"
            if response.status_code >= 400
            else "Meta Graph API response path=%s status_code=%s body=%s"
        )
        log_method = logger.warning if response.status_code >= 400 else logger.info
        log_method(log_message, path, response.status_code, to_safe_log_json(data))
        if response.status_code >= 400:
            raise build_meta_graph_app_error(data)
        return data
