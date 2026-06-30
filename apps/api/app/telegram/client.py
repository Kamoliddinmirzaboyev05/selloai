import logging
from typing import Any

import httpx

from app.core.errors import AppError

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def get_me(self) -> dict[str, Any]:
        data = await self._request("getMe", {})
        return data["result"]

    async def get_webhook_info(self) -> dict[str, Any]:
        data = await self._request("getWebhookInfo", {})
        return data["result"]

    async def set_webhook(self, url: str) -> dict[str, Any]:
        data = await self._request(
            "setWebhook",
            {
                "url": url,
                "allowed_updates": ["message"],
                "drop_pending_updates": False,
            },
        )
        return data["result"]

    async def send_message(self, chat_id: str, text: str) -> dict[str, Any]:
        data = await self._request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )
        return data["result"]

    async def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.base_url}/{method}", json=payload)

        if response.status_code >= 400:
            logger.warning(
                "Telegram request failed method=%s status_code=%s body=%s",
                method,
                response.status_code,
                response.text,
            )
            raise AppError("Telegram API request failed.", "TELEGRAM_API_ERROR", 502)

        data = response.json()
        if not data.get("ok"):
            logger.warning("Telegram API returned error method=%s body=%s", method, data)
            raise AppError("Telegram API returned an error.", "TELEGRAM_API_ERROR", 502)
        return data
