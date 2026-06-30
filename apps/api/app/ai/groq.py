import logging

import httpx

from app.core.config import settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        self.model = model or settings.groq_model

    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise AppError("Groq API key is not configured.", "SERVICE_NOT_CONFIGURED", 503)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
            )

        if response.status_code >= 400:
            logger.warning("Groq request failed", extra={"status_code": response.status_code})
            raise AppError("AI provider request failed.", "AI_PROVIDER_ERROR", 502)

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AppError("AI provider returned an invalid response.", "AI_PROVIDER_ERROR", 502) from exc

