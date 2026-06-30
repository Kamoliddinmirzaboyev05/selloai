import pytest
from httpx import AsyncClient

from app.ai.groq import GroqClient
from app.core.errors import AppError
from app.telegram.parser import parse_telegram_update
from tests.conftest import register_and_create_org


def test_telegram_parser_extracts_inbound_message():
    inbound = parse_telegram_update(
        {
            "message": {
                "message_id": 42,
                "text": "What is the price?",
                "chat": {"id": 1001},
                "from": {"id": 1001, "first_name": "Ada", "username": "ada"},
            }
        }
    )

    assert inbound is not None
    assert inbound.external_message_id == "telegram:1001:42"
    assert inbound.customer_external_id == "1001"
    assert inbound.name == "Ada"


async def test_groq_client_requires_api_key():
    client = GroqClient(api_key="", model="test-model")

    with pytest.raises(AppError) as exc:
        await client.chat_completion([{"role": "user", "content": "Hello"}])

    assert exc.value.code == "SERVICE_NOT_CONFIGURED"


async def test_connect_telegram_registers_production_webhook(client: AsyncClient, monkeypatch):
    from app.telegram import router as telegram_router

    calls: dict[str, object] = {}

    class FakeTelegramClient:
        def __init__(self, bot_token: str) -> None:
            calls["bot_token"] = bot_token

        async def get_me(self):
            return {"id": 12345, "username": "demo_bot"}

        async def set_webhook(self, url: str):
            calls["webhook_url"] = url
            return {"ok": True}

    monkeypatch.setattr(telegram_router, "TelegramClient", FakeTelegramClient)
    monkeypatch.setattr(telegram_router.app_settings, "telegram_webhook_base_url", "https://selloapi.webportfolio.uz")
    token, organization_id = await register_and_create_org(client)

    response = await client.post(
        "/api/v1/channels/telegram/connect",
        headers={"Authorization": f"Bearer {token}"},
        json={"organization_id": organization_id, "bot_token": "123456789:AA-test-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["webhook_path"].startswith("/api/v1/webhooks/telegram/")
    assert calls["webhook_url"] == f"https://selloapi.webportfolio.uz{body['webhook_path']}"
