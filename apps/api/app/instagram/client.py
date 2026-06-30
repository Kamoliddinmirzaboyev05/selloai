from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import AppError


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
        if response.status_code >= 400:
            raise AppError("Meta Graph API request failed.", "META_GRAPH_API_ERROR", 502)
        return response.json()

